"""Explicit real local acceptance: auto-start, inference, retrieval, errors, stop/restart.
Uses existing installed models. No external providers or paid operations.
"""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from tools.imagegen import backend, high_resolution, submit_image

ROOT = backend.ROOT

def main():
    checks=[]
    backend.stop()
    assert backend.status()['status']=='UNAVAILABLE'
    checks.append('cooperative_stop')
    result=high_resolution.run('tools/providers/requests/industrial_concrete_source.json')
    assert result['image_job']['status']=='PASS'
    checks += ['provider_auto_start','local_base_inference','tiled_4k_inference','poll_and_retrieve']
    assert backend.status()['devices'][0]['type']=='cuda'
    checks.append('cuda_backend')
    assert backend.start()['action']=='REUSED_EXISTING_SERVER'
    checks.append('reuse_existing')
    request=json.loads((ROOT/'tools/imagegen/requests/industrial_concrete_source.json').read_text())
    request['checkpoint']='intentionally_missing_test_model.safetensors'
    file=ROOT/'generated/reports/missing_model_request.json'
    file.write_text(json.dumps(request))
    try:
        submit_image.run_job(str(file),execute=True)
    except ValueError as exc:
        assert 'not installed' in str(exc)
        checks.append('missing_model_rejected_before_submit')
    else:
        raise AssertionError('Missing model accepted')
    backend.stop()
    backend.start()
    assert backend.status()['status']=='REACHABLE'
    checks.append('stop_restart')
    backend.stop()
    report={'status':'PASS','checks':checks,'passed':len(checks),'failed':0,
            'external_credits':0,'final_server':'STOPPED','upscale_performance':result['performance']}
    (ROOT/'generated/reports/local_backend_acceptance.json').write_text(json.dumps(report,indent=2))
    print('LOCAL_BACKEND_PASS: '+json.dumps(report))

if __name__=='__main__': main()
