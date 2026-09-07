"""Start/reuse/stop only the studio-owned loopback ComfyUI process."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import build_opener, ProxyHandler
import uuid

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.imagegen.submit_image import NoRedirect, validate_server
from tools.providers.common import read_json, write_json

CONTROL = ROOT / 'generated/backend'
STATE = CONTROL / 'comfyui.json'


def process_alive(pid):
    import ctypes
    if sys.platform != 'win32':
        import os
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    handle = kernel.OpenProcess(0x1000, False, int(pid))
    if not handle:
        if ctypes.get_last_error() == 87:
            return False
        raise OSError('Cannot safely inspect the previous backend PID')
    try:
        code = ctypes.c_ulong()
        if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
            raise OSError('Cannot inspect backend exit status')
        return code.value == 259
    finally:
        kernel.CloseHandle(handle)


def configuration():
    return read_json(ROOT / 'tools/providers/image_generation/comfyui.json')


def api(route, config=None):
    config = config or configuration()
    validate_server(config['server'])
    with build_opener(ProxyHandler({}), NoRedirect()).open(config['server'].rstrip('/') + route, timeout=3) as response:
        return json.loads(response.read(4 * 1024 * 1024))


def status(config=None):
    config = config or configuration()
    try:
        stats = api('/system_stats', config)
        return {'status': 'REACHABLE', 'server': config['server'], 'system': stats.get('system', {}), 'devices': stats.get('devices', [])}
    except (OSError, ValueError):
        return {'status': 'UNAVAILABLE', 'server': config['server']}


def start(config=None):
    config = config or configuration()
    # Management is deliberately fixed to the reviewed local installation endpoint.
    if config['server'] != 'http://127.0.0.1:8188':
        raise ValueError('Automatic startup only manages 127.0.0.1:8188')
    current = status(config)
    if current['status'] == 'REACHABLE':
        return {**current, 'action': 'REUSED_EXISTING_SERVER'}
    runtime = Path(config['runtime']).resolve()
    python = runtime / 'python_embeded/python.exe'
    if not python.is_file() or not (runtime / 'ComfyUI/main.py').is_file():
        raise ValueError('Configured ComfyUI Portable installation is missing')
    CONTROL.mkdir(parents=True, exist_ok=True)
    lock = CONTROL / 'start.lock'
    try:
        with lock.open('x') as file:
            file.write(str(time.time()))
    except FileExistsError:
        raise RuntimeError('Backend start is already in progress; inspect the owned process/state before retrying')
    try:
        if STATE.exists():
            prior = read_json(STATE)
            if not (CONTROL / (prior['run_id'] + '.exit.json')).exists():
                if process_alive(prior['pid']):
                    raise RuntimeError('Previous backend PID is still alive without a reachable API; inspect its log before starting a duplicate')
                write_json(CONTROL / (prior['run_id'] + '.exit.json'), {'exited': True, 'recovered': 'verified previous PID exited', 'time': time.time()})
        run_id = uuid.uuid4().hex
        logfile = CONTROL / (run_id + '.log')
        command = [str(python), '-s', str(ROOT / 'tools/imagegen/managed_server.py'), '--runtime', str(runtime),
                   '--control', str(CONTROL), '--run-id', run_id]
        with logfile.open('w', encoding='utf-8') as log:
            process = subprocess.Popen(command, cwd=runtime, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        state = {'pid': process.pid, 'run_id': run_id, 'runtime': str(runtime), 'log': str(logfile), 'started': time.time()}
        write_json(STATE, state)
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            current = status(config)
            if current['status'] == 'REACHABLE':
                return {**current, 'action': 'STARTED', 'pid': process.pid, 'log': str(logfile)}
            if process.poll() is not None:
                raise RuntimeError('ComfyUI exited during startup; inspect ' + str(logfile))
            time.sleep(1)
        raise TimeoutError('ComfyUI startup timed out; inspect the owned process log, do not duplicate it')
    finally:
        lock.unlink()


def stop(config=None):
    config = config or configuration()
    if not STATE.exists():
        return {'status': 'NOT_OWNED', 'action': 'NO_PROCESS_STOPPED'}
    state = read_json(STATE)
    run_id = state['run_id']
    if not isinstance(run_id, str) or len(run_id) != 32 or not all(c in '0123456789abcdef' for c in run_id):
        raise ValueError('Invalid managed run identity')
    exited = CONTROL / (run_id + '.exit.json')
    if exited.exists():
        return {'status': 'STOPPED', 'action': 'ALREADY_EXITED'}
    if not process_alive(state['pid']):
        write_json(exited, {'exited': True, 'recovered': 'verified previous PID exited', 'time': time.time()})
        return {'status': 'STOPPED', 'action': 'RECOVERED_EXIT_RECORD'}
    current = status(config)
    if current['status'] == 'REACHABLE':
        queue = api('/queue', config)
        if queue.get('queue_running') or queue.get('queue_pending'):
            raise RuntimeError('ComfyUI has queued/running work; refusing to interrupt it')
    # Only this wrapper watches this unique file; no unrelated PID is ever killed.
    (CONTROL / (run_id + '.stop')).write_text('cooperative stop', encoding='utf-8')
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if exited.exists() and status(config)['status'] == 'UNAVAILABLE':
            return {'status': 'STOPPED', 'action': 'COOPERATIVE_SHUTDOWN', 'pid': state['pid']}
        time.sleep(0.5)
    raise TimeoutError('Owned ComfyUI did not confirm clean shutdown; no process was force-killed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('start', 'stop', 'restart', 'status'))
    args = parser.parse_args()
    if args.action == 'restart':
        stop()
        result = start()
    else:
        result = globals()[args.action]()
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'status': 'FAIL', 'error': str(exc)}))
        sys.exit(1)
