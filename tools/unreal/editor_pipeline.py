"""UE 5.7 editor-only build and acceptance. No Python runtime gameplay dependency."""
import json
import os
import traceback
import hashlib
import struct
import time
from pathlib import Path
import unreal as u

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(os.environ['CINDER_REPORT_DIR'])
ACTION = os.environ['CINDER_ACTION']
BASE = '/Game/Cinder/Generated'
MAP = BASE + '/Maps/L_Pipeline'
assets = u.AssetToolsHelpers.get_asset_tools()
library = u.EditorAssetLibrary
meshes = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
actors = u.get_editor_subsystem(u.EditorActorSubsystem)
levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
checks = []

def check(value, message):
    if not value: raise RuntimeError(message)
    checks.append(message)

def import_asset(source, folder, name, options=None):
    task = u.AssetImportTask()
    task.filename = str(source)
    task.destination_path = folder
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    if options: task.options = options
    assets.import_asset_tasks([task])
    objects = task.get_objects()
    check(bool(objects), 'Imported ' + name)
    return objects[0]

def material(name, color, roughness=.65, metallic=0):
    path = BASE + '/Materials/' + name
    existing = library.load_asset(path) if library.does_asset_exist(path) else None
    if existing: return existing
    result = assets.create_asset(name, BASE+'/Materials', u.Material, u.MaterialFactoryNew())
    node = u.MaterialEditingLibrary.create_material_expression(result, u.MaterialExpressionConstant3Vector)
    node.constant = u.LinearColor(*color, 1)
    u.MaterialEditingLibrary.connect_material_property(node, '', u.MaterialProperty.MP_BASE_COLOR)
    for value, prop in [(roughness, u.MaterialProperty.MP_ROUGHNESS), (metallic, u.MaterialProperty.MP_METALLIC)]:
        scalar = u.MaterialEditingLibrary.create_material_expression(result, u.MaterialExpressionConstant)
        scalar.r = value
        u.MaterialEditingLibrary.connect_material_property(scalar, '', prop)
    u.MaterialEditingLibrary.recompile_material(result)
    library.save_loaded_asset(result)
    return result

def concrete():
    path = BASE+'/Materials/M_Concrete'
    if library.does_asset_exist(path): return library.load_asset(path)
    mat = assets.create_asset('M_Concrete',BASE+'/Materials',u.Material,u.MaterialFactoryNew())
    for role, prop in [('basecolor',u.MaterialProperty.MP_BASE_COLOR),('normal',u.MaterialProperty.MP_NORMAL),('roughness',u.MaterialProperty.MP_ROUGHNESS)]:
        tex = import_asset(ROOT/'game/assets/textures/polyhaven/brushed_concrete'/f'{role}.png',BASE+'/Textures','T_Concrete_'+role)
        tex.set_editor_property('srgb',role=='basecolor')
        if role=='normal':
            tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_NORMALMAP)
            tex.set_editor_property('flip_green_channel',True) # OpenGL source -> UE tangent convention.
        elif role=='roughness': tex.set_editor_property('compression_settings',u.TextureCompressionSettings.TC_MASKS)
        library.save_loaded_asset(tex)
        sample=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionTextureSample)
        sample.texture=tex
        if role=='normal':sample.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_NORMAL
        elif role=='roughness':sample.sampler_type=u.MaterialSamplerType.SAMPLERTYPE_MASKS
        uv=u.MaterialEditingLibrary.create_material_expression(mat,u.MaterialExpressionTextureCoordinate)
        uv.u_tiling=12;uv.v_tiling=12
        u.MaterialEditingLibrary.connect_material_expressions(uv,'',sample,'UVs')
        u.MaterialEditingLibrary.connect_material_property(sample,'R' if role=='roughness' else 'RGB',prop)
    u.MaterialEditingLibrary.recompile_material(mat);library.save_loaded_asset(mat)
    return mat

def spawn(cls, name, location, rotation=(0,0,0)):
    actor=actors.spawn_actor_from_class(cls,u.Vector(*location),u.Rotator(*rotation))
    check(actor is not None,'Spawned '+name)
    actor.set_actor_label(name)
    return actor

