"""Local ComfyUI adapter using only Python's standard library. Defaults to dry-run.

Explicit --execute requires an already-installed local ComfyUI and checkpoint.
No package/model installation or service startup is performed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler
import uuid

ROOT = Path(__file__).resolve().parents[2]


def project_path(value):
    path = (ROOT / value).resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Path must stay inside the project")
    return path


def build_workflow(request):
    if request.get("schema_version") != 1:
        raise ValueError("Unsupported image request schema")
    for field in ("id", "asset"):
        if not re.fullmatch(r"[a-z][a-z0-9_]{0,63}", request[field]):
            raise ValueError(f"Invalid {field}")
    if request["kind"] not in ("concept", "texture", "decal", "ui", "map", "reference"):
        raise ValueError("Invalid image kind")
    for field in ("width", "height"):
        limit = 4096 if request.get('mode') == 'upscale' else 2048
        if type(request[field]) is not int or not 256 <= request[field] <= limit or request[field] % 64:
            raise ValueError("Image dimensions must be multiples of 64, from 256 to 2048")
    if type(request["seed"]) is not int or not 0 <= request["seed"] < 2**64:
        raise ValueError("Seed must be an unsigned 64-bit integer")
    if request.get("tileable_required") or request.get("alpha_required"):
        raise ValueError("Basic SDXL workflow does not guarantee tiling or alpha. Author and verify a dedicated workflow before requesting these outputs.")
    steps, cfg = request.get('steps', 25), request.get('cfg', 7.0)
    if type(steps) is not int or not 1 <= steps <= 60 or type(cfg) not in (int, float) or not 1 <= cfg <= 15:
        raise ValueError('Steps must be 1–60 and CFG 1–15')
    values = {"__CHECKPOINT__": request["checkpoint"], "__PROMPT__": request["prompt"],
              "__NEGATIVE__": request["negative"], "__WIDTH__": request["width"],
              "__HEIGHT__": request["height"], "__SEED__": request["seed"],
              "__PREFIX__": "ai_game_studio/" + request["id"], '__STEPS__': steps, '__CFG__': cfg}
    if request.get('mode') == 'upscale':
        source = project_path(request['source_image'])
        if not source.is_file() or source.suffix.lower() != '.png':
            raise ValueError('Upscale source must be an existing project PNG')
        values['__INPUT_IMAGE__'] = 'studio_' + hashlib.sha256(source.read_bytes()).hexdigest()[:24] + '.png'
        values['__UPSCALE_MODEL__'] = request.get('upscale_model', 'RealESRGAN_x4plus.pth')
    def replace(value):
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace(item) for item in value]
        return values.get(value, value) if isinstance(value, str) else value
    return replace(json.loads(project_path(request["workflow"]).read_text(encoding="utf-8")))


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('Local image API redirects are not allowed')


def validate_server(server):
    endpoint = urlparse(server)
    if endpoint.scheme != "http" or endpoint.hostname not in ("127.0.0.1", "localhost", "::1") or endpoint.path not in ("", "/") or endpoint.username or endpoint.query or endpoint.fragment:
        raise ValueError("Only a local loopback ComfyUI HTTP endpoint is supported")


def combo_options(schema):
    """Comfy legacy nodes and current core V3 nodes expose different combo schemas."""
    if isinstance(schema[0], list):
        return schema[0]
    if schema[0] == 'COMBO' and len(schema) > 1:
        return schema[1].get('options', [])
    raise ValueError('Unrecognized model selection schema')


def run_job(request_file, execute=False, server='http://127.0.0.1:8188', timeout=180):
    validate_server(server)
    if timeout < 1:
        raise ValueError("Timeout must be positive")
    request = json.loads(project_path(request_file).read_text(encoding="utf-8-sig"))
    workflow = build_workflow(request)
    job = project_path("generated/image-jobs/" + request["id"] + "-" + uuid.uuid4().hex[:12])
    job.mkdir(parents=True)
    (job / "request.json").write_text(json.dumps(request, indent=2), encoding="utf-8")
    (job / "workflow.api.json").write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    record = {"status": "DRY_RUN", "job": job.relative_to(ROOT).as_posix(), "request": request["id"], "files": [], "workflow_sha256": hashlib.sha256(json.dumps(workflow, sort_keys=True).encode()).hexdigest()}
    record['resolution'] = [request['width'], request['height']]
    record['steps'] = next((n['inputs']['steps'] for n in workflow.values() if n['class_type'] == 'KSampler'), 0)
    stopped = threading.Event()
    samples = []
    monitor = None
    started = time.monotonic()

    def sample_vram():
        executable = shutil.which('nvidia-smi')
        if not executable:
            return
        while not stopped.is_set():
            try:
                measured = subprocess.run([executable, '--query-gpu=memory.used', '--format=csv,noheader,nounits'], capture_output=True,
                                          text=True, timeout=3, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                if measured.returncode == 0:
                    samples.append(float(measured.stdout.splitlines()[0]))
            except (OSError, ValueError, subprocess.TimeoutExpired):
                pass
            stopped.wait(1)
    opener = build_opener(ProxyHandler({}), NoRedirect())
    def http(route, body=None, binary=False):
        payload = None if body is None else json.dumps(body).encode()
        req = Request(server.rstrip("/") + route, data=payload, headers={"Content-Type": "application/json"})
        with opener.open(req, timeout=10) as response:
            data = response.read(64 * 1024 * 1024 + 1)
        if len(data) > 64 * 1024 * 1024:
            raise ValueError('Image API response exceeds 64 MiB')
        return data if binary else json.loads(data)
    try:
        if execute:
            record["status"] = "RUNNING"
            record['backend'] = http("/system_stats")
            if request.get('mode') == 'upscale':
                info = http('/object_info/UpscaleModelLoader')
                available = combo_options(info['UpscaleModelLoader']['input']['required']['model_name'])
                if request.get('upscale_model', 'RealESRGAN_x4plus.pth') not in available:
                    raise ValueError('Required upscale model is not installed')
                source = project_path(request['source_image']).read_bytes()
                if len(source) > 32 * 1024 * 1024:
                    raise ValueError('Source upload exceeds 32 MiB')
                filename = 'studio_' + hashlib.sha256(source).hexdigest()[:24] + '.png'
                boundary = 'studio-' + uuid.uuid4().hex
                body = (f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{filename}"\r\nContent-Type: image/png\r\n\r\n'.encode()
                        + source + f'\r\n--{boundary}--\r\n'.encode())
                upload = Request(server.rstrip('/') + '/upload/image', data=body, headers={'Content-Type': 'multipart/form-data; boundary=' + boundary})
                with opener.open(upload, timeout=30) as response:
                    uploaded = json.loads(response.read(1024 * 1024))
                for node in workflow.values():
                    if node['class_type'] == 'LoadImage':
                        node['inputs']['image'] = (uploaded.get('subfolder', '').strip('/') + '/' + uploaded['name']).lstrip('/')
                (job / 'workflow.api.json').write_text(json.dumps(workflow, indent=2), encoding='utf-8')
                record['workflow_sha256'] = hashlib.sha256(json.dumps(workflow, sort_keys=True).encode()).hexdigest()
            else:
                info = http('/object_info/CheckpointLoaderSimple')
                available = combo_options(info['CheckpointLoaderSimple']['input']['required']['ckpt_name'])
                if request['checkpoint'] not in available:
                    raise ValueError('Required checkpoint is not installed: ' + request['checkpoint'])
            monitor = threading.Thread(target=sample_vram, daemon=True)
            monitor.start()
            queued = http("/prompt", {"prompt": workflow, "client_id": uuid.uuid4().hex})
            if queued.get("error") or queued.get("node_errors"):
                raise RuntimeError(f"ComfyUI rejected workflow: {queued}")
            prompt_id = queued["prompt_id"]
            record["prompt_id"] = prompt_id
            (job / 'result.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                entry = http("/history/" + prompt_id).get(prompt_id)
                if entry:
                    if entry.get("status", {}).get("status_str") == "error":
                        raise RuntimeError(f"ComfyUI execution failed: {entry.get('status')}")
                    if entry.get("status", {}).get("completed"):
                        for output in entry.get("outputs", {}).values():
                            for image in output.get("images", []):
                                data = http("/view?" + urlencode(image), binary=True)
                                if not data.startswith(b"\x89PNG\r\n\x1a\n"):
                                    raise RuntimeError("Expected a PNG from the SaveImage node")
                                filename = f"image-{len(record['files']):03d}.png"
                                (job / filename).write_bytes(data)
                                record["files"].append({"path": filename, "sha256": hashlib.sha256(data).hexdigest()})
                        if not record["files"]:
                            raise RuntimeError("Workflow completed without images")
                        record["status"] = "PASS"
                        record['provider_execution_status'] = entry.get('status', {})
                        break
                time.sleep(1)
            else:
                raise TimeoutError(f"Timed out waiting for {prompt_id}; job may still be running. No global interrupt was sent.")
    except Exception as exc:
        record["status"] = "FAIL"
        record["error"] = str(exc)
        raise
    finally:
        stopped.set()
        if monitor:
            monitor.join(timeout=4)
        record['elapsed_seconds'] = round(time.monotonic() - started, 3)
        record['peak_device_vram_mib_sampled'] = max(samples) if samples else None
        record['vram_measurement'] = 'nvidia-smi approximately 1-second samples; entire GPU including other apps; not allocator peak'
        (job / "result.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"IMAGE_JOB_{record['status']}: {job}")
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('request')
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--server', default='http://127.0.0.1:8188')
    parser.add_argument('--timeout', type=int, default=180)
    args = parser.parse_args()
    run_job(args.request, args.execute, args.server, args.timeout)


if __name__ == "__main__":
    main()
