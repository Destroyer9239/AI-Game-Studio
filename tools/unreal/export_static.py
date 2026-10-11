"""Non-destructive static adapter. Run only in Blender's factory-startup process.

Read accepted .blend sources; never save over them. FBX is the UE adapter, while
existing GLBs remain Godot/canonical interchange artifacts. Reject rigged inputs.
"""
import bpy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "generated/unreal/source"
OUT.mkdir(parents=True, exist_ok=True)
records = []
for asset in ("test_fighter", "foundry_building", "market_building", "relay_building"):
    source = ROOT / "blender/projects" / (asset + ".blend")
    bpy.ops.wm.open_mainfile(filepath=str(source))
    assert not any(o.type == 'ARMATURE' for o in bpy.data.objects), "Rig requires specialized exporter"
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH'
              and not any(s in o.name.lower() for s in ('-colonly', '-convcolonly'))]
    assert meshes, asset
    bpy.ops.object.select_all(action='DESELECT')
    for obj in meshes: obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    # Bake evaluated geometry before joining so modifiers stay correct.
    bpy.ops.object.convert(target='MESH')
    bpy.ops.object.join()
    mesh = bpy.context.object
    mesh.name = 'SM_' + asset
    bpy.context.scene.cursor.location = (0, 0, 0)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    mesh.data.calc_loop_triangles()
    triangles = len(mesh.data.loop_triangles)
    assert 0 < triangles <= 25000, (asset, triangles)
    target = OUT / (asset + '.fbx')
    bpy.ops.export_scene.fbx(filepath=str(target), use_selection=True,
        object_types={'MESH'}, axis_forward='-Y', axis_up='Z',
        apply_unit_scale=True, bake_anim=False, path_mode='AUTO', add_leaf_bones=False,
        mesh_smooth_type='FACE')
    records.append(dict(id=asset, source=str(source.relative_to(ROOT)),
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        export=str(target.relative_to(ROOT)), sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
        triangles=triangles, dimensions_m=list(mesh.dimensions), materials=len(mesh.data.materials),
        collision='UE generated simple box; exterior only', rigged=False))
(OUT / 'manifest.json').write_text(json.dumps(records, indent=2))
print('UNREAL_EXPORT_PASS: 4 static assets; original blends preserved')