def build():
    records=json.loads((ROOT/'generated/unreal/source/manifest.json').read_text())
    palette=[material('M_Structure',(.04,.07,.085),.45,.65), material('M_Hull',(.4,.44,.42)),material('M_Accent',(.55,.19,.025),.4,.5)]
    imported=[]
    for record in records:
        options=u.FbxImportUI()
        options.import_mesh=True;options.import_materials=False;options.import_textures=False
        options.import_as_skeletal=False;options.import_animations=False
        options.mesh_type_to_import=u.FBXImportType.FBXIT_STATIC_MESH
        options.static_mesh_import_data.combine_meshes=True
        options.static_mesh_import_data.auto_generate_collision=False
        mesh=import_asset(ROOT/record['export'],BASE+'/Meshes','SM_'+record['id'],options)
        check(isinstance(mesh,u.StaticMesh),'Static mesh '+record['id'])
        meshes.remove_collisions(mesh)
        meshes.add_simple_collisions(mesh,u.ScriptCollisionShapeType.BOX)
        for index,slot in enumerate(mesh.static_materials):
            label=str(slot.material_slot_name).lower()
            selected=palette[2] if any(v in label for v in ('accent','orange','warning')) else palette[0] if any(v in label for v in ('dark','metal','glass','glaz')) else palette[1]
            mesh.set_material(index,selected)
        library.save_loaded_asset(mesh)
        record['unreal_path']=mesh.get_path_name()
        imported.append(record)
    floor_material=concrete()
    if library.does_asset_exist(MAP):
        levels.load_level(MAP)
        for actor in actors.get_all_level_actors():
            if actor.get_actor_label().startswith('Pipeline_'):actors.destroy_actor(actor)
    else:check(levels.new_level(MAP),'Created pipeline map')
    floor=spawn(u.StaticMeshActor,'Pipeline_Floor',(0,0,-20))
    floor.static_mesh_component.set_static_mesh(library.load_asset('/Engine/BasicShapes/Cube'))
    floor.set_actor_scale3d(u.Vector(120,120,.4))
    floor.static_mesh_component.set_material(0,floor_material)
    placements=[(0,-500,260),(-2300,1600,0),(0,2200,0),(2500,2000,0)]
    for record,location in zip(imported,placements):
        actor=spawn(u.StaticMeshActor,'Pipeline_'+record['id'],location)
        actor.static_mesh_component.set_static_mesh(library.load_asset(record['unreal_path']))
    sun=spawn(u.DirectionalLight,'Pipeline_Sun',(0,0,3000),(-35,-35,0))
    sun.light_component.set_editor_property('intensity',5.0)
    sun.light_component.set_editor_property('atmosphere_sun_light',True)
    spawn(u.SkyAtmosphere,'Pipeline_Atmosphere',(0,0,0))
    sky=spawn(u.SkyLight,'Pipeline_Sky',(0,0,2000))
    sky.light_component.set_editor_property('real_time_capture',True)
    spawn(u.ExponentialHeightFog,'Pipeline_Fog',(0,0,0))
    spawn(u.PlayerStart,'Pipeline_PlayerStart',(0,-3000,130),(0,90,0))
    camera=spawn(u.CameraActor,'Pipeline_ReviewCamera',(6500,-6500,3700))
    camera.set_actor_rotation(u.MathLibrary.find_look_at_rotation(camera.get_actor_location(),u.Vector(0,1300,700)),False)
    u.get_editor_subsystem(u.UnrealEditorSubsystem).set_level_viewport_camera_info(camera.get_actor_location(),camera.get_actor_rotation())
    check(levels.save_current_level(),'Saved pipeline map')
    library.save_directory(BASE)
    (ROOT/'generated/unreal/import_manifest.json').write_text(json.dumps(imported,indent=2))

def validate():
    records=json.loads((ROOT/'generated/unreal/import_manifest.json').read_text())
    for record in records:
        check(hashlib.sha256((ROOT/record['source']).read_bytes()).hexdigest()==record['source_sha256'],record['id']+' source not stale')
        check(hashlib.sha256((ROOT/record['export']).read_bytes()).hexdigest()==record['sha256'],record['id']+' export hash verified')
        mesh=library.load_asset(record['unreal_path'])
        check(isinstance(mesh,u.StaticMesh),record['id']+' loads')
        check(mesh.get_num_lods()>0,record['id']+' has geometry')
        check(mesh.get_num_sections(0)>0,record['id']+' has sections')
        check(meshes.get_simple_collision_count(mesh)>0,record['id']+' has simple collision')
        actual=sorted([mesh.get_bounds().box_extent.x*2,mesh.get_bounds().box_extent.y*2,mesh.get_bounds().box_extent.z*2])
        expected=sorted([v*100 for v in record['dimensions_m']])
        check(all(abs(a-b)<max(2,b*.02) for a,b in zip(actual,expected)),record['id']+' meters to centimeters')
        for slot in mesh.static_materials:check(slot.material_interface is not None,record['id']+' material assigned')
    check(levels.load_level(MAP),'Map loads')
    check(sum(a.get_actor_label().startswith('Pipeline_') for a in actors.get_all_level_actors())==11,'Exactly eleven generated actors; no duplicate builds')
    check(any(a.get_actor_label()=='Pipeline_PlayerStart' for a in actors.get_all_level_actors()),'Player start exists')
    for role in ('basecolor','normal','roughness'):
        tex=library.load_asset(BASE+'/Textures/T_Concrete_'+role)
        check(isinstance(tex,u.Texture2D),'Concrete '+role+' texture loads')
        check(tex.get_editor_property('srgb')==(role=='basecolor'),'Concrete '+role+' color space')
        if role=='normal':check(tex.get_editor_property('flip_green_channel'),'Normal convention corrected')
    for path in ['/Game/FirstPerson/Blueprints/BP_FirstPersonGameMode','/Game/FirstPerson/Blueprints/BP_FirstPersonCharacter']:
        check(library.load_asset(path) is not None,'Template loads '+path)

