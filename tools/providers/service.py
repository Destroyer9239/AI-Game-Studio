"""Provider selection, immutable plans, task tracking and staged asset promotion."""
from datetime import datetime, timezone, timedelta
import importlib
import json
from pathlib import Path
import shutil
import struct
import time
from urllib.parse import urlparse
import uuid
from tools.providers.common import ROOT, OPERATIONS, asset_id, path, read_json, write_json, digest, file_hash, now, sanitized, reject_secrets, consume_approval, download, run

ADAPTERS = {'blender': 'blender.adapter', 'meshy': 'meshy.adapter', 'higgsfield': 'higgsfield.adapter', 'comfyui': 'image_generation.comfyui'}

def registry():
    return read_json(path('tools/providers/provider_registry.json'))

def adapter(name):
    if name not in ADAPTERS:
        raise ValueError('Provider is a placeholder or unknown; no executable adapter')
    return importlib.import_module('tools.providers.' + ADAPTERS[name])

def select_provider(request):
    chosen = request.get('provider', 'auto')
    if chosen != 'auto':
        return chosen, 'Provider explicitly selected'
    operation = request['operation']
    if operation == 'generate_3d':
        if not request.get('source_file') and (request.get('source_images') or request.get('quality') == 'hero' and request.get('complexity') == 'high') and request.get('cost_policy', 'local_first') == 'consider_paid':
            if adapter('higgsfield').configured()['cli_available'] and not adapter('meshy').configured()['api_key_present']:
                return 'higgsfield', 'Important/reference asset; installed official CLI preferred; authentication and per-job approval still required'
            return 'meshy', 'Important/reference asset: plan multi-view/PBR generation; credentials and approval may be pending, never submit automatically'
        if request.get('source_file') or request['asset_type'] in ('spacecraft', 'mechanical', 'prop', 'architecture'):
            return 'blender', 'Local cleanup/procedural geometry suits this mechanical/simple asset; no paid fallback'
        if request.get('source_images') or request['asset_type'] in ('organic', 'humanoid', 'hero'):
            return 'meshy', 'Consider a generated organic/reference-driven shape; paid plan only until approved'
        return 'blender', 'Conservative local default; agent must author the generator if absent'
    if operation in ('remesh', 'retexture', 'rig', 'animate'):
        return 'meshy', 'Documented specialized operation; paid approval required'
    if operation == 'edit_image':
        return 'higgsfield', 'Documented reference-image editing; paid plan only'
    if operation in ('generate_image', 'generate_texture'):
        return ('comfyui', 'Use the prepared local image workflow') if request.get('image_request') else ('higgsfield', 'Documented image CLI; paid approval required')
    if operation == 'generate_video':
        return 'higgsfield', 'Video concepts use a separate paid media route, never a runtime game dependency'
    raise ValueError('No selection rule for this operation')

def validate_request(request):
    reject_secrets(request)
    if request.get('schema_version', 1) != 1:
        raise ValueError('Unknown request schema')
    asset_id(request.get('name'))
    if request.get('quality', 'standard') not in registry_quality():
        raise ValueError('Unknown quality profile')
    if request.get('cost_policy', 'local_first') not in ('local_first', 'consider_paid'):
        raise ValueError('Invalid cost policy')
    if request.get('complexity', 'medium') not in ('low', 'medium', 'high'):
        raise ValueError('Invalid complexity')
    views = request.get('reference_views', {})
    if not isinstance(views, dict) or set(views) - {'concept', 'front', 'side', 'rear', 'top'} or any(not isinstance(v, str) for v in views.values()):
        raise ValueError('Invalid reference_views')
    if request.get('operation', 'generate_3d') not in OPERATIONS:
        raise ValueError('Unsupported operation')
    for key in ('prompt', 'asset_type', 'provider', 'method'):
        if key in request and not isinstance(request[key], str):
            raise ValueError('Request strings have invalid types')
    if not isinstance(request.get('source_images', []), list) or any(not isinstance(v, str) for v in request.get('source_images', [])):
        raise ValueError('source_images must be a list of paths/URLs')
    cleanup = request.get('cleanup', {})
    if set(cleanup) - {'longest_side_m', 'origin', 'max_triangles', 'allow_decimate', 'lod_ratio'}:
        raise ValueError('Unsupported cleanup option')
    if cleanup.get('origin', 'center') not in ('center', 'bottom'):
        raise ValueError('Origin must be center or bottom')
    if not 0.01 <= float(cleanup.get('longest_side_m', 2.0)) <= 10000:
        raise ValueError('Invalid target dimensions')
    if type(cleanup.get('max_triangles', 20000)) is not int or cleanup.get('max_triangles', 20000) < 12:
        raise ValueError('Invalid triangle budget')
    if type(cleanup.get('allow_decimate', False)) is not bool or not 0 <= float(cleanup.get('lod_ratio', 0)) < 1:
        raise ValueError('Invalid decimation/LOD policy')

