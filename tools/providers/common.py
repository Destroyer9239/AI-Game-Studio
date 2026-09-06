"""Provider-neutral contracts, bounded transport and one-use paid approval receipts."""
import base64
from datetime import datetime, timedelta, timezone
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import subprocess
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

ROOT = Path(__file__).resolve().parents[2]
OPERATIONS = {'generate_3d', 'generate_image', 'edit_image', 'generate_texture', 'generate_video', 'remesh', 'retexture', 'rig', 'animate'}

def now():
    return datetime.now(timezone.utc).isoformat()

def asset_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', value):
        raise ValueError('Asset name must be a lowercase identifier')
    return value

def path(value):
    resolved = (ROOT / value).resolve()
    if not resolved.is_relative_to(ROOT):
        raise ValueError('Path must stay inside the project')
    return resolved

def read_json(file):
    return json.loads(Path(file).read_text(encoding='utf-8-sig'))

def write_json(file, value):
    file = Path(file)
    file.parent.mkdir(parents=True, exist_ok=True)
    temporary = file.with_suffix(file.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(file)

def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()

def file_hash(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()

def reject_secrets(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == 'api_key_present' and type(item) is bool:
                continue
            if re.search(r'(^|_)(api_key|secret|password|authorization|access_token|hf_key)($|_)', key, re.I):
                raise ValueError('Credentials belong in environment variables, never request/config files')
            reject_secrets(item)
    elif isinstance(value, list):
        for item in value:
            reject_secrets(item)
    elif isinstance(value, str):
        for variable in ('MESHY_API_KEY', 'HF_KEY', 'HF_API_KEY', 'HF_API_SECRET'):
            secret = os.environ.get(variable)
            if secret and secret in value:
                raise ValueError('Request contains a configured secret')

def public_https(url, resolve=False):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Provider media requires a public HTTPS URL')
    if parsed.hostname.lower() == 'localhost':
        raise ValueError('Private media URL rejected')
    try:
        if not ipaddress.ip_address(parsed.hostname).is_global:
            raise ValueError('Private media URL rejected')
    except ValueError as exc:
        if str(exc) == 'Private media URL rejected':
            raise
    if resolve:
        addresses = socket.getaddrinfo(parsed.hostname, 443)
        if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError('Private media destination rejected')
    return url

def reference(value, image=True):
    if value.startswith('https://'):
        return public_https(value)
    file = path(value)
    allowed = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'} if image else {'.glb': 'application/octet-stream'}
    if file.suffix.lower() not in allowed or file.stat().st_size > 20 * 1024 * 1024:
        raise ValueError('Unsupported input format or file exceeds 20 MiB')
    return 'data:' + allowed[file.suffix.lower()] + ';base64,' + base64.b64encode(file.read_bytes()).decode()

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Authenticated API redirects are not followed')

def api_json(origin, route, headers, body=None):
    if origin not in ('https://api.meshy.ai',):
        raise ValueError('Unreviewed provider API origin')
    if not route.startswith('/openapi/') or '..' in route or '://' in route:
        raise ValueError('Invalid API route')
    payload = None if body is None else json.dumps(body).encode()
    request = Request(origin + route, data=payload, headers={**headers, 'Content-Type': 'application/json'})
    try:
        # No POST retries: a timeout may mean the provider already billed the job.
        with build_opener(ProxyHandler({}), NoRedirect()).open(request, timeout=30) as response:
            return json.loads(response.read(8 * 1024 * 1024))
    except HTTPError as exc:
        raise RuntimeError(f'Provider HTTP {exc.code}; response body withheld to prevent credential leakage') from None
    except (URLError, TimeoutError):
        raise RuntimeError('Provider network failure; submission outcome may be unknown. Do not resubmit automatically.') from None

class MediaRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_https(newurl, resolve=True)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def download(url, destination, limit=512 * 1024 * 1024):
    public_https(url, resolve=True)
    destination = path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    # No API credentials are sent to media storage hosts.
    with build_opener(ProxyHandler({}), MediaRedirect()).open(url, timeout=60) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Media download exceeds size limit')
    if destination.suffix == '.glb' and (data[:4] != b'glTF' or len(data) < 20):
        raise ValueError('Expected GLB output; refusing HTML/archive/other data')
    destination.write_bytes(data)
    return destination

def sanitized(value):
    if isinstance(value, dict):
        return {k: sanitized(v) for k, v in value.items() if k == 'api_key_present' and type(v) is bool or not re.search(r'secret|token|authorization|api_key', k, re.I)}
    if isinstance(value, list):
        return [sanitized(v) for v in value]
    if isinstance(value, str):
        if value.startswith('data:'):
            return '<embedded input; sha256=' + hashlib.sha256(value.encode()).hexdigest() + '>'
        if value.startswith('https://'):
            parts = urlparse(value)
            return urlunparse(parts._replace(query='', fragment=''))
        for variable in ('MESHY_API_KEY', 'HF_KEY', 'HF_API_KEY', 'HF_API_SECRET'):
            if os.environ.get(variable):
                value = value.replace(os.environ[variable], '<redacted>')
    return value

def run(command, timeout=180):
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}): {Path(command[0]).name}; inspect local stage logs. Output: {sanitized(result.stdout[-2000:] + result.stderr[-2000:])}')
    return result.stdout

def create_approval(plan, receipt, user_reference, max_cost, unit):
    if not plan['paid'] or not user_reference.strip() or max_cost < 0:
        raise ValueError('Paid approval requires a user-message reference and nonnegative ceiling')
    cost = plan['cost']
    if cost.get('amount') is not None and (unit != cost['unit'] or max_cost < cost['amount']):
        raise ValueError('Approval ceiling is below the displayed estimate or uses a different unit')
    receipt = path(receipt)
    if not receipt.is_relative_to(path('generated/approvals')):
        raise ValueError('Approval receipts must live in ignored generated/approvals')
    if receipt.exists():
        raise ValueError('Approval receipt already exists')
    write_json(receipt, {'plan_sha256': digest(plan), 'user_reference': user_reference, 'max_cost': max_cost, 'unit': unit,
                         'expires': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()})

def consume_approval(plan, receipt, job_dir):
    approval = read_json(path(receipt))
    if approval['plan_sha256'] != digest(plan) or not approval.get('user_reference'):
        raise ValueError('Approval does not match this exact plan')
    if datetime.fromisoformat(approval['expires']) <= datetime.now(timezone.utc):
        raise ValueError('Approval expired')
    cost = plan['cost']
    if cost.get('amount') is not None and (approval['unit'] != cost['unit'] or approval['max_cost'] < cost['amount']):
        raise ValueError('Approval ceiling does not cover this operation')
    # Exclusive creation is an atomic cross-process one-submission latch.
    with (Path(job_dir) / 'submission.lock').open('x', encoding='utf-8') as file:
        file.write(now())
    return approval
