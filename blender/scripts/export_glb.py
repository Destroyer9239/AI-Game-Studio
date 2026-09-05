"""Export the Blender project opened by the CLI; no external Python dependencies."""
import argparse
from pathlib import Path
import struct
import sys
import bpy

parser = argparse.ArgumentParser()
parser.add_argument("--output", required=True)
parser.add_argument("--uv-mode", choices=("none", "required", "smart"), default="none")
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
root = Path(__file__).resolve().parents[2]
output = Path(args.output).resolve()
if not output.is_relative_to(root / "game/assets/models") or output.suffix != ".glb":
    raise ValueError("Export destination must be a .glb under game/assets/models")
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if not meshes:
    raise ValueError("No mesh geometry to export")
for obj in meshes:
    if obj.name.endswith(("-colonly", "-convcolonly")):
        continue
    if not obj.data.materials:
        raise ValueError(f"Mesh has no material: {obj.name}")
    if args.uv_mode != "none" and not obj.data.uv_layers:
        if args.uv_mode == "required":
            raise ValueError(f"Missing authored UVs: {obj.name}")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(island_margin=0.02)
        bpy.ops.object.mode_set(mode="OBJECT")
if args.uv_mode == "smart":
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
output.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(output), export_format="GLB", export_apply=True,
                         export_yup=True, export_cameras=False, export_lights=False)
data = output.read_bytes()
magic, version, length = struct.unpack_from("<4sII", data)
if magic != b"glTF" or version != 2 or length != len(data):
    raise ValueError("Invalid GLB container header")
print(f"PIPELINE_GLB_PASS: {output} ({len(data)} bytes; {len(meshes)} source meshes)")