def input_hashes(request):
    files = list(request.get('source_images', []))
    files += list(request.get('reference_views', {}).values())
    files += [request[k] for k in ('source_file', 'image_request') if request.get(k)]
    if request.get('image_request'):
        image_spec = read_json(path(request['image_request']))
        files.append(image_spec['workflow'])
        if image_spec.get('source_image'):
            files.append(image_spec['source_image'])
        files.append('tools/providers/image_generation/comfyui.json')
    return {str(path(file).relative_to(ROOT)).replace('\\', '/'): file_hash(path(file)) for file in files if not file.startswith('https://')}

def registry_quality():
    return read_json(path('tools/providers/quality_profiles.json'))


def prepare(request):
    request = {'schema_version': 1, 'asset_type': 'prop', 'operation': 'generate_3d', 'method': 'auto', 'quality': 'standard', **request}
    validate_request(request)
    profile = registry_quality()[request['quality']]
    request['cleanup'] = {'max_triangles': profile['max_triangles'], 'lod_ratio': profile['lod_ratio'], **request.get('cleanup', {})}
    if request['quality'] == 'hero' and not request['cleanup']['lod_ratio']:
        raise ValueError('Hero cleanup requires LOD preparation')
    if request.get('reference_views') and not request.get('source_images'):
        request['source_images'] = [request['reference_views'][view] for view in ('front', 'side', 'rear', 'top') if view in request['reference_views']]
    chosen, reason = select_provider(request)
    info = registry()['providers'].get(chosen)
    if info is None or request['operation'] not in info['operations']:
        raise ValueError('Selected provider does not advertise this operation')
    built = adapter(chosen).build(request)
    job_id = uuid.uuid4().hex
    plan = {'schema_version': 1, 'job_id': job_id, 'created': now(),
            'expires': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            'provider': chosen, 'operation': request['operation'], 'selection_reason': reason,
            'paid': info['paid'], 'cost': built.pop('cost'), 'request': built, 'asset': request,
            'input_sha256': input_hashes(request), 'quality_profile': profile,
            'availability': adapter(chosen).configured() if hasattr(adapter(chosen), 'configured') else {'local_tool_resolution': 'at execution'},
            'workflow_stages': ['design', 'concept/references if required', 'generation', 'Blender cleanup/material checks', 'collision/LOD', 'Godot import/validation', 'preview/review', 'provenance'],
            'automatic_followup_paid_tasks': False}
    plan['local_alternative'] = 'Authored procedural Blender or local ComfyUI; never automatic paid fallback'
    plan['external_recommendation_reason'] = request.get('external_reason', 'No external quality recommendation established; explicit provider selection still requires review') if info['paid'] else None
    plan['output_destination'] = 'generated/raw/' + job_id if info['paid'] else 'generated/image-jobs/' if chosen == 'comfyui' else request['name']
    directory = path('generated/provider-jobs/' + job_id)
    write_json(directory / 'plan.json', plan)
    write_json(directory / 'state.json', {'status': 'PLANNED', 'paid_requests_submitted': 0})
    return directory, plan

