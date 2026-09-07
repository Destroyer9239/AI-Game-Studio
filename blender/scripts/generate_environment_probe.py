"""Original modular industrial wall/floor sample, packed PBR textures, meters."""
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.preferences.filepaths.save_version = 0

def material(name, color, metallic=0, roughness=.5, emission=False):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    node = mat.node_tree.nodes.get('Principled BSDF')
    node.inputs['Base Color'].default_value = (*color,1)
    node.inputs['Metallic'].default_value = metallic
    node.inputs['Roughness'].default_value = roughness
    if emission:
        node.inputs['Emission Color'].default_value = (*color,1)
        node.inputs['Emission Strength'].default_value = 4
    return mat

concrete = material('Concrete_4K_Authored_Relief',(.45,.45,.45),roughness=.82)
nodes, links = concrete.node_tree.nodes, concrete.node_tree.links
bsdf = nodes.get('Principled BSDF')
for role, socket in [('basecolor','Base Color'),('roughness','Roughness'),('normal','Normal')]:
    image = bpy.data.images.load(str(ROOT/f'game/assets/textures/industrial_concrete/industrial_concrete_{role}.png'))
    image.colorspace_settings.name = 'sRGB' if role == 'basecolor' else 'Non-Color'
    image.pack()
    texture = nodes.new('ShaderNodeTexImage')
    texture.image = image
    if role == 'normal':
        normal = nodes.new('ShaderNodeNormalMap')
        links.new(texture.outputs['Color'],normal.inputs['Color'])
        links.new(normal.outputs['Normal'],bsdf.inputs[socket])
    else:
        links.new(texture.outputs['Color'],bsdf.inputs[socket])
steel = material('Graphite_Steel',(.065,.085,.11),.85,.32)
light = material('Cyan_Strip',(.015,.65,.85),emission=True)

def box(name,location,scale,mat):
    bpy.ops.mesh.primitive_cube_add(size=1,location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat)
    # Planar per-face physical UV scale, 2 meters per repeated tile.
    for polygon in obj.data.polygons:
        axis = max(range(3),key=lambda a:abs(polygon.normal[a]))
        axes = [a for a in range(3) if a != axis]
        for loop_index in polygon.loop_indices:
            co = obj.data.vertices[obj.data.loops[loop_index].vertex_index].co
            obj.data.uv_layers.active.data[loop_index].uv = (co[axes[0]]/2,co[axes[1]]/2)
    return obj

box('Floor_Module',(0,0,-.12),(8,6,.24),concrete)
box('Wall_Module',(0,2.9,1.5),(8,.2,3),concrete)
for x in (-4,0,4):
    box('Steel_Pillar_'+str(x),(x,2.65,1.55),(.14,.25,3.1),steel)
    box('Emission_Strip_'+str(x),(x,2.50,1.55),(.035,.025,2.65),light)
box('Wall_Cap',(0,2.65,3),(8.15,.4,.12),steel)
for name,loc,scale in [('Floor-colonly',(0,0,-.12),(8,6,.24)),('Wall-colonly',(0,2.9,1.5),(8,.2,3))]:
    box(name,loc,scale,concrete)
output = ROOT/'blender/projects/environment_probe.blend'
output.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(output))
print('PIPELINE_BLENDER_PASS: '+str(output))
