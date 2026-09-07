"""Deterministic modular building recipe. Original geometry, shared materials."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
import bpy

ROOT=Path(__file__).resolve().parents[2]

def validate(spec):
    import re
    if not re.fullmatch('[a-z][a-z0-9_]{0,50}',spec['id']): raise ValueError('Unsafe building ID')
    if spec['archetype'] not in ('residential','commercial','industrial','office','civic','spaceport','warehouse','utility'): raise ValueError('Unsupported archetype')
    if not 1<=spec['floors']<=12: raise ValueError('Floor budget')
    if any(not 6<=v<=40 for v in spec['footprint']): raise ValueError('Footprint budget')
    if spec['quality'] not in ('HERO','NEAR','STANDARD','BACKGROUND','DISTANT'): raise ValueError('Quality class')

def build(spec):
    validate(spec)
    rng=random.Random(spec['seed'])
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    for mesh in list(bpy.data.meshes):
        if mesh.users==0: bpy.data.meshes.remove(mesh)
    for mat in list(bpy.data.materials):
        if mat.users==0: bpy.data.materials.remove(mat)
    bpy.context.preferences.filepaths.save_version=0
    bpy.context.scene.unit_settings.system='METRIC'
    def material(name,color,metal=.0,rough=.6,emission=0):
        m=bpy.data.materials.new(name); m.use_nodes=True
        p=m.node_tree.nodes.get('Principled BSDF')
        p.inputs['Base Color'].default_value=(*color,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
        p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=emission
        return m
    stone=material('Warm_Mineral_Facade',spec.get('facade_color',[.34,.39,.42]))
    steel=material('Charcoal_Trim',(.055,.075,.09),.75,.3)
    glass=material('Blue_Glazing',(.045,.17,.23),.7,.18)
    light=material('Warm_Window_Light',(.95,.59,.23),0,.35,1.3)
    cyan=material('Cyan_Wayfinding',(.02,.5,.63),.2,.35,2)
    ground=material('Foundation',(.17,.19,.20),0,.9)
    placements=[]
    def box(name,loc,dim,mat,bevel=0):
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
        o=bpy.context.object; o.name=name; o.dimensions=dim
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        o.data.materials.append(mat)
        if bevel:
            modifier=o.modifiers.new('EdgeHighlights','BEVEL'); modifier.width=bevel; modifier.segments=1
        placements.append({'name':name,'position':loc,'dimensions':dim,'material':mat.name})
        return o
    w,d=spec['footprint']; floors=spec['floors']; story=3.2; h=floors*story
    box('Foundation',(0,0,.2),(w+.5,d+.5,.4),ground,.06)
    box('Structural_Shell',(0,0,h/2+.4),(w,d,h),stone,.04)
    detailed=spec['quality'] in ('HERO','NEAR','STANDARD')
    if detailed:
        for floor in range(floors):
            z=.4+floor*story
            box(f'Floor_Ledge_{floor}',(0,0,z+.18),(w+.18,d+.18,.16),steel,.025)
            for facade,length,depth in [('front',w,d),('rear',w,d),('left',d,w),('right',d,w)]:
                bay_width={'industrial':3.0,'residential':2.5,'commercial':3.4,'office':2.1,'civic':4.0,'spaceport':4.0,'warehouse':5.0,'utility':3.0}[spec['archetype']]
                bays=max(3,int(length/bay_width))
                if bays%2==0: bays-=1
                bay=length/bays
                for b in range(bays):
                    horizontal=-length/2+(b+.5)*bay
                    # Entrance replaces a ground-floor front bay, preserving structure.
                    entrance=facade=='front' and floor==0 and b==bays//2
                    width=bay*.68; height=2.45 if entrance else 1.75
                    position=(horizontal,depth/2+.04,z+1.5) if facade=='front' else (horizontal,-depth/2-.04,z+1.5) if facade=='rear' else (-depth/2-.04,horizontal,z+1.5) if facade=='left' else (depth/2+.04,horizontal,z+1.5)
                    dim=(width,.16,height) if facade in ('front','rear') else (.16,width,height)
                    box(f'{facade}_{floor}_{b}_Frame',position,tuple(v+.10 if v>.2 else v for v in dim),steel,.025)
                    outward=(0,.095,0) if facade=='front' else (0,-.095,0) if facade=='rear' else (-.095,0,0) if facade=='left' else (.095,0,0)
                    inset=tuple(position[i]+outward[i] for i in range(3))
                    inset_dim=(width-.1,.035,height-.12) if facade in ('front','rear') else (.035,width-.1,height-.12)
                    box('Entrance_Glass' if entrance else f'{facade}_{floor}_{b}_Window',inset,inset_dim,light if rng.random()<.16 and not entrance else glass)
                    if entrance:
                        box('Entrance_Canopy',(horizontal,d/2+.65,3.02),(bay*1.25,1.5,.18),steel,.04)
                        box('Entrance_Light',(horizontal,d/2+.71,2.89),(bay,.9,.035),cyan)
        for x in (-w/2+.14,w/2-.14):
            for y in (-d/2+.14,d/2-.14): box('Corner_Column',(x,y,h/2+.4),(.4,.4,h),steel,.04)
        box('Roof_Parapet',(0,0,h+.53),(w+.3,d+.3,.28),steel,.04)
        box('Roof_Deck',(0,0,h+.71),(w-.5,d-.5,.1),ground)
        for i in range(2 if spec['archetype'] in ('industrial','warehouse','spaceport') else 1):
            x=(-.2+i*.4)*w
            box('HVAC_Base',(x,0,h+1.15),(2.4,1.9,.85),steel,.08)
            for slat in range(6): box('HVAC_Louver',(x-1+slat*.4,0,h+1.60),(.16,1.6,.08),stone)
        box('Service_Panel',(-w*.35,d/2+.12,1.1),(.7,.16,1.1),steel,.02)
        box('Sign_Mount',(0,d/2+.15,3.6),(w*.5,.2,.5),cyan,.02)
    else:
        box('Skyline_Cap',(0,0,h+.55),(w+.1,d+.1,.3),steel)
    collision=box('Building-colonly',(0,0,h/2+.2),(w,d,h+.4),ground); collision.hide_render=True
    blend=ROOT/f"blender/projects/{spec['id']}.blend"; blend.parent.mkdir(parents=True,exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    report={'schema_version':1,'spec':spec,'placements':placements,'recipe_sha256':hashlib.sha256(json.dumps(placements,sort_keys=True).encode()).hexdigest(),
            'source':'original modular generator','navigation_hooks':{'front_entrance':[0,d/2+1,0]},
            'material_policy':'shared authored PBR; no per-building 4K textures',
            'lod_policy':'Godot automatic mesh LOD plus cheap DISTANT recipe; assembled HLOD requires city visibility integration'}
    output=ROOT/f"generated/manifests/{spec['id']}_recipe.json"; output.parent.mkdir(parents=True,exist_ok=True); output.write_text(json.dumps(report,indent=2))
    print('PIPELINE_BLENDER_PASS: '+str(blend))

if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--spec',required=True); args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    build(json.loads((ROOT/args.spec).read_text()))
