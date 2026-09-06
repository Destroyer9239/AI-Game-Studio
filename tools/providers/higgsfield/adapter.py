"""Adapter for the officially documented Higgsfield CLI, not private website APIs."""
import json
import shutil
from tools.providers.common import path, public_https, run

def configured():
    return {'cli_available': bool(shutil.which('higgsfield')), 'authentication_verified': False,
            'required_action': 'Install the official CLI if needed, then complete higgsfield auth login; never inspect or copy login tokens into the project'}

def build(request):
    operation = request['operation']
    images = request.get('source_images', [])
    method = request.get('method', 'auto')
    if method == 'auto':
        method = 'multi_image' if len(images) > 1 else 'image' if images else 'text'
    options = request.get('options', {})
    if options:
        raise ValueError('Higgsfield adapter uses reviewed fixed model defaults; new flags require documented schema review')
    args = []
    if operation == 'generate_3d':
        if method == 'text':
            model = 'tripo_3d'
            args = ['--prompt', request.get('prompt', ''), '--pbr', 'true', '--texture', 'true']
            if request.get('quality') == 'hero':
                args += ['--geometry_quality', 'detailed', '--texture_quality', 'detailed']
        elif method in ('image', 'multi_image'):
            model = 'image_to_3d' if method == 'image' else 'multi_image_to_3d'
            if (method == 'image' and len(images) != 1) or not 1 <= len(images) <= 4:
                raise ValueError('Select one image or up to four matching views')
            for image in images:
                # CLI documents UUID/path inputs; avoid guessing support for remote URLs.
                file = path(image)
                if not file.is_file() or file.suffix.lower() not in ('.png', '.jpg', '.jpeg'):
                    raise ValueError('Higgsfield reference must be a local PNG/JPEG')
                args += ['--image', str(file)]
            args += ['--should_texture', 'true', '--enable_pbr', 'true']
        else:
            raise ValueError('Unsupported Higgsfield 3D method')
    elif operation in ('generate_image', 'edit_image'):
        model = 'nano_banana_2'
        args = ['--prompt', request.get('prompt', '')]
        if len(images) > 14 or (operation == 'edit_image' and not images):
            raise ValueError('Image editing requires 1–14 local references')
        for image in images:
            file = path(image)
            if not file.is_file() or file.suffix.lower() not in ('.png', '.jpg', '.jpeg'):
                raise ValueError('Image reference must be a local PNG/JPEG')
            args += ['--image', str(file)]
        method = 'image_edit' if images else 'text'
    elif operation == 'generate_video':
        model = 'seedance_2_0'
        args = ['--prompt', request.get('prompt', ''), '--duration', '5', '--resolution', '720p', '--mode', 'std']
        if images:
            raise ValueError('This adapter currently implements text-to-video only')
    elif operation == 'rig':
        model = '3d_rigging'
        args = ['--model_url', public_https(request.get('source_file', ''))]
    else:
        raise ValueError('Unsupported Higgsfield operation')
    if operation in ('generate_image', 'edit_image', 'generate_video') or (operation == 'generate_3d' and method == 'text'):
        if not request.get('prompt', '').strip():
            raise ValueError('A prompt is required')
    return {'transport': 'official_cli', 'model': model, 'arguments': args, 'method': method,
            'cost': {'amount': None, 'unit': 'credits', 'basis': 'Unknown until official CLI generate cost / account pricing is checked; no price guessed'}}

def executable():
    found = shutil.which('higgsfield')
    if not found:
        raise ValueError('Official Higgsfield CLI is not installed; adapter is prepared but cannot make live requests')
    return found

def submit(plan, runner=run):
    # Submit once without --wait so the job ID can be persisted before polling.
    output = json.loads(runner([executable(), 'generate', 'create', plan['request']['model'], *plan['request']['arguments'], '--json', '--no-color']))
    task_id = output.get('id') or output.get('job_id') or output.get('job_set_id')
    if not task_id:
        raise RuntimeError('Unrecognized CLI submission response; reconcile the account before any retry')
    return str(task_id)

def status(plan, task_id, runner=run):
    if not task_id or not all(c.isalnum() or c in '-_' for c in task_id):
        raise ValueError('Invalid Higgsfield job ID')
    return json.loads(runner([executable(), 'generate', 'get', task_id, '--json', '--no-color']))

def quote(plan, runner=run):
    return json.loads(runner([executable(), 'generate', 'cost', plan['request']['model'], *plan['request']['arguments'], '--json', '--no-color']))