def load_plan(job):
    directory = path(job)
    if not directory.is_relative_to(path('generated/provider-jobs')):
        raise ValueError('Job must be under generated/provider-jobs')
    plan = read_json(directory / 'plan.json')
    if directory.name != plan['job_id']:
        raise ValueError('Job ID/path mismatch')
    reject_secrets(plan)
    return directory, plan

def check_inputs(plan):
    for file, expected in plan['input_sha256'].items():
        if file_hash(path(file)) != expected:
            raise ValueError('Source input changed since planning; create a new reviewed plan')

def ensure_new_asset(name):
    for file in (f'game/assets/models/{name}.glb', f'blender/projects/{name}.blend', f'tools/assets/{name}.json', f'docs/assets/{name}.md', f'generated/manifests/{name}.json'):
        if path(file).exists():
            raise ValueError('Preserving existing asset; use a new asset name for imported versions: ' + name)

def studio(action, name, capture=False):
    executable = shutil.which('pwsh')
    if not executable:
        raise ValueError('PowerShell 7 (pwsh) is required')
    command = [executable, '-NoProfile', '-File', str(path('tools/pipeline.ps1')), action, '-Asset', name]
    if capture:
        command.append('-Capture')
    output = run(command, timeout=600)
    if 'PIPELINE_PASS:' not in output:
        raise RuntimeError('Studio action lacked its completion marker')
    return output

def glb_summary(file):
    data = Path(file).read_bytes()
    if data[:4] != b'glTF' or struct.unpack_from('<II', data, 4) != (2, len(data)):
        raise ValueError('Invalid GLB container')
    chunk_length, chunk_type = struct.unpack_from('<II', data, 12)
    if chunk_type != 0x4E4F534A:
        raise ValueError('Missing GLB JSON chunk')
    doc = json.loads(data[20:20 + chunk_length])
    triangles = 0
    for node in doc.get('nodes', []):
        if 'mesh' not in node or node.get('name', '').endswith(('-colonly', '-convcolonly')):
            continue
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            if primitive.get('mode', 4) == 4:
                accessor = primitive.get('indices', primitive['attributes']['POSITION'])
                triangles += doc['accessors'][accessor]['count'] // 3
    textures = []
    for material in doc.get('materials', []):
        pbr = material.get('pbrMetallicRoughness', {})
        slots = {k: v for k, v in {**pbr, **material}.items() if k.endswith('Texture')}
        textures.append({'material': material.get('name', ''), 'slots': slots})
    return {'polygon_count': triangles, 'polygon_count_unit': 'triangles excluding collision', 'textures': textures}

