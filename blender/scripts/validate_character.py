"""Read-only validation of a saved skinned character; never flatten its rig."""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[2]
spec=json.loads((root/sys.argv[sys.argv.index('--')+1]).read_text())
bpy.ops.wm.open_mainfile(filepath=str(root/spec['source']))
rigs=[o for o in bpy.context.scene.objects if o.type=='ARMATURE']
assert len(rigs)==1, 'Expected one rig'
rig=rigs[0]
assert set(spec['bones'])<=set(rig.data.bones.keys()), 'Missing bones'
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert meshes, 'Missing meshes'
triangles=0
for obj in meshes:
    assert obj.data.materials and all(obj.data.materials), 'Missing material'
    assert any(m.type=='ARMATURE' and m.object==rig for m in obj.modifiers), 'Missing skin modifier'
    for vertex in obj.data.vertices:
        assert all(math.isfinite(x) for x in vertex.co), 'Invalid vertex'
        assert abs(sum(g.weight for g in vertex.groups)-1)<1e-5, 'Unnormalized skin weights'
        assert all(obj.vertex_groups[g.group].name in rig.data.bones for g in vertex.groups), 'Invalid bone reference'
    obj.data.calc_loop_triangles();triangles+=len(obj.data.loop_triangles)
    assert all(t.area>1e-10 for t in obj.data.loop_triangles), 'Degenerate triangle'
assert triangles<=spec['max_triangles'], 'Triangle budget'
assert set(spec['animations'])<=set(bpy.data.actions.keys()), 'Missing animation'
corners=[o.matrix_world@Vector(c) for o in meshes for c in o.bound_box]
height=max(v.z for v in corners)-min(v.z for v in corners)
assert spec['height_range'][0]<=height<=spec['height_range'][1], 'Scale'
assert bpy.data.objects['HeadVisor'].location.y>0, 'Forward orientation'
assert (root/spec['model']).is_file(), 'Missing GLB'
print(f'CHARACTER_SOURCE_PASS: 10 categories; {triangles} triangles, {len(rig.data.bones)} bones; weights, topology, materials, clips, scale, orientation, GLB')
