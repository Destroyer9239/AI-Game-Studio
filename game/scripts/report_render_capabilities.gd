extends SceneTree

func _initialize() -> void:
	var report := {"version": Engine.get_version_info(), "classes": {}, "project_settings": {}}
	for class_name_value in ["Environment", "WorldEnvironment", "PhysicalSkyMaterial", "PanoramaSkyMaterial", "ProceduralSkyMaterial", "ReflectionProbe", "Decal", "GPUParticles3D", "MultiMeshInstance3D", "OccluderInstance3D", "NavigationRegion3D"]:
		var properties: Array[String] = []
		for property in ClassDB.class_get_property_list(class_name_value):
			properties.append(str(property.name))
		report.classes[class_name_value] = properties
	for property in ProjectSettings.get_property_list():
		var key := str(property.name)
		if key.begins_with("rendering/") and ("shadow" in key or "anisotropic" in key or "ray" in key or "anti_aliasing" in key or "occlusion" in key):
			report.project_settings[key] = ProjectSettings.get_setting(key)
	var file := FileAccess.open("res://../generated/reports/godot_capabilities.json", FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "  "))
	print("RENDER_CAPABILITIES_PASS: ", Engine.get_version_info().string)
	quit()
