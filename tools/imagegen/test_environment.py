"""Offline safety/material tests plus real exported GLB texture contracts."""
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
from tools.imagegen import submit_image, material_factory, backend


class EnvironmentTests(unittest.TestCase):
    def test_combo_compatibility(self):
        self.assertEqual(submit_image.combo_options([['model']]),['model'])
        self.assertEqual(submit_image.combo_options(['COMBO',{'options':['model']}]),['model'])
        with self.assertRaises(ValueError): submit_image.combo_options(['UNKNOWN'])

    def test_loopback_only(self):
        for server in ('https://example.com','http://127.0.0.1@evil.com','http://localhost/path'):
            with self.assertRaises(ValueError): submit_image.validate_server(server)

    def test_periodic_edges(self):
        source = np.random.default_rng(2).integers(0,256,(64,64,3),dtype=np.uint8)
        result = material_factory.periodic_color(source,8)
        np.testing.assert_array_equal(result[0],result[-1])
        np.testing.assert_array_equal(result[:,0],result[:,-1])
        np.testing.assert_array_equal(result[16:48,16:48],source[16:48,16:48])

    def test_material_package(self):
        self.assertTrue(material_factory.validate(material_factory.ROOT/'game/assets/textures/industrial_concrete'))

    def test_exported_texture_contract(self):
        data = (material_factory.ROOT/'game/assets/models/environment_probe.glb').read_bytes()
        length,kind = struct.unpack_from('<II',data,12)
        self.assertEqual(kind,0x4e4f534a)
        gltf = json.loads(data[20:20+length])
        concrete = next(m for m in gltf['materials'] if m['name']=='Concrete_4K_Authored_Relief')
        self.assertIn('baseColorTexture',concrete['pbrMetallicRoughness'])
        self.assertIn('metallicRoughnessTexture',concrete['pbrMetallicRoughness'])
        self.assertIn('normalTexture',concrete)
        self.assertGreaterEqual(len(gltf['images']),3)
        for image in gltf['images']:
            self.assertIn('bufferView',image)
            view = gltf['bufferViews'][image['bufferView']]
            binary_start = 20+length+8
            offset = binary_start+view.get('byteOffset',0)
            png = data[offset:offset+view['byteLength']]
            self.assertEqual(png[:8],b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack_from('>II',png,16),(4096,4096))

    def test_all_workflows(self):
        for file in (submit_image.ROOT/'tools/imagegen/requests').glob('*.json'):
            request=json.loads(file.read_text(encoding='utf-8-sig'))
            graph=submit_image.build_workflow(request)
            self.assertTrue(any(n['class_type']=='SaveImage' for n in graph.values()))

    def test_live_pid_detection(self):
        import os
        self.assertTrue(backend.process_alive(os.getpid()))

    def test_backend_refuses_busy_shutdown(self):
        with tempfile.TemporaryDirectory() as temp:
            control=Path(temp)
            (control/'comfyui.json').write_text(json.dumps({'run_id':'a'*32,'pid':123}))
            with patch.object(backend,'CONTROL',control), patch.object(backend,'STATE',control/'comfyui.json'), patch.object(backend,'process_alive',return_value=True), patch.object(backend,'status',return_value={'status':'REACHABLE'}), patch.object(backend,'api',return_value={'queue_running':[1]}):
                with self.assertRaisesRegex(RuntimeError,'queued/running'): backend.stop()
            self.assertFalse((control/('a'*32+'.stop')).exists())

    def test_stale_pid_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            control=Path(temp)
            (control/'comfyui.json').write_text(json.dumps({'run_id':'b'*32,'pid':123}))
            with patch.object(backend,'CONTROL',control), patch.object(backend,'STATE',control/'comfyui.json'), patch.object(backend,'process_alive',return_value=False):
                self.assertEqual(backend.stop()['action'],'RECOVERED_EXIT_RECORD')
            self.assertTrue((control/('b'*32+'.exit.json')).exists())

if __name__ == '__main__': unittest.main()
