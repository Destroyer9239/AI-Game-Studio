"""Prepare dependent concept/view requests; never submit or spend credits."""
from tools.providers.common import asset_id, path, write_json, read_json


def scaffold(request):
    name = asset_id(request['name'])
    if len(name) > 55:
        raise ValueError('Multi-view base ID must leave room for view suffixes (maximum 55 characters)')
    folder = path('generated/reference-plans/' + name)
    if folder.exists():
        raise ValueError('Reference plan exists; preserve it or use a new version ID')
    base = read_json(path('tools/imagegen/requests/test_fighter_concept.json'))
    outputs = {}
    for index, view in enumerate(('concept', 'front', 'side', 'rear', 'top')):
        image_request = {**base, 'id': name + '_' + view, 'asset': name, 'kind': 'concept' if view == 'concept' else 'reference',
                         'seed': base['seed'] + index, 'prompt': request.get('prompt', '') + '. ' + view + ' view, consistent design, neutral background, full object visible.',
                         'notes': 'Draft: independent SDXL prompts do not guarantee matching views. Review concept first; use reference-conditioned editing or Blender orthographic renders for consistency.'}
        write_json(folder / (view + '.image.json'), image_request)
        write_json(folder / (view + '.provider.json'), {'name': name + '_' + view, 'asset_type': 'reference', 'operation': 'generate_image', 'provider': 'comfyui', 'image_request': (folder / (view + '.image.json')).relative_to(path('.')).as_posix()})
        outputs[view] = f'generated/references/{name}/{view}.png'
    final = {**request, 'provider': request.get('provider', 'auto'), 'cost_policy': 'consider_paid', 'method': 'multi_image',
             'operation': 'generate_3d', 'reference_views': outputs,
             'source_images': [outputs[v] for v in ('front', 'side', 'rear', 'top')]}
    write_json(folder / 'generate_3d.json', final)
    write_json(folder / 'sequence.json', {'status': 'PREPARED_NOT_GENERATED', 'steps': ['generate/review concept', 'derive and review consistent front/side/rear/top', 'place approved images at declared paths', 'plan generate_3d.json', 'approve one paid request if selected', 'fetch/Blender/Godot/preview'], 'references': outputs})
    return {'status': 'MULTIVIEW_PREPARED', 'directory': folder.relative_to(path('.')).as_posix(), 'references': outputs}
