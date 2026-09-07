import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from generate_building import build, validate, ROOT
spec=json.loads((ROOT/'tools/world/foundry_building.json').read_text())
spec['id']='unit_building_recipe'
def run():
    build(spec)
    return json.loads((ROOT/f"generated/manifests/{spec['id']}_recipe.json").read_text())
a=run(); b=run()
assert a['recipe_sha256']==b['recipe_sha256']
assert len([p for p in b['placements'] if p['name']=='Entrance_Glass'])==1
assert next(p for p in b['placements'] if p['name']=='Entrance_Glass')['position'][0]==0
spec['seed']+=1
c=run(); assert b['recipe_sha256']!=c['recipe_sha256']
spec['quality']='DISTANT'; d=run(); assert len(d['placements'])<len(b['placements'])/4
for key,value in [('id','../unsafe'),('floors',100),('archetype','unknown')]:
    bad={**spec,key:value}
    try: validate(bad)
    except ValueError: pass
    else: raise AssertionError('Invalid specification accepted')
print('BUILDING_RECIPE_TESTS_PASS: 8 checks')
