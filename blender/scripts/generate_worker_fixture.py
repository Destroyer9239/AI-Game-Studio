"""Original articulated maintenance robot, proving a local skinned character route."""
from pathlib import Path
import json,math
import bpy
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.context.preferences.filepaths.save_version=0
def material(name,color,metal=0,emission=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=.45
    p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    return m
shell=material('Worker_Amber',(.55,.22,.035),.4)
joint=material('Worker_Graphite',(.04,.06,.08),.7)
visor=material('Worker_Cyan',(.015,.55,.7),.1,1.4)
armature=bpy.data.armatures.new('WorkerSkeleton');rig=bpy.data.objects.new('WorkerRig',armature);bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
definitions=[('root',(0,0,0),(0,0,.2),None),('hips',(0,0,.85),(0,0,1.05),'root'),('spine',(0,0,1.05),(0,0,1.45),'hips'),('head',(0,0,1.45),(0,0,1.85),'spine'),('arm_l',(-.24,0,1.4),(-.62,0,1.25),'spine'),('arm_r',(.24,0,1.4),(.62,0,1.25),'spine'),('leg_l',(-.16,0,.85),(-.16,0,.15),'hips'),('leg_r',(.16,0,.85),(.16,0,.15),'hips')]
for name,head,tail,parent in definitions:
    bone=armature.edit_bones.new(name);bone.head=head;bone.tail=tail
    if parent:bone.parent=armature.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
def part(name,loc,dim,mat,bone):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);obj=bpy.context.object;obj.name=name;obj.dimensions=dim
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat);group=obj.vertex_groups.new(name=bone);group.add(list(range(len(obj.data.vertices))),1,'REPLACE')
    modifier=obj.modifiers.new('PreservedSkin','ARMATURE');modifier.object=rig;obj.parent=rig
    return obj
part('WorkerTorso',(0,0,1.24),(.52,.34,.48),shell,'spine')
part('WorkerPelvis',(0,0,.91),(.4,.3,.22),joint,'hips')
part('WorkerHead',(0,0,1.64),(.34,.32,.36),shell,'head')
part('HeadVisor',(0,.17,1.66),(.28,.035,.11),visor,'head')
for sign,side in [(-1,'l'),(1,'r')]:
    part('Arm_'+side,(sign*.46,0,1.28),(.3,.23,.23),shell,'arm_'+side)
    part('Leg_'+side,(sign*.16,0,.5),(.19,.24,.65),shell,'leg_'+side)
    part('Foot_'+side,(sign*.16,.06,.13),(.22,.38,.15),joint,'leg_'+side)
rig.animation_data_create()
for action_name in ['Idle','Walk']:
    action=bpy.data.actions.new(action_name);action.use_fake_user=True;rig.animation_data.action=action
    for frame in [1,16,31]:
        for name in ['leg_l','leg_r','arm_l','arm_r']:
            bone=rig.pose.bones[name];bone.rotation_mode='XYZ'
            angle=0 if action_name=='Idle' else (.35 if frame!=16 else -.35)*(1 if name.endswith('_l') else -1)
            bone.rotation_euler.x=angle;bone.keyframe_insert(data_path='rotation_euler',frame=frame)
        hips=rig.pose.bones['hips'];hips.location.z=.012 if frame==16 else 0;hips.keyframe_insert(data_path='location',frame=frame)
bpy.context.scene.render.fps=30;bpy.context.scene.frame_start=1;bpy.context.scene.frame_end=31
rig.animation_data.action=bpy.data.actions['Idle'];bpy.context.scene.frame_set(1)
blend=ROOT/'blender/projects/worker_fixture.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
glb=ROOT/'game/assets/models/worker_fixture.glb'
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_apply=False)
report={'id':'worker_fixture','class':'worker technical fixture','height_m':1.82,'bones':[d[0] for d in definitions],
        'animations':['Idle','Walk'],'orientation':'Blender +Y forward/+Z up, Godot -Z forward/+Y up',
        'skin':'rigid segmented parts with normalized single-bone weights; not organic humanoid deformation',
        'source':'Original local procedural geometry/materials/animation','lod':'runtime cheap capsule proxy beyond 35 m',
        'collision':'Godot CharacterBody3D capsule; source rig is never flattened','external_credits':0}
(ROOT/'generated/manifests/worker_fixture.json').write_text(json.dumps(report,indent=2))
print('CHARACTER_BLENDER_PASS: rig, skin, Idle/Walk, editable source and GLB')
