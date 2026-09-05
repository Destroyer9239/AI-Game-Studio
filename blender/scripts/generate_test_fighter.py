"""Generate the original Kestrel test fighter. Run with Blender --background --python.

Meters; Blender +Y is the nose, +Z is up. glTF converts this to Godot -Z/+Y.
Only solid PBR materials are used, so texture UVs are unnecessary.
"""
from pathlib import Path
import math
import sys
import bpy

ROOT = Path(__file__).resolve().parents[2]
BLEND = ROOT / "blender/projects/test_fighter.blend"
GLB = ROOT / "game/assets/models/test_fighter.glb"


def material(name, color, metallic=0.0, roughness=0.4, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1.0)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Emission Color"].default_value = (*color, 1.0)
    shader.inputs["Emission Strength"].default_value = emission
    return mat


def finish(obj, name, mat, bevel=0.0):
    obj.name = name
    obj.data.name = name + "_Mesh"
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("Machined edge bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
        obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return obj


def mesh(name, vertices, faces, mat, bevel=0.025):
    data = bpy.data.meshes.new(name + "_Mesh")
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    # Normalize winding, including mirrored wing geometry.
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.select_set(False)
    return finish(obj, name, mat, bevel)


def loft(name, sections, mat):
    vertices = []
    for y, width, bottom, top in sections:
        vertices.extend([(-width * .65, y, bottom), (width * .65, y, bottom),
                         (width, y, bottom + (top-bottom)*.4),
                         (width*.65, y, top), (-width*.65, y, top),
                         (-width, y, bottom + (top-bottom)*.4)])
    faces = [tuple(range(5, -1, -1))]
    for ring in range(len(sections)-1):
        for j in range(6):
            a, b = ring*6+j, ring*6+(j+1)%6
            faces.append((a, b, b+6, a+6))
    faces.append(tuple((len(sections)-1)*6+j for j in range(6)))
    return mesh(name, vertices, faces, mat)


def slab(name, outline, bottom, top, mat):
    n = len(outline)
    vertices = [(x, y, z) for z in (bottom, top) for x, y in outline]
    faces = [tuple(range(n-1, -1, -1)), tuple(range(n, n*2))]
    faces += [(j, (j+1)%n, (j+1)%n+n, j+n) for j in range(n)]
    return mesh(name, vertices, faces, mat)


def cylinder(name, location, radius, depth, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=radius, depth=depth,
                                        location=location, rotation=(math.pi/2, 0, 0))
    return finish(bpy.context.object, name, mat, .025)


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    hull = material("Hull_Titanium_Slate", (.19, .27, .32), .78, .3)
    edge = material("Armor_Pale_Ceramic_Metal", (.57, .65, .67), .65, .3)
    dark = material("Engine_Graphite", (.035, .052, .068), .7, .4)
    canopy = material("Cockpit_Deep_Teal", (.015, .21, .28), .55, .16)
    stripe = material("Identification_Amber", (.95, .28, .035), .4, .32)
    glow = material("Engine_Ion_Emission", (.035, .65, 1.0), .15, .24, 6.0)

    loft("Fuselage_Main", [(-2.5,.65,-.28,.42), (-1.2,.95,-.42,.65),
                           (1.3,.68,-.28,.48), (3.65,.07,-.06,.09)], hull)
    loft("Nose_Armor", [(1.5,.44,.22,.49), (3.45,.06,.035,.14)], edge)
    loft("Cockpit_Frame", [(-.5,.54,.38,.8), (.45,.52,.4,1.0),
                           (1.65,.26,.24,.54)], dark)
    loft("Cockpit_Canopy", [(-.38,.45,.5,.8), (.43,.43,.53,.94),
                            (1.48,.22,.35,.57)], canopy)
    for side, sign in (("Left", -1), ("Right", 1)):
        def mirrored(points):
            return [(x*sign,y) for x,y in points]
        slab(f"Wing_{side}", mirrored([(.6,1.0), (2.0,.25), (4.15,-1.65),
                                       (3.8,-2.2), (1.0,-1.65)]), -.12,.09,hull)
        slab(f"Wing_{side}_Leading_Armor", mirrored([(.88,.9), (2.0,.25),
             (4.05,-1.66), (3.8,-1.62), (1.85,.02)]), .10,.16,edge)
        slab(f"Wing_{side}_Amber_Marking", mirrored([(2.65,-.64), (2.85,-.83),
             (2.85,-1.77), (2.65,-1.70)]), .105,.125,stripe)
        cylinder(f"Engine_{side}_Housing", (sign*1.16,-1.75,.12), .43,2.0,dark)
        cylinder(f"Engine_{side}_Armor", (sign*1.16,-1.52,.12), .45,1.18,edge)
        cylinder(f"Engine_{side}_Rear_Nozzle", (sign*1.16,-2.8,.12), .36,.24,dark)
        cylinder(f"Engine_{side}_Emissive_Core", (sign*1.16,-2.935,.12), .27,.025,glow)
        cylinder(f"Engine_{side}_Intake", (sign*1.16,-.73,.12), .31,.05,dark)
        # Small swept dorsal stabilizers, distinct from the broad horizontal wings.
        x = sign*.66
        mesh(f"Tail_Fin_{side}", [(x-.07,-2.2,.4),(x+.07,-2.2,.4),
             (x+.07,-1.0,.5),(x-.07,-1.0,.5),
             (x+sign*.38-.04,-2.35,1.22),(x+sign*.38+.04,-2.35,1.22)],
             [(0,3,2,1),(0,1,5,4),(3,4,5,2),(0,4,3),(1,2,5)], hull)

    # Godot's glTF importer converts the -colonly suffix into collision geometry.
    collision = loft("Fuselage-colonly", [(-2.55,.75,-.45,.7),
                      (1.25,.75,-.35,1.0),(3.7,.08,-.08,.12)], dark)
    collision.modifiers.clear()
    collision.hide_render = True
    collision.display_type = "WIRE"
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.context.scene.world.color = (.025,.025,.025)
    # Useful initial view when the editable source is opened.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_distance = 13
    BLEND.parent.mkdir(parents=True, exist_ok=True)
    GLB.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    if "--blend-only" in sys.argv:
        print(f"PIPELINE_BLENDER_PASS: {BLEND} ({BLEND.stat().st_size} bytes)")
        return
    bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB",
                             export_apply=True, export_yup=True,
                             export_cameras=False, export_lights=False)
    assert BLEND.is_file() and BLEND.stat().st_size > 1000
    assert GLB.is_file() and GLB.stat().st_size > 1000
    print(f"PIPELINE_BLENDER_PASS: {BLEND} ({BLEND.stat().st_size} bytes)")
    print(f"PIPELINE_GLB_PASS: {GLB} ({GLB.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
