"""Meshy's official REST API; no SDK/package or network call during planning."""
import os
import re
from tools.providers.common import api_json, reference

ORIGIN = 'https://api.meshy.ai'
PRICING = 'https://docs.meshy.ai/en/api/pricing'

def configured():
    return {'api_key_present': bool(os.environ.get('MESHY_API_KEY')), 'authentication_verified': False}

def headers():
    key = os.environ.get('MESHY_API_KEY')
    if not key:
        raise ValueError('Set MESHY_API_KEY securely outside the repository before live use')
    return {'Authorization': 'Bearer ' + key}

def build(request):
    operation = request['operation']
    options = request.get('options', {})
    allowed = {'ai_model', 'smart_topology', 'target_polycount', 'should_texture', 'height_meters', 'input_task_id', 'rig_task_id', 'action_id'}
    if set(options) - allowed:
        raise ValueError('Unsupported Meshy option; update the adapter from official docs first')
    model = options.get('ai_model', 'meshy-6')
    smart = options.get('smart_topology', False)
    if smart:
        model = 'meshy-t2'
    if model not in ('meshy-6', 'meshy-7', 'meshy-t2'):
        raise ValueError('Use a reviewed, pinned Meshy model')
    if model == 'meshy-t2' and not smart:
        raise ValueError('meshy-t2 requires smart_topology=true')
    prompt = request.get('prompt', '')
    if len(prompt) > 800:
        raise ValueError('Meshy prompt limit is 800 characters')
    images = request.get('source_images', [])
    method = request.get('method', 'auto')
    if method == 'auto':
        method = 'multi_image' if len(images) > 1 else 'image' if images else 'text'
    count = options.get('target_polycount', 8000)
    if type(count) is not int or not 100 <= count <= (15000 if smart else 300000):
        raise ValueError('Invalid Meshy target polygon count')
    body = {}
    if operation == 'generate_3d':
        if method == 'refine':
            if smart:
                raise ValueError('Refine requires a texture model, not meshy-t2')
            route = '/openapi/v2/text-to-3d'
            body = {'mode': 'refine', 'preview_task_id': options.get('input_task_id'), 'ai_model': model,
                    'enable_pbr': True, 'texture_resolution': '2k', 'target_formats': ['glb']}
            if not body['preview_task_id']:
                raise ValueError('Refine requires the completed preview input_task_id')
            cost = 10
        else:
            body = {'ai_model': model, 'model_type': 'smart-topology' if smart else 'standard',
                    'target_polycount': count, 'topology': 'triangle', 'target_formats': ['glb']}
            if not smart:
                body['should_remesh'] = True
            if method == 'text':
                if not prompt.strip():
                    raise ValueError('Text-to-3D needs a prompt')
                route = '/openapi/v2/text-to-3d'
                body.update(mode='preview', prompt=prompt)
                cost = 5 if smart else 20
            elif method in ('image', 'multi_image'):
                if (method == 'image' and len(images) != 1) or not 1 <= len(images) <= 4:
                    raise ValueError('Image-to-3D requires one image; multi-image accepts 1–4')
                if smart and method == 'multi_image':
                    raise ValueError('Smart topology multi-image pricing/model route not enabled by this adapter')
                route = '/openapi/v1/' + ('image-to-3d' if method == 'image' else 'multi-image-to-3d')
                body['image_url' if method == 'image' else 'image_urls'] = reference(images[0]) if method == 'image' else [reference(image) for image in images]
                textured = options.get('should_texture', True)
                if type(textured) is not bool:
                    raise ValueError('should_texture must be a boolean')
                body.update(should_texture=textured, enable_pbr=textured)
                cost = (5 if smart else 20) + (10 if textured else 0)
            else:
                raise ValueError('Unsupported Meshy generation method')
    elif operation in ('remesh', 'retexture', 'rig'):
        route = '/openapi/v1/' + {'rig': 'rigging'}.get(operation, operation)
        if options.get('input_task_id'):
            body['input_task_id'] = options['input_task_id']
        elif request.get('source_file'):
            body['model_url'] = reference(request['source_file'], image=False)
        else:
            raise ValueError('Operation needs source_file or input_task_id')
        if operation == 'remesh':
            body.update(target_formats=['glb'], topology='triangle', target_polycount=count)
            cost = 5
        elif operation == 'retexture':
            if not prompt.strip():
                raise ValueError('Retexture needs a style prompt')
            body.update(text_style_prompt=prompt, enable_original_uv=True, enable_pbr=True, ai_model='meshy-6')
            cost = 10
        else:
            if request['asset_type'] != 'humanoid':
                raise ValueError('Meshy auto-rigging is for humanoids; do not route spacecraft to it')
            height = options.get('height_meters', 1.7)
            if not isinstance(height, (float, int)) or height <= 0:
                raise ValueError('height_meters must be positive')
            body['height_meters'] = height
            cost = 5
    elif operation == 'animate':
        route = '/openapi/v1/animations'
        if not options.get('rig_task_id') or type(options.get('action_id')) is not int:
            raise ValueError('Animation requires rig_task_id and an official animation-library action_id')
        body = {'rig_task_id': options['rig_task_id'], 'action_id': options['action_id']}
        cost = 3
    else:
        raise ValueError('Meshy adapter does not implement this operation')
    return {'transport': 'rest', 'route': route, 'body': body, 'method': method,
            'cost': {'amount': cost, 'unit': 'credits', 'basis': 'Official pricing snapshot 2026-09-05; verify before approval', 'source': PRICING}}

def submit(plan, transport=api_json):
    response = transport(ORIGIN, plan['request']['route'], headers(), plan['request']['body'])
    task_id = response.get('result')
    if not isinstance(task_id, str) or not re.fullmatch(r'[a-zA-Z0-9-]+', task_id):
        raise RuntimeError('Submission response has no valid task ID; do not automatically retry')
    return task_id

def status(plan, task_id, transport=api_json):
    if not re.fullmatch(r'[a-zA-Z0-9-]+', task_id):
        raise ValueError('Invalid task ID')
    return transport(ORIGIN, plan['request']['route'] + '/' + task_id, headers())

def balance(transport=api_json):
    return transport(ORIGIN, '/openapi/v1/balance', headers())

def usage(transport=api_json):
    # Studio/Enterprise team keys only; propagate a 403 instead of claiming no usage.
    return transport(ORIGIN, '/openapi/v1/usage/tasks', headers())
