"""Deterministic bounded corridor composer; preserves the accepted block and assets."""
import argparse
import copy
import json
from pathlib import Path
import random
import re

ROOT = Path(__file__).resolve().parents[2]
TEMPLATES = {
    'main_street': [(-16,-17,'foundry_building'),(16,-17,'market_building'),(-16,17,'relay_building'),(16,17,'foundry_building')],
    'industrial_service': [(-17,-18,'foundry_building'),(15,19,'foundry_building')],
    'alley_backside': [(-17,-18,'foundry_building'),(15,-18,'relay_building'),(-8,20,'market_building')],
    'plaza_open': [(0,20,'relay_building')],
}

def compose(spec):
    if not re.fullmatch('[a-z][a-z0-9_]{0,40}',spec['district_id']): raise ValueError('Unsafe district ID')
    if spec['cell_size'] != 64 or spec['road_width'] != 8: raise ValueError('Current corridor kit requires 64 m cells and 8 m road')
    if not 1 <= len(spec['blocks']) <= 3: raise ValueError('Three-block limit')
    ids=[b['id'] for b in spec['blocks']]
    if len(set(ids)) != len(ids) or not set(ids)<= {'west','center','east'}: raise ValueError('Invalid cell IDs')
    source=json.loads((ROOT/'game/world/city_block.json').read_text())
    result={k:copy.deepcopy(v) for k,v in source.items() if k not in ('cells',)}
    result.update(id=spec['district_id'],seed=spec['seed'],scene_directory='res://scenes/district',cells=[])
    result['max_loaded']=min(3,spec['budgets']['max_loaded_cells'])
    for block in spec['blocks']:
        if block['archetype'] not in TEMPLATES: raise ValueError('Unknown block archetype')
        rng=random.Random(spec['seed']*65537+block['seed'])
        cell={'id':block['id'],'x':{'west':-64,'center':0,'east':64}[block['id']], 'role':block['archetype'],'seed':block['seed'],'buildings':[],'lots':[],
              'road_sockets':[[-32,0,0],[32,0,0]],'hooks':{'mission_location':block['id']+'_service','npc_spawn':[0,.3,6],'vehicle_spawn':[0,.3,0],'objective_area':[0,0,0]}}
        for index,(x,z,asset) in enumerate(TEMPLATES[block['archetype']]):
            if block['id'] != 'center': x += rng.choice([-1,0,1])*2
            recipe=json.loads((ROOT/f'tools/world/{asset}.json').read_text())
            width,depth=recipe['footprint']
            b={'id':block['id']+'_'+str(index),'asset':asset,'position':[x,0,z],'yaw':180 if z<0 else 0,'front_offset':depth/2+.28}
            cell['buildings'].append(b)
            cell['lots'].append({'lot_id':b['id'],'position':b['position'],'rotation':b['yaw'],'width':width+4,'depth':depth+4,'street_frontage':True,'corner_lot':False,'building_type':recipe['archetype'],'setback':abs(z)-depth/2-4,'service_access':True,'entrance_side':'street','height_limit':recipe['floors']*3.2+4,'entrance_kind':'DECORATIVE_ENTRANCE'})
        if block['id']=='center':
            cell['buildings']=copy.deepcopy(source['cells'][1]['buildings'])
            for lot,b in zip(cell['lots'],cell['buildings']):lot['lot_id']=b['id']
        cell['props']=[];cell['decals']=[]
        if block['archetype']=='industrial_service':
            cell['props']=[
                {'id':'loading_pad','position':[13,.08,-20],'size':[20,.16,18],'collision':False},
                {'id':'power_unit','position':[14,2,-23],'size':[4,4,3],'collision':True},
                {'id':'vent_cap','position':[14,4.2,-23],'size':[4.4,.4,3.4],'collision':False},
                {'id':'service_crate_a','position':[8,.8,-13],'size':[1.6,1.6,1.4],'collision':True},
                {'id':'service_crate_b','position':[10,.8,-14],'size':[1.6,1.6,1.4],'collision':True},
                {'id':'utility_riser_a','position':[21,3,-23],'size':[.5,6,.5],'collision':True},
                {'id':'utility_riser_b','position':[24,3,-23],'size':[.5,6,.5],'collision':True},
                {'id':'utility_bridge','position':[22.5,6,-23],'size':[3.5,.5,.5],'collision':False}]
            cell['decals']=[{'id':'warning','position':[9,.18,-13.5],'size':[6,.35,4]}, {'id':'repair','position':[15,.18,-18],'size':[5,.35,3]}]
        result['cells'].append(cell)
    validate(result,spec['budgets']['max_buildings'])
    return result

def validate(plan,budget):
    if sum(len(c['buildings']) for c in plan['cells'])>budget:raise ValueError('Building budget exceeded')
    for c in plan['cells']:
        rectangles=[]
        for lot in c['lots']:
            x,_,z=lot['position'];w,d=lot['width'],lot['depth']
            if abs(x)+w/2>32 or abs(z)+d/2>32 or abs(z)-d/2<8:raise ValueError('Lot overlaps boundary or pedestrian corridor')
            for px,pz,pw,pd in rectangles:
                if abs(x-px)<(w+pw)/2 and abs(z-pz)<(d+pd)/2:raise ValueError('Overlapping lots')
            rectangles.append((x,z,w,d))

def write(spec):
    plan=compose(spec)
    folder=ROOT/'game/scenes/district';folder.mkdir(parents=True,exist_ok=True)
    (ROOT/'game/world/district.json').write_text(json.dumps(plan,indent=2)+'\n')
    for c in plan['cells']:
        assets=sorted({b['asset'] for b in c['buildings']})
        lines=[f'[gd_scene load_steps={len(assets)+2} format=3]', '[ext_resource type="Script" path="res://scripts/city_chunk.gd" id="1"]']
        lines += [f'[ext_resource type="PackedScene" path="res://scenes/assets/{a}.tscn" id="{i+2}"]' for i,a in enumerate(assets)]
        lines += [f'[node name="DistrictCell" type="Node3D"]','script = ExtResource("1")',f'cell_id = "{c["id"]}"','spec_path = "res://world/district.json"','building_scenes = Array[PackedScene](['+', '.join(f'ExtResource("{i+2}")' for i in range(len(assets)))+'])']
        (folder/f'cell_{c["id"]}.tscn').write_text('\n'.join(lines)+'\n')
    print('DISTRICT_GENERATION_PASS:',len(plan['cells']),'cells')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--spec',default=str(ROOT/'tools/world/district_spec.json'));args=parser.parse_args()
    write(json.loads(Path(args.spec).read_text()))