def manifest(plan, original, processed=None, audit=None, status='PENDING'):
    name = plan['asset']['name']
    result = {'schema_version': 1, 'asset_name': name, 'asset_type': plan['asset']['asset_type'], 'provider': plan['provider'],
              'generation_method': plan['request']['method'], 'source_prompt': plan['asset'].get('prompt', ''),
              'source_images': sanitized(plan['asset'].get('source_images', [])), 'generation_date': now(),
              'original_file': str(original.relative_to(ROOT)).replace('\\', '/'),
              'original_sha256': file_hash(original), 'processed_file': None, 'polygon_count': None, 'textures': [],
              'scale': None, 'collision_status': 'NOT_CHECKED', 'Godot_import_status': status,
              'license_provenance_notes': plan['asset'].get('provenance', 'Original requested design; verify provider/account output rights before distribution.'),
              'provider_job': plan['job_id']}
    result.update(asset_id=name, quality_tier=plan['asset'].get('quality', 'standard'),
                  provider_model=plan['request'].get('model', plan['request'].get('body', {}).get('ai_model')),
                  processed_blender_file=None, final_glb=None, lods=[], Godot_scene=None,
                  validation={'status': status}, preview=None, preview_review='PENDING_AGENT_REVIEW',
                  reference_views=sanitized(plan['asset'].get('reference_views', {})),
                  cost={'estimate': plan['cost'], 'reported_credits': None})
    state_file = path('generated/provider-jobs/' + plan['job_id'] + '/state.json')
    if state_file.exists():
        result['cost']['reported_credits'] = read_json(state_file).get('consumed_credits')
    # Preserve local references independently of their mutable source paths.
    preserved = []
    for index, value in enumerate(dict.fromkeys(list(plan['asset'].get('source_images', [])) + list(plan['asset'].get('reference_views', {}).values()))):
        if value.startswith('https://'):
            suffix = Path(urlparse(value).path).suffix.lower()
            if suffix not in ('.png', '.jpg', '.jpeg'):
                raise ValueError('Reference archival requires a PNG/JPEG URL or a local file')
            dest = path(f'generated/references/{name}/{index:02d}{suffix}')
            download(value, dest)
            preserved.append({'source': sanitized(value), 'path': dest.relative_to(ROOT).as_posix(), 'sha256': file_hash(dest)})
        else:
            src = path(value)
            dest = path(f'generated/references/{name}/{index:02d}{src.suffix.lower()}')
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            preserved.append({'source': value, 'path': dest.relative_to(ROOT).as_posix(), 'sha256': file_hash(dest)})
    result['reference_images'] = preserved
    if processed:
        result.update(processed_file=str(processed.relative_to(ROOT)).replace('\\', '/'), processed_sha256=file_hash(processed))
        result.update(glb_summary(processed))
        result.update(final_glb=processed.relative_to(ROOT).as_posix(), processed_blender_file=f'blender/projects/{name}.blend', Godot_scene=f'game/scenes/assets/{name}.tscn')
    if audit:
        result.update(scale=audit.get('normalization'), collision_status=audit.get('collision_status'), cleanup_audit=audit)
        if audit.get('lod_file'):
            result['lods'] = [f'game/assets/models/{audit["lod_file"]}']
    if not plan['paid']:
        result['cost']['reported_credits'] = 0
    write_json(path('generated/manifests/' + name + '.json'), result)
    return result

