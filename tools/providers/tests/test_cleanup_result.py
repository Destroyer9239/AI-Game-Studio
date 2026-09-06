"""Acceptance checks on the actually generated textured cleanup fixture."""
import hashlib
import json
import struct
import unittest
from tools.providers.common import path, read_json
from tools.providers.service import glb_summary


def glb(file):
    data = path(file).read_bytes()
    size = struct.unpack_from('<I', data, 12)[0]
    return json.loads(data[20:20 + size]), data[28 + size:]


def image_hashes(doc, binary):
    result = {}
    for image in doc['images']:
        view = doc['bufferViews'][image['bufferView']]
        start = view.get('byteOffset', 0)
        data = binary[start:start + view['byteLength']]
        assert data.startswith(b'\x89PNG\r\n\x1a\n')
        result[image['name']] = hashlib.sha256(data).hexdigest()
    return result


class CleanupAcceptance(unittest.TestCase):
    def test_pbr_embedded_image_bytes_preserved(self):
        before, source = glb('generated/provider-fixtures/textured_source.glb')
        after, output = glb('game/assets/models/provider_cleanup_probe.glb')
        self.assertEqual(image_hashes(before, source), image_hashes(after, output))
        slots = glb_summary(path('game/assets/models/provider_cleanup_probe.glb'))['textures'][0]['slots']
        self.assertEqual(set(slots), {'baseColorTexture', 'normalTexture', 'metallicRoughnessTexture', 'emissiveTexture'})

    def test_geometry_transform_origin_normals_and_lod(self):
        doc, binary = glb('game/assets/models/provider_cleanup_probe.glb')
        node = next(n for n in doc['nodes'] if n['name'] == 'PBR_TestHull')
        self.assertFalse(set(node) & {'matrix', 'translation', 'rotation', 'scale'})
        prim = doc['meshes'][node['mesh']]['primitives'][0]
        acc = doc['accessors'][prim['attributes']['POSITION']]
        self.assertAlmostEqual(max(b-a for a,b in zip(acc['min'],acc['max'])), 3.0, places=4)
        self.assertAlmostEqual(acc['min'][1], 0, places=4)  # Godot/glTF +Y up.
        normals = doc['accessors'][prim['attributes']['NORMAL']]
        view = doc['bufferViews'][normals['bufferView']]
        start = view.get('byteOffset', 0) + normals.get('byteOffset', 0)
        for i in range(normals['count']):
            n = struct.unpack_from('<fff', binary, start + i * view.get('byteStride', 12))
            self.assertAlmostEqual(sum(x*x for x in n), 1, places=4)
        self.assertTrue(any(n['name'].endswith('-colonly') for n in doc['nodes']))
        high = glb_summary(path('game/assets/models/provider_cleanup_probe.glb'))['polygon_count']
        low = glb_summary(path('game/assets/models/provider_cleanup_probe_lod1.glb'))['polygon_count']
        self.assertTrue(0 < low < high)

    def test_packed_materials_and_actual_godot_preview(self):
        record = read_json(path('generated/manifests/provider_cleanup_probe.json'))
        self.assertEqual(record['Godot_import_status'], 'PASS')
        self.assertTrue(all(i['packed'] for i in record['cleanup_audit']['textures']))
        self.assertTrue(path(record['processed_blender_file']).is_file())
        self.assertTrue(path(record['preview']).read_bytes().startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertIn('PIPELINE_PASS: preview', path(record['validation']['log']).read_text())


if __name__ == '__main__':
    unittest.main()
