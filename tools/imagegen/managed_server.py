"""Run official ComfyUI unchanged, with an owned cooperative shutdown signal."""
import _thread
import argparse
import json
import os
from pathlib import Path
import runpy
import sys
import threading
import time

parser = argparse.ArgumentParser()
parser.add_argument('--runtime', required=True)
parser.add_argument('--control', required=True)
parser.add_argument('--run-id', required=True)
args = parser.parse_args()
runtime, control = Path(args.runtime).resolve(), Path(args.control).resolve()
stop_file = control / (args.run_id + '.stop')


def watch():
    while not stop_file.exists():
        time.sleep(0.25)
    _thread.interrupt_main()


threading.Thread(target=watch, daemon=True).start()
main = runtime / 'ComfyUI/main.py'
sys.path.insert(0, str(main.parent))
os.chdir(main.parent)
sys.argv = [str(main), '--windows-standalone-build', '--listen', '127.0.0.1', '--port', '8188',
            '--disable-auto-launch', '--disable-all-custom-nodes', '--disable-api-nodes']
try:
    runpy.run_path(str(main), run_name='__main__')
except KeyboardInterrupt:
    print('STUDIO_COMFY_STOPPED: cooperative shutdown', flush=True)
finally:
    (control / (args.run_id + '.exit.json')).write_text(json.dumps({'run_id': args.run_id, 'exited': True, 'time': time.time()}))
