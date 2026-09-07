"""Bridge to the existing local image workflow; no paid/custom Comfy nodes."""
import contextlib
import io
import json
from urllib.request import build_opener, ProxyHandler
from tools.providers.common import path, read_json, write_json
from tools.imagegen.submit_image import build_workflow, run_job, validate_server, NoRedirect

LOCAL_NODES = {'CheckpointLoaderSimple', 'CLIPTextEncode', 'EmptyLatentImage', 'KSampler', 'VAEDecode', 'SaveImage', 'LoadImage', 'UpscaleModelLoader', 'ImageUpscaleWithModel', 'ImageScale'}


def configuration():
    config = read_json(path('tools/providers/image_generation/comfyui.json'))
    validate_server(config['server'])
    return config


def configured():
    config = configuration()
    return {'server': config['server'], 'backend_status': config['install_status'], 'health': 'NOT_PROBED'}


def health():
    config = configuration()
    try:
        with build_opener(ProxyHandler({}), NoRedirect()).open(config['server'].rstrip('/') + '/system_stats', timeout=3) as response:
            data = json.loads(response.read(1024 * 1024))
        return {'status': 'REACHABLE', 'devices': data.get('devices', []), 'inference_verified': False}
    except (OSError, ValueError):
        return {'status': 'UNAVAILABLE', 'inference_verified': False}

def build(request):
    image_request = read_json(path(request.get('image_request', '')))
    workflow = build_workflow(image_request)
    if request['operation'] not in ('generate_image', 'generate_texture'):
        raise ValueError('ComfyUI adapter supports images/texture concepts only')
    if any(node.get('class_type') not in LOCAL_NODES for node in workflow.values()):
        raise ValueError('Only reviewed core local nodes are allowed; paid API/custom nodes are not local generation')
    return {'transport': 'local_http', 'method': image_request.get('mode', 'text'), 'model': image_request.get('upscale_model', image_request['checkpoint']), 'image_request': request['image_request'],
            'configuration': configuration(),
            'cost': {'amount': 0, 'unit': 'credits', 'basis': 'Local inference; backend/model must already be installed'}}


def execute(plan, directory):
    from tools.providers.service import manifest
    build(plan['asset'])
    config = plan['request']['configuration']
    if config.get('auto_start') and health()['status'] != 'REACHABLE':
        from tools.imagegen.backend import start
        start(config)
    output = io.StringIO()
    try:
        with contextlib.redirect_stdout(output):
            record = run_job(plan['request']['image_request'], True, config['server'], config['timeout_seconds'])
    finally:
        (directory / 'image.log').write_text(output.getvalue(), encoding='utf-8')
    original = path(record['job']) / record['files'][0]['path']
    result = manifest(plan, original, status='IMAGE_SOURCE_PENDING_VISUAL_REVIEW')
    result['image_job'] = record
    result['performance'] = {key: record[key] for key in ('elapsed_seconds', 'resolution', 'steps', 'peak_device_vram_mib_sampled', 'vram_measurement')}
    result['media_files'] = [(path(record['job']) / f['path']).relative_to(path('.')).as_posix() for f in record['files']]
    result['cost']['reported_credits'] = 0
    result['image_specification'] = read_json(path(plan['request']['image_request']))
    result['source_prompt'] = result['image_specification']['prompt']
    result['license_provenance_notes'] = result['image_specification'].get('model_license', '') + '; ' + result['image_specification'].get('model_source', '')
    write_json(path('generated/manifests/' + plan['asset']['name'] + '.json'), result)
    return result
