"""Canonical source consistency gate; visual claims require an explicit review."""
import argparse
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def evaluate(package,review=None):
    errors=[]
    views=package['views']
    if len(views)<4: errors.append('Insufficient views')
    if package.get('marking_audit')!='NO_FONT_OR_IMAGE_NODES': errors.append('Unreviewed markings or image textures')
    source=ROOT/package['source']
    if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=package['source_sha256']:
        errors.append('Canonical source changed')
    for name,v in views.items():
        file=(ROOT/v['file']).resolve()
        if not file.is_relative_to(ROOT) or not file.is_file(): errors.append('Missing/unsafe '+name); continue
        if hashlib.sha256(file.read_bytes()).hexdigest()!=v['sha256']: errors.append('Changed image '+name)
        if v['geometry_sha256']!=package['geometry_sha256']: errors.append('Contradictory geometry '+name)
    if errors: return {'status':'REJECT','reasons':errors}
    required={'silhouette','proportions','components','placement','palette','markings','viewpoints'}
    if not review or set(review.get('checks',{}))!=required:
        return {'status':'NEEDS_REGENERATION','reasons':['Needs explicit complete visual review; do not regenerate blindly']}
    if review.get('geometry_sha256')!=package['geometry_sha256'] or set(review.get('views',[]))!=set(views):
        return {'status':'REJECT','reasons':['Review does not match this canonical set']}
    if not all(v=='PASS' for v in review['checks'].values()):
        return {'status':'REJECT','reasons':['Visual invariant failed']}
    return {'status':'PASS','reasons':['Shared canonical geometry/camera metadata, hashes and explicit visual review passed']}

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('package'); parser.add_argument('--review'); args=parser.parse_args()
    package=json.loads((ROOT/args.package).read_text()); review=json.loads((ROOT/args.review).read_text()) if args.review else None
    result=evaluate(package,review); print(json.dumps(result)); raise SystemExit(result['status']!='PASS')
