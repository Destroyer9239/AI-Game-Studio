"""Local ComfyUI adapter using only Python's standard library. Defaults to dry-run.

Explicit --execute requires an already-installed local ComfyUI and checkpoint.
No package/model installation or service startup is performed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode, urlparse
from urllib.request import Request, build_opener, ProxyHandler
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
        if type(request[field]) is not int or not 256 <= request[field] <= 2048 or request[field] % 64:
            raise ValueError("Image dimensions must be multiples of 64, from 256 to 2048")
    if type(request["seed"]) is not int or not 0 <= request["seed"] < 2**64:
        raise ValueError("Seed must be an unsigned 64-bit integer")
    if request.get("tileable_required") or request.get("alpha_required"):
        raise ValueError("Basic SDXL workflow does not guarantee tiling or alpha. Author and verify a dedicated workflow before requesting these outputs.")
    values = {"__CHECKPOINT__": request["checkpoint"], "__PROMPT__": request["prompt"],
              "__NEGATIVE__": request["negative"], "__WIDTH__": request["width"],
              "__HEIGHT__": request["height"], "__SEED__": request["seed"],
              "__PREFIX__": "ai_game_studio/" + request["id"]}
    def replace(value):
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace(item) for item in value]
        return values.get(value, value) if isinstance(value, str) else value
    return replace(json.loads(project_path(request["workflow"]).read_text(encoding="utf-8")))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--server", default="http://127.0.0.1:8188")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    endpoint = urlparse(args.server)
    if endpoint.scheme != "http" or endpoint.hostname not in ("127.0.0.1", "localhost", "::1") or endpoint.path not in ("", "/") or endpoint.username or endpoint.query or endpoint.fragment:
        raise ValueError("Only a local loopback ComfyUI HTTP endpoint is supported")
    if args.timeout < 1:
        raise ValueError("Timeout must be positive")
    request = json.loads(project_path(args.request).read_text(encoding="utf-8"))
    workflow = build_workflow(request)
    job = project_path("generated/image-jobs/" + request["id"] + "-" + uuid.uuid4().hex[:12])
    job.mkdir(parents=True)
    (job / "request.json").write_text(json.dumps(request, indent=2), encoding="utf-8")
    (job / "workflow.api.json").write_text(json.dumps(workflow, indent=2), encoding="utf-8")
    record = {"status": "DRY_RUN", "request": request["id"], "files": [], "workflow_sha256": hashlib.sha256(json.dumps(workflow, sort_keys=True).encode()).hexdigest()}
    opener = build_opener(ProxyHandler({}))
    def http(route, body=None, binary=False):
        payload = None if body is None else json.dumps(body).encode()
        req = Request(args.server.rstrip("/") + route, data=payload, headers={"Content-Type": "application/json"})
        with opener.open(req, timeout=10) as response:
            data = response.read()
        return data if binary else json.loads(data)
    try:
        if args.execute:
            record["status"] = "RUNNING"
            http("/system_stats")
            queued = http("/prompt", {"prompt": workflow, "client_id": uuid.uuid4().hex})
            if queued.get("error") or queued.get("node_errors"):
                raise RuntimeError(f"ComfyUI rejected workflow: {queued}")
            prompt_id = queued["prompt_id"]
            record["prompt_id"] = prompt_id
            deadline = time.monotonic() + args.timeout
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
                        break
                time.sleep(1)
            else:
                raise TimeoutError(f"Timed out waiting for {prompt_id}; job may still be running. No global interrupt was sent.")
    except Exception as exc:
        record["status"] = "FAIL"
        record["error"] = str(exc)
        raise
    finally:
        (job / "result.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"IMAGE_JOB_{record['status']}: {job}")


if __name__ == "__main__":
    main()