def process_model(plan, source, repair=False):
    name = plan['asset']['name']
    if repair:
        prior = read_json(path(f'generated/manifests/{name}.json'))
        if prior['provider'] != plan['provider'] or path(prior['original_file']) != source.resolve():
            raise ValueError('Repair must match the recorded provider and original source path')
        backup = path('generated/processed/' + name + '/history/' + uuid.uuid4().hex)
        backup.mkdir(parents=True)
        write_json(backup / 'manifest.json', prior)
        for previous in (prior.get('final_glb'), prior.get('processed_blender_file')):
            if previous and path(previous).is_file():
                shutil.copyfile(path(previous), backup / Path(previous).name)
    else:
        ensure_new_asset(name)
    stage = path('generated/processed/' + name)
    stage.mkdir(parents=True, exist_ok=True)
    config = {'name': name, 'source': str(source), 'output_dir': str(stage), **plan['asset'].get('cleanup', {})}
    config_path = stage / 'cleanup.json'
    write_json(config_path, config)
    blender = shutil.which('blender') or 'C:/Program Files/Blender Foundation/Blender 5.0/blender.exe'
    output = run([blender, '--background', '--factory-startup', '--python-exit-code', '1', '--python', str(path('blender/scripts/process_external_asset.py')), '--', '--config', str(config_path)], timeout=300)
    (stage / 'blender-cleanup.log').write_text(output, encoding='utf-8')
    if 'PIPELINE_CLEANUP_PASS' not in output:
        raise RuntimeError('Blender cleanup lacked completion marker')
    audit = read_json(stage / 'audit.json')
    clean = stage / (name + '.glb')
    summary = glb_summary(clean)
    if source.suffix.lower() == '.glb':
        before = glb_summary(source)
        expected = {m['material']: set(m['slots']) for m in before['textures']}
        actual = {m['material']: set(m['slots']) for m in summary['textures']}
        if any(not slots.issubset(actual.get(name, set())) for name, slots in expected.items()):
            raise ValueError('PBR texture slots lost during cleanup; refusing promotion')
    max_materials = plan.get('quality_profile', registry_quality()['standard'])['max_materials']
    if audit['material_count'] > max_materials:
        raise ValueError('Material budget exceeded; consolidate deliberately')
    runtime = path(f'game/assets/models/{name}.glb')
    shutil.copyfile(clean, runtime)
    shutil.copyfile(stage / (name + '.blend'), path(f'blender/projects/{name}.blend'))
    if audit.get('lod_file'):
        shutil.copyfile(stage / audit['lod_file'], path('game/assets/models/' + audit['lod_file']))
    # Generated source manifest supports existing integrate/test/preview commands.
    write_json(path(f'tools/assets/{name}.json'), {'schema_version': 1, 'id': name, 'status': 'ready',
        'generation_method': 'external_import', 'specification': f'docs/assets/{name}.md', 'generator': f'blender/scripts/generate_{name}.py',
        'blend': f'blender/projects/{name}.blend', 'model': f'game/assets/models/{name}.glb', 'scene': f'game/scenes/assets/{name}.tscn',
        'uv_mode': 'required' if audit['textured'] else 'none', 'require_collision': True,
        'max_triangles': config.get('max_triangles', 20000), 'max_materials': max_materials, 'required_nodes': [], 'emissive_nodes': [],
        'required_texture_slots': {m['material']: list(m['slots']) for m in summary['textures']}})
    path(f'docs/assets/{name}.md').write_text('# ' + name + '\n\nImported provider asset. See generated/manifests/' + name + '.json for provenance and cleanup audit.\n\n' + plan['asset'].get('prompt', '') + '\n', encoding='utf-8')
    record = manifest(plan, source, runtime, audit, 'PENDING_VALIDATION')
    try:
        output = studio('integrate', name) + studio('preview', name)
        (stage / 'godot-validation.log').write_text(output, encoding='utf-8')
        record['Godot_import_status'] = 'PASS'
        record['preview'] = f'generated/previews/{name}.png'
        record['validation'] = {'status': 'PASS', 'pbr_slots': 'PRESERVED', 'Godot': 'PASS', 'log': stage.relative_to(ROOT).as_posix() + '/godot-validation.log'}
    except Exception:
        record['Godot_import_status'] = 'FAIL_REQUIRES_FIX'
        raise
    finally:
        write_json(path(f'generated/manifests/{name}.json'), record)
    return record

def execute(job, receipt=None):
    directory, plan = load_plan(job)
    if datetime.fromisoformat(plan['expires']) <= datetime.now(timezone.utc):
        raise ValueError('Plan expired; recheck current docs/pricing and prepare again')
    check_inputs(plan)
    if str(plan['asset'].get('review_status','')).startswith('REJECTED'):
        raise ValueError('Asset review rejected these inputs; replace/review references and prepare a new plan')
    module = adapter(plan['provider'])
    if plan['paid']:
        if not receipt:
            raise ValueError('Paid generation blocked: show this plan and obtain explicit user approval first')
        if plan['provider'] == 'meshy':
            module.headers()  # Presence check before consuming approval, never printed.
        else:
            module.executable()
        approval = consume_approval(plan, receipt, directory)
        state = {'status': 'SUBMITTING', 'paid_requests_submitted': 1, 'approval': sanitized(approval)}
        write_json(directory / 'state.json', state)
        try:
            state['task_id'] = module.submit(plan)
            state['status'] = 'SUBMITTED'
        except Exception:
            state['status'] = 'SUBMISSION_FAILED_OR_UNKNOWN_DO_NOT_RETRY'
            raise
        finally:
            write_json(directory / 'state.json', state)
        return state
    if plan['provider'] == 'blender':
        if plan['request']['method'] == 'procedural':
            if not plan['request'].get('generator_ready', True):
                raise ValueError('Plan requires agent-authored Blender generator; scaffold/implement then replan')
            output = studio('test-pipeline', plan['asset']['name'])
            (directory / 'local.log').write_text(output, encoding='utf-8')
            model = path(f"game/assets/models/{plan['asset']['name']}.glb")
            result = manifest(plan, model, model, status='PASS')
            result['collision_status'] = 'PASS_GODOT_VALIDATOR'
            result['scale'] = {'units': 'meters', 'source': 'authored procedural generator'}
            profile = plan.get('quality_profile', registry_quality()['standard'])
            if result['polygon_count'] > profile['max_triangles'] or len(result['textures']) > profile['max_materials']:
                raise ValueError('Procedural output exceeds selected quality profile budgets')
            result['preview'] = f"generated/previews/{plan['asset']['name']}.png"
            result['validation'] = {'status': 'PASS', 'log': directory.relative_to(ROOT).as_posix() + '/local.log'}
            result['lods'] = ['Godot automatic mesh LOD import; inspect imported geometry and distances for this asset']
            result['cost']['reported_credits'] = 0
            write_json(path(f"generated/manifests/{plan['asset']['name']}.json"), result)
        else:
            result = process_model(plan, path(plan['asset']['source_file']))
    elif plan['provider'] == 'comfyui':
        # Reload/verify workflow before local dispatch; prevents newly introduced paid nodes.
        module.build(plan['asset'])
        result = module.execute(plan, directory)
    else:
        raise ValueError('Unimplemented local executor')
    write_json(directory / 'state.json', {'status': 'LOCAL_COMPLETE', 'paid_requests_submitted': 0, 'result': result})
    return result

