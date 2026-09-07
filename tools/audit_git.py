"""Check candidate/tracked files for obvious secrets and prohibited model artifacts.
Reports file names only, never matched content. This is not a full secret scanner.
"""
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
files=set(subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0'))
files.update(subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0'))
patterns=[rb'sk-[A-Za-z0-9_-]{32,}',rb'gh[pousr]_[A-Za-z0-9]{30,}',
          rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
          rb'(?i)(?:api_key|access_token|auth_token)\s*[=:]\s*["\x27][A-Za-z0-9_-]{24,}["\x27]']
issues=[]
checked=0
for name in sorted(files-{''}):
    file=ROOT/name
    if not file.is_file(): continue
    checked+=1
    if file.suffix.lower() in ('.safetensors','.ckpt','.pth','.pt') or file.name.startswith('.env'):
        issues.append({'file':name,'reason':'prohibited model/secret filename'})
    if file.stat().st_size>95*1024*1024:
        issues.append({'file':name,'reason':'oversized repository file'})
    if file.suffix.lower() in ('.py','.ps1','.gd','.json','.md','.toml','.yaml','.yml','.txt'):
        data=file.read_bytes()
        if any(re.search(pattern,data) for pattern in patterns):
            issues.append({'file':name,'reason':'possible credential pattern'})
report={'status':'FAIL' if issues else 'PASS','files_checked':checked,'issues':issues,
        'scope':'tracked and nonignored candidate working files; obvious patterns only, no secret values printed'}
target=ROOT/'generated/reports/git_security_audit.json'
target.parent.mkdir(parents=True,exist_ok=True)
target.write_text(json.dumps(report,indent=2))
print(json.dumps(report))
raise SystemExit(bool(issues))
