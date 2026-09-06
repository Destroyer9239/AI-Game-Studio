"""Local procedural generation and conservative import/cleanup execution."""
from tools.providers.common import path, read_json

def build(request):
    if request['operation'] != 'generate_3d':
        raise ValueError('Blender adapter exposes generate_3d; other work uses authored Blender scripts')
    method = 'import' if request.get('source_file') else 'procedural'
    if method == 'procedural':
        manifest = path('tools/assets/' + request['name'] + '.json')
        ready = manifest.exists() and read_json(manifest).get('status') == 'ready'
    else:
        source = path(request['source_file'])
        if not source.is_file() or source.suffix.lower() not in ('.glb', '.gltf', '.fbx'):
            raise ValueError('Cleanup source must be an existing local GLB, glTF or FBX')
    return {'transport': 'local_cli', 'method': method, 'generator_ready': ready if method == 'procedural' else True,
            'next_step': 'Execute' if method != 'procedural' or ready else 'Agent must scaffold/author the original procedural generator before execution',
            'cost': {'amount': 0, 'unit': 'credits', 'basis': 'Local Blender; no API spend'}}