def poll(job, wait_seconds=0):
    directory, plan = load_plan(job)
    state = read_json(directory / 'state.json')
    if not state.get('task_id'):
        raise ValueError('No recorded provider task ID; do not submit a second paid job')
    deadline = time.monotonic() + wait_seconds
    while True:
        response = adapter(plan['provider']).status(plan, state['task_id'])
        state['provider_response'] = sanitized(response)
        state['status'] = str(response.get('status', 'UNKNOWN')).upper()
        state['consumed_credits'] = response.get('consumed_credits')
        write_json(directory / 'state.json', state)
        if state['status'] in ('SUCCEEDED', 'COMPLETED', 'FAILED', 'CANCELED', 'CANCELLED', 'NSFW') or time.monotonic() >= deadline:
            return response
        time.sleep(min(3, max(0, deadline - time.monotonic())))

def artifact_urls(response, extension):
    found = []
    def visit(value):
        if isinstance(value, dict):
            for item in value.values(): visit(item)
        elif isinstance(value, list):
            for item in value: visit(item)
        elif isinstance(value, str) and value.startswith('https://') and urlparse(value).path.lower().endswith(extension):
            if value not in found: found.append(value)
    visit(response)
    return found

def fetch(job):
    directory, plan = load_plan(job)
    response = poll(job)
    if str(response.get('status', '')).upper() not in ('SUCCEEDED', 'COMPLETED'):
        raise ValueError('Provider task is not complete')
    operation = plan['operation']
    suffixes = ('.mp4', '.webm') if operation == 'generate_video' else ('.png', '.jpg', '.jpeg', '.webp') if operation in ('generate_image', 'edit_image', 'generate_texture') else ('.glb',)
    urls = [url for suffix in suffixes for url in artifact_urls(response, suffix)]
    if not urls:
        raise ValueError('No recognized artifact URL; review the documented response schema before promotion')
    raw = path('generated/raw/' + plan['job_id'])
    files = []
    for index, url in enumerate(urls):
        destination = raw / (str(index) + Path(urlparse(url).path).suffix.lower())
        files.append(download(url, destination))
    if suffixes == ('.glb',) and operation not in ('rig', 'animate'):
        if len(files) != 1:
            raise ValueError('Multiple GLBs require deliberate selection before cleanup')
        return process_model(plan, files[0])
    record = manifest(plan, files[0], status='NOT_RUNTIME_MEDIA' if suffixes != ('.glb',) else 'RIGGED_MODEL_REQUIRES_SPECIALIZED_REVIEW')
    record['media_files'] = [str(file.relative_to(ROOT)).replace('\\', '/') for file in files]
    write_json(path(f"generated/manifests/{plan['asset']['name']}.json"), record)
    return record
