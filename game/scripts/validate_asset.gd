extends SceneTree
## Manifest-driven geometry/material/collision validation, independent of asset name.
var failures: Array[String] = []

func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)

func _initialize() -> void:
	call_deferred("_validate")

func _validate() -> void:
	var manifest_path := ""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--manifest="):
			manifest_path = argument.trim_prefix("--manifest=")
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	if not data is Dictionary:
		push_error("Missing or invalid asset manifest")
		quit(1)
		return
	var config: Dictionary = data
	var path: String = str(config.scene).replace("game/", "res://")
	var packed := load(path) as PackedScene
	if packed == null:
		push_error("Missing asset integration scene: " + path)
		quit(1)
		return
	var asset := packed.instantiate() as Node3D
	root.add_child(asset)
	await process_frame
	var meshes := asset.find_children("*", "MeshInstance3D", true, false)
	check(not meshes.is_empty(), "No visible asset meshes")
	var triangles := 0
	var materials: Dictionary = {}
	var material_names: Dictionary = {}
	for child in meshes:
		var instance := child as MeshInstance3D
		check(instance.mesh != null, "Empty mesh: " + str(child.name))
		if instance.mesh == null:
			continue
		check(instance.get_aabb().size.length() > 0.0001, "Degenerate mesh bounds: " + str(child.name))
		check(instance.get_aabb().size.is_finite(), "Non-finite geometry bounds")
		for surface in range(instance.mesh.get_surface_count()):
			check(instance.mesh.surface_get_primitive_type(surface) == Mesh.PRIMITIVE_TRIANGLES, "Expected triangle surface")
			var arrays := instance.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
			triangles += int((indices.size() if not indices.is_empty() else vertices.size()) / 3.0)
			var material := instance.get_active_material(surface)
			check(material != null, "Missing material: " + str(child.name))
			if material != null:
				materials[material.get_instance_id()] = true
				material_names[material.resource_name] = true
				var requirements: Dictionary = config.get("required_texture_slots", {})
				var slots: Array = requirements.get(material.resource_name, [])
				var pbr := material as StandardMaterial3D
				for slot in slots:
					check(pbr != null, "PBR material required")
					if pbr == null:
						continue
					match str(slot):
						"baseColorTexture": check(pbr.albedo_texture != null, "Base-color texture lost")
						"normalTexture": check(pbr.normal_enabled and pbr.normal_texture != null, "Normal map lost")
						"metallicRoughnessTexture": check(pbr.metallic_texture != null and pbr.roughness_texture != null, "Metallic/roughness map lost")
						"emissiveTexture": check(pbr.emission_enabled and pbr.emission_texture != null, "Emission map lost")
			if config.uv_mode != "none":
				var uv: Variant = arrays[Mesh.ARRAY_TEX_UV]
				check(uv != null and uv.size() == vertices.size(), "Missing UVs: " + str(child.name))
	check(triangles > 0 and triangles <= int(config.max_triangles), "Triangle budget exceeded or empty geometry: %d" % triangles)
	check(materials.size() <= int(config.max_materials), "Material budget exceeded: %d" % materials.size())
	for expected_material in config.get("required_texture_slots", {}):
		check(material_names.has(expected_material), "Required PBR material missing: " + str(expected_material))
	if config.require_collision:
		var shapes := asset.find_children("*", "CollisionShape3D", true, false)
		check(not shapes.is_empty(), "Missing collision setup")
		for shape in shapes:
			check(shape.shape != null and not shape.disabled, "Invalid/disabled collision shape")
	for component in config.required_nodes:
		check(asset.find_child(str(component), true, false) != null, "Missing required node: " + str(component))
	for component in config.emissive_nodes:
		var node := asset.find_child(str(component), true, false) as MeshInstance3D
		check(node != null, "Missing emissive mesh: " + str(component))
		if node != null:
			var material := node.get_active_material(0) as StandardMaterial3D
			check(material != null and material.emission_enabled and material.emission.get_luminance() > 0, "Emission lost: " + str(component))
	print("PIPELINE_ASSET_%s: %s; %d meshes; %d triangles; %d materials" % ["PASS" if failures.is_empty() else "FAIL", config.id, meshes.size(), triangles, materials.size()])
	asset.queue_free()
	await process_frame
	quit(0 if failures.is_empty() else 1)
