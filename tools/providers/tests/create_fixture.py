"""Blender-only local textured fixture; never contacts an AI provider."""
from pathlib import Path
import bpy

root = Path(__file__).resolve().parents[3]
folder = root / 'generated/provider-fixtures'
folder.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, location=(4, -3, 2))
obj = bpy.context.object
obj.name = 'PBR_TestHull'
obj.scale = (-2, 1, 1)
material = bpy.data.materials.new('PBR_Fixture')
material.use_nodes = True
shader = material.node_tree.nodes.get('Principled BSDF')
for label, color, socket in (
    ('BaseColor', (0.08, 0.3, 0.5, 1), 'Base Color'),
    ('Metallic', (0.7, 0.7, 0.7, 1), 'Metallic'),
    ('Roughness', (0.4, 0.4, 0.4, 1), 'Roughness'),
    ('Emission', (0.03, 0.15, 0.2, 1), 'Emission Color'),
    ('Normal', (0.5, 0.5, 1, 1), None)
):
    image = bpy.data.images.new(label, width=4, height=4)
    image.pixels = list(color) * 16
    if label in ('Metallic', 'Roughness', 'Normal'):
        image.colorspace_settings.name = 'Non-Color'
    image.pack()
    texture = material.node_tree.nodes.new('ShaderNodeTexImage')
    texture.image = image
    if socket:
        material.node_tree.links.new(texture.outputs['Color'], shader.inputs[socket])
    else:
        normal = material.node_tree.nodes.new('ShaderNodeNormalMap')
        material.node_tree.links.new(texture.outputs['Color'], normal.inputs['Color'])
        material.node_tree.links.new(normal.outputs['Normal'], shader.inputs['Normal'])
shader.inputs['Emission Strength'].default_value = 1.0
obj.data.materials.append(material)
bpy.ops.object.camera_add()
bpy.context.object.name = 'Unused_ProviderCamera'
bpy.ops.export_scene.gltf(filepath=str(folder / 'textured_source.glb'), export_format='GLB', export_cameras=True)
print('PROVIDER_FIXTURE_PASS')
