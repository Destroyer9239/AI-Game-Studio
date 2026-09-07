"""Render canonical Blender geometry from eight deterministic camera poses."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--spec',required=True)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
spec=json.loads((ROOT/args.spec).read_text())
source=(ROOT/spec['source_blend']).resolve()
if not source.is_relative_to(ROOT): raise ValueError('Source escapes project')
bpy.ops.wm.open_mainfile(filepath=str(source))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH' and not o.name.endswith(('-colonly','-convcolonly'))]
for o in bpy.context.scene.objects:
    if o.name.endswith(('-colonly','-convcolonly')): o.hide_render=True
names={o.name for o in objects}
missing=set(spec['invariants']['required_nodes'])-names
if missing: raise ValueError('Missing invariant components: '+str(sorted(missing)))
if any(o.type=='FONT' for o in bpy.context.scene.objects):
    raise ValueError('Unreviewed text geometry: reference gate rejects markings')
if any(n.type=='TEX_IMAGE' for m in bpy.data.materials if m.use_nodes for n in m.node_tree.nodes):
    raise ValueError('Textured canonical asset requires a separate reviewed marking audit')
corners=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
low=Vector(tuple(min(v[i] for v in corners) for i in range(3)))
high=Vector(tuple(max(v[i] for v in corners) for i in range(3)))
center=(high+low)*.5
dimensions=high-low
for i,(minimum,maximum) in enumerate(spec['invariants']['dimension_ranges_m']):
    if not minimum<=dimensions[i]<=maximum: raise ValueError('Canonical dimensions outside design bounds')
geometry=[{'name':o.name,'vertices':[list(v.co) for v in o.data.vertices],
           'matrix':[list(row) for row in o.matrix_world],
           'materials':[m.name for m in o.data.materials]} for o in sorted(objects,key=lambda x:x.name)]
geometry_hash=hashlib.sha256(json.dumps(geometry,sort_keys=True).encode()).hexdigest()
scene=bpy.context.scene
scene.render.engine='CYCLES'
scene.cycles.samples=16
scene.cycles.use_denoising=True
scene.render.resolution_x=640
scene.render.resolution_y=640
scene.render.resolution_percentage=100
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.20,.27,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
for location,power,size in [((8,6,10),1800,7),((-8,2,5),1300,6),((0,-8,6),1600,5)]:
    light=bpy.data.lights.new('ReferenceStudioLight','AREA'); light.energy=power; light.shape='DISK'; light.size=size
    obj=bpy.data.objects.new(light.name,light); scene.collection.objects.link(obj); obj.location=center+Vector(location)
    obj.rotation_euler=(center-obj.location).to_track_quat('-Z','Y').to_euler()
camera_data=bpy.data.cameras.new('CanonicalCamera'); camera_data.type='ORTHO'; camera_data.ortho_scale=dimensions.length*1.12
camera=bpy.data.objects.new('CanonicalCamera',camera_data); scene.collection.objects.link(camera); scene.camera=camera
directions={'front':(0,1,0),'left':(-1,0,0),'right':(1,0,0),'rear':(0,-1,0),
            'top':(0,0,1),'bottom':(0,0,-1),'front_three_quarter':(1,1,.65),'rear_three_quarter':(-1,-1,.65)}
destination=ROOT/'generated/references'/spec['id']; destination.mkdir(parents=True,exist_ok=True)
views={}
for name,direction in directions.items():
    camera.location=center+Vector(direction).normalized()*dimensions.length*2
    camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    output=destination/(name+'.png'); scene.render.filepath=str(output)
    bpy.ops.render.render(write_still=True)
    views[name]={'file':output.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
                 'camera_direction':direction,'projection':'orthographic','geometry_sha256':geometry_hash}
package={'schema_version':1,'id':spec['id'],'source':spec['source_blend'],
         'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
         'geometry_sha256':geometry_hash,'dimensions_m':list(dimensions),'component_names':sorted(names),
         'invariants':spec['invariants'],'views':views,'marking_audit':'NO_FONT_OR_IMAGE_NODES',
         'status':'NEEDS_REGENERATION','reason':'Structural checks passed; explicit visual review still required'}
(destination/'package.json').write_text(json.dumps(package,indent=2))
print('MULTIVIEW_RENDER_PASS: '+str(destination))

