"""Conservative static asset cleanup. Staging only; Godot promotion is separate.

Preserves material node graphs, UVs and source files. Rigged/animated/morph assets
stop for specialized processing instead of silently flattening their animation.
"""
import argparse
import json
import math
from pathlib import Path
import sys
import struct
import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]

def safe_path(value):
    result = Path(value).resolve()
    if not result.is_relative_to(ROOT):
        raise ValueError('Cleanup paths must stay inside this workspace')
    return result

def texture_audit():
    images = []
    for image in bpy.data.images:
        if image.name in ('Render Result', 'Viewer Node'):
            continue
        if image.source == 'FILE' and not image.packed_file:
            texture = Path(bpy.path.abspath(image.filepath))
            if not texture.is_file():
                raise ValueError('Missing texture reference: ' + image.name)
        # glTF imports packed images lazily; touching pixels decodes the buffer.
        pixel_count = len(image.pixels)
        if not image.has_data or image.size[0] == 0 or pixel_count == 0:
            raise ValueError('Unreadable texture: ' + image.name)
        if not image.packed_file:
            image.pack()
        if not image.packed_file:
            raise ValueError('Texture could not be packed: ' + image.name)
        images.append({'name': image.name, 'size': list(image.size), 'color_space': image.colorspace_settings.name, 'packed': bool(image.packed_file)})
    connections = []
    for material in bpy.data.materials:
        if not material.use_nodes:
            continue
        for link in material.node_tree.links:
            connections.append({'material': material.name, 'from_node': link.from_node.bl_idname, 'from_socket': link.from_socket.name,
                                'to_node': link.to_node.bl_idname, 'to_socket': link.to_socket.name})
    return images, connections

def triangles(objects):
    total = 0
    for obj in objects:
        obj.data.calc_loop_triangles()
        total += len(obj.data.loop_triangles)
    return total

