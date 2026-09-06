"""Real loopback HTTP protocol test with a fake inference backend; no models."""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import unittest
from unittest.mock import patch
import uuid
from tools.providers import service
from tools.providers.common import path, read_json, write_json
from tools.providers.image_generation import comfyui


class ComfyProtocolTests(unittest.TestCase):
    def test_job_health_poll_download_and_manifest(self):
        calls = []
        # Actual PNG fixture already rendered by Godot, not pretend AI inference.
        png = path('generated/previews/provider_cleanup_probe.png').read_bytes()
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def send(self, value):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(value if isinstance(value, bytes) else json.dumps(value).encode())
            def do_GET(self):
                calls.append(self.path)
                if self.path == '/system_stats': self.send({'devices': [{'name': 'MOCK_NO_INFERENCE'}]})
                elif self.path.startswith('/history/'):
                    self.send({'mock-prompt': {'status': {'completed': True}, 'outputs': {'9': {'images': [{'filename': 'test.png', 'type': 'output', 'subfolder': ''}]}}}})
                elif self.path.startswith('/view?'): self.send(png)
                else: self.send_error(404)
            def do_POST(self):
                calls.append(self.path)
                body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if self.path == '/prompt' and body.get('prompt'): self.send({'prompt_id': 'mock-prompt'})
                else: self.send_error(400)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        config = {**comfyui.configuration(), 'server': 'http://127.0.0.1:' + str(server.server_port)}
        try:
            with patch.object(comfyui, 'configuration', return_value=config):
                self.assertEqual(comfyui.health()['status'], 'REACHABLE')
                directory, plan = service.prepare({'name': 'unit_comfy_' + uuid.uuid4().hex[:8], 'operation': 'generate_image', 'provider': 'comfyui', 'image_request': 'tools/imagegen/requests/test_fighter_concept.json'})
                result = service.execute(str(directory))
            self.assertEqual(path(result['media_files'][0]).read_bytes(), png)
            self.assertEqual(result['image_job']['status'], 'PASS')
            self.assertEqual(result['cost']['reported_credits'], 0)
            self.assertEqual(calls.count('/prompt'), 1)
            self.assertFalse(result['final_glb'])
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=3)

    def test_unreviewed_nodes_and_missing_backend(self):
        with patch.object(comfyui, 'build_workflow', return_value={'1': {'class_type': 'PaidCloudNode'}}):
            with self.assertRaisesRegex(ValueError, 'local nodes'):
                comfyui.build({'operation': 'generate_image', 'image_request': 'tools/imagegen/requests/test_fighter_concept.json'})
        with patch('urllib.request.OpenerDirector.open', side_effect=OSError('mock offline')):
            self.assertEqual(comfyui.health()['status'], 'UNAVAILABLE')


if __name__ == '__main__': unittest.main()