def finish():
    (REPORT/'result.json').write_text(json.dumps(dict(status='PASS',action=ACTION,checks=checks,count=len(checks)),indent=2))
    print('CINDER_UNREAL_PASS: '+str(len(checks))+' checks')

try:
    if ACTION=='build':build()
    validate()
    if ACTION=='preview':
        camera=next(a for a in actors.get_all_level_actors() if a.get_actor_label()=='Pipeline_ReviewCamera')
        output=ROOT/'generated/previews/unreal_pipeline.png'
        output.parent.mkdir(parents=True,exist_ok=True)
        if output.exists():output.unlink()
        u.EditorPythonScripting.set_keep_python_script_alive(True)
        start=time.monotonic();task=None;requested=False
        def tick(delta):
            global task,requested
            try:
                if time.monotonic()-start>180:raise RuntimeError('Screenshot timed out')
                if not requested and time.monotonic()-start>12:
                    requested=True
                    task=u.AutomationLibrary.take_high_res_screenshot(3840,2160,str(output),camera=camera,delay=3.0)
                    check(task is not None,'Screenshot requested')
                elif task is not None and task.is_task_done() and output.exists():
                    raw=output.read_bytes()
                    check(raw[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',raw[16:24])==(3840,2160),'GPU screenshot 3840x2160 saved')
                    finish();u.unregister_slate_post_tick_callback(handle)
                    u.EditorPythonScripting.set_keep_python_script_alive(False)
            except Exception:
                (REPORT/'result.json').write_text(json.dumps(dict(status='FAIL',traceback=traceback.format_exc()),indent=2))
                u.log_error(traceback.format_exc());u.unregister_slate_post_tick_callback(handle)
                u.EditorPythonScripting.set_keep_python_script_alive(False)
        handle=u.register_slate_post_tick_callback(tick)
    elif ACTION=='test':
        u.EditorPythonScripting.set_keep_python_script_alive(True)
        levels.editor_request_begin_play()
        start=time.monotonic();initial=None;stopping=False
        def play_tick(delta):
            global initial,stopping
            try:
                elapsed=time.monotonic()-start
                if elapsed>60:raise RuntimeError('PIE acceptance timed out')
                if stopping:
                    if not levels.is_in_play_in_editor():
                        check(True,'PIE stopped cleanly');finish()
                        u.unregister_slate_post_tick_callback(play_handle)
                        u.EditorPythonScripting.set_keep_python_script_alive(False)
                    return
                world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
                if not world or elapsed<4:return
                pawn=u.GameplayStatics.get_player_character(world,0)
                check(pawn is not None,'First-person character spawned') if initial is None else None
                if initial is None:
                    initial=pawn.get_actor_location()
                    check('BP_FirstPersonCharacter' in pawn.get_class().get_name(),'Epic first-person Blueprint active')
                    check(pawn.get_component_by_class(u.CharacterMovementComponent).movement_mode==u.MovementMode.MOVE_WALKING,'Character grounded on test collision')
                pawn.add_movement_input(u.Vector(1,0,0),1,True)
                if elapsed>7:
                    check(pawn.get_actor_location().x-initial.x>100,'Character movement advances over 1 meter')
                    levels.editor_request_end_play();stopping=True
            except Exception:
                (REPORT/'result.json').write_text(json.dumps(dict(status='FAIL',traceback=traceback.format_exc()),indent=2))
                u.log_error(traceback.format_exc());levels.editor_request_end_play()
                u.unregister_slate_post_tick_callback(play_handle)
                u.EditorPythonScripting.set_keep_python_script_alive(False)
        play_handle=u.register_slate_post_tick_callback(play_tick)
    else:finish()
except Exception:
    (REPORT/'result.json').write_text(json.dumps(dict(status='FAIL',action=ACTION,checks=checks,traceback=traceback.format_exc()),indent=2))
    raise
