extends SceneTree
## Run after editor import: godot --headless --path game --script res://scripts/validate_pipeline.gd

var failures: Array[String] = []


func _initialize() -> void:
	call_deferred("_validate")


func check(condition: bool, message: String) -> void:
	if not condition:
		failures.append(message)
		push_error(message)


func _validate() -> void:
	check(FileAccess.file_exists("res://assets/models/test_fighter.glb"), "Missing generated GLB")
	var packed := load("res://scenes/test_fighter_scene.tscn") as PackedScene
	if packed == null:
		push_error("Cannot load test scene")
		quit(1)
		return
	var scene := packed.instantiate()
	root.add_child(scene)
	await process_frame
	check(ProjectSettings.get_setting("application/run/main_scene") == "res://scenes/test_fighter_scene.tscn", "Incorrect main scene")
	check(scene.get_node("Camera3D").current, "Camera is not active")
	var fighter := scene.get_node("FighterPivot/TestFighter")
	var meshes := fighter.find_children("*", "MeshInstance3D", true, false)
	check(meshes.size() >= 20, "Expected named fighter mesh components")
	check(fighter.find_children("*", "CollisionShape3D", true, false).size() > 0, "Missing imported collision geometry")
	for name_fragment in ["Fuselage_Main", "Cockpit_Canopy", "Wing_Left", "Wing_Right", "Engine_Left_Emissive_Core", "Engine_Right_Emissive_Core"]:
		check(fighter.find_child(name_fragment, true, false) != null, "Missing component: " + name_fragment)
	for side in ["Left", "Right"]:
		var engine := fighter.find_child("Engine_%s_Emissive_Core" % side, true, false) as MeshInstance3D
		if engine != null:
			var material := engine.get_active_material(0) as StandardMaterial3D
			check(material != null and material.emission_enabled, "Engine emission lost during import")
	var pivot := scene.get_node("FighterPivot") as Node3D
	var initial_angle := pivot.rotation.y
	await create_timer(0.2).timeout
	check(pivot.rotation.y > initial_angle, "Fighter does not rotate")
	var key := InputEventKey.new()
	key.pressed = true
	key.keycode = KEY_SPACE
	scene._unhandled_key_input(key)
	var paused_angle := pivot.rotation.y
	await create_timer(0.1).timeout
	check(is_equal_approx(pivot.rotation.y, paused_angle), "Pause control failed")
	key.keycode = KEY_R
	scene._unhandled_key_input(key)
	check(pivot.rotation.is_zero_approx() and scene.rotating, "Reset control failed")
	print("PIPELINE_SCENE_%s: %d visible meshes; rotation, pause, reset, materials and collision checked" % ["PASS" if failures.is_empty() else "FAIL", meshes.size()])
	quit(0 if failures.is_empty() else 1)