def export(file, objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(file), export_format='GLB', use_selection=True, export_apply=True,
                             export_yup=True, export_cameras=False, export_lights=False)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    config = json.loads(safe_path(args.config).read_text(encoding='utf-8'))
    source, output = safe_path(config['source']), safe_path(config['output_dir'])
    if not output.is_relative_to(ROOT / 'generated/processed'):
        raise ValueError('Cleaned models must first be exported to generated/processed')
    name = config['name']
    if not name.replace('_', '').isalnum():
        raise ValueError('Invalid cleanup asset name')
    if source.suffix.lower() in ('.gltf', '.glb'):
        if source.suffix.lower() == '.glb':
            data = source.read_bytes()
            if data[:4] != b'glTF' or len(data) < 20:
                raise ValueError('Invalid GLB header')
            gltf = json.loads(data[20:20 + struct.unpack_from('<I', data, 12)[0]])
        else:
            gltf = json.loads(source.read_text(encoding='utf-8'))
        for entry in gltf.get('buffers', []) + gltf.get('images', []):
            uri = entry.get('uri', '')
            if uri and not uri.startswith('data:'):
                resource = (source.parent / uri).resolve()
                if '://' in uri or not resource.is_relative_to(source.parent) or not resource.is_file():
                    raise ValueError('Missing or unsafe glTF buffer/texture reference')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    if source.suffix.lower() in ('.glb', '.gltf'):
        bpy.ops.import_scene.gltf(filepath=str(source))
    elif source.suffix.lower() == '.fbx':
        bpy.ops.import_scene.fbx(filepath=str(source))
    else:
        raise ValueError('Supported sources are GLB, glTF and FBX')
    objects = list(bpy.context.scene.objects)
    if bpy.data.actions or any(obj.type == 'ARMATURE' or obj.animation_data or (obj.type == 'MESH' and obj.data.shape_keys) for obj in objects):
        raise ValueError('Rigged/animated/morph model requires specialized preservation workflow; static cleanup refuses it')
    removed = []
    for obj in objects:
        if obj.type in ('CAMERA', 'LIGHT') or (obj.type == 'MESH' and (not obj.data.polygons or obj.name.endswith(('-colonly', '-convcolonly')))):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    if not meshes:
        raise ValueError('No usable mesh geometry')
    images, connections = texture_audit()
    if images and any(not obj.data.uv_layers for obj in meshes):
        raise ValueError('Textured model has missing UVs; do not invent mapping during cleanup')
    before = triangles(meshes)
    # Flatten static transforms without changing the model's orientation or silhouette.
    world_matrices = {obj: obj.matrix_world.copy() for obj in meshes}
    for obj in meshes:
        obj.data = obj.data.copy()
        obj.parent = None
        transform = world_matrices[obj]
        obj.data.transform(transform)
        if transform.determinant() < 0:
            obj.data.flip_normals()
        obj.matrix_world = Matrix.Identity(4)
        for vertex in obj.data.vertices:
            if not all(math.isfinite(v) for v in vertex.co):
                raise ValueError('Non-finite vertex coordinates')
        obj.data.update()
        if any(face.area <= 1e-12 or not all(math.isfinite(v) for v in face.normal) for face in obj.data.polygons):
            raise ValueError('Degenerate faces or invalid normals need deliberate repair')
        if not obj.data.materials:
            material = bpy.data.materials.new(obj.name + '_NeutralFallback')
            material.diffuse_color = (0.35, 0.4, 0.45, 1)
            obj.data.materials.append(material)
        if any(mat is None for mat in obj.data.materials) or any(face.material_index >= len(obj.data.materials) for face in obj.data.polygons):
            raise ValueError('Broken material references on ' + obj.name)
    points = [vertex.co for obj in meshes for vertex in obj.data.vertices]
    lower = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    upper = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    dimensions = upper - lower
    if max(dimensions) <= 1e-8:
        raise ValueError('Empty model bounds')
    target = float(config.get('longest_side_m', 2.0))
    factor = target / max(dimensions)
    center = (lower + upper) * 0.5
    if config.get('origin', 'center') == 'bottom':
        center.z = lower.z
    normalize = Matrix.Scale(factor, 4) @ Matrix.Translation(-center)
    for obj in meshes:
        obj.data.transform(normalize)
    budget = int(config.get('max_triangles', 20000))
    if before > budget:
        if not config.get('allow_decimate', False):
            raise ValueError(f'{before} triangles exceed {budget}; explicit allow_decimate or authored retopology required')
        for obj in meshes:
            modifier = obj.modifiers.new('BudgetDecimation', 'DECIMATE')
            modifier.ratio = budget / before * 0.98
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    after = triangles(meshes)
    if after > budget:
        raise ValueError('Decimated model still exceeds triangle budget')
    # Box proxy gives predictable cheap collision; never substitutes for flight physics.
    lower, upper = (lower - center) * factor, (upper - center) * factor
    bpy.ops.mesh.primitive_cube_add(size=1, location=(lower + upper) * 0.5)
    collision = bpy.context.object
    collision.name = name + '-colonly'
    collision.dimensions = upper - lower
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    collision.hide_render = True
    collision.display_type = 'WIRE'
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'EMPTY' and not obj.children:
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.context.preferences.filepaths.save_version = 0
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(output / (name + '.blend')))
    export(output / (name + '.glb'), meshes + [collision])
    lod = None
    ratio = float(config.get('lod_ratio', 0))
    if 0 < ratio < 1 and after > 100:
        for obj in meshes:
            modifier = obj.modifiers.new('LODPreview', 'DECIMATE')
            modifier.ratio = ratio
        lod = name + '_lod1.glb'
        export(output / lod, meshes)
    audit = {'source': str(source.relative_to(ROOT)), 'source_triangles': before, 'polygon_count': after,
             'material_count': len({mat.name for obj in meshes for mat in obj.data.materials if mat}),
             'textured': bool(images), 'textures': images, 'material_connections': connections,
             'normalization': {'factor': factor, 'longest_side_m': target, 'origin': config.get('origin', 'center'), 'units': 'meters', 'orientation': 'source preserved; inspect front/up in preview'},
             'removed_objects': removed, 'collision_status': 'GENERATED_BOX_PROXY', 'lod_file': lod,
             'normals_status': 'FINITE_NONDEGENERATE; negative-determinant winding corrected; existing shading retained'}
    (output / 'audit.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    print('PIPELINE_CLEANUP_PASS: ' + str(output))

if __name__ == '__main__':
    main()
