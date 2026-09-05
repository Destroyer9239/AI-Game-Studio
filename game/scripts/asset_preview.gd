extends Node3D
## Shared GPU turntable. Automatically frames a manifest-generated asset wrapper.
var pivot := Node3D.new()
var rotating := true
var elapsed := 0.0
var capture := ""
var capturing := false

func _ready() -> void:
	var asset_path := "res://scenes/assets/test_fighter.tscn"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--asset="):
			asset_path = argument.trim_prefix("--asset=")
		elif argument.begins_with("--capture="):
			capture = argument.trim_prefix("--capture=")
	var packed := load(asset_path) as PackedScene
	if packed == null:
		push_error("Preview cannot load " + asset_path)
		get_tree().quit(1)
		return
	add_child(pivot)
	var asset := packed.instantiate() as Node3D
	pivot.add_child(asset)
	var bounds := AABB()
	var has_bounds := false
	for child in asset.find_children("*", "MeshInstance3D", true, false):
		var mesh := child as MeshInstance3D
		var world_bounds: AABB = mesh.global_transform * mesh.get_aabb()
		bounds = bounds.merge(world_bounds) if has_bounds else world_bounds
		has_bounds = true
	if not has_bounds:
		push_error("No geometry to preview")
		get_tree().quit(1)
		return
	asset.position -= bounds.get_center()
	var radius := maxf(bounds.size.length() * 0.5, 0.1)
	var environment := Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = Color(0.007, 0.013, 0.026)
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color(0.45, 0.58, 0.7)
	environment.ambient_light_energy = 0.5
	var sky := Sky.new()
	sky.sky_material = ProceduralSkyMaterial.new()
	environment.sky = sky
	environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	var world := WorldEnvironment.new()
	world.environment = environment
	add_child(world)
	for values in [Vector3(-45, -30, 0), Vector3(-25, 145, 0)]:
		var light := DirectionalLight3D.new()
		light.rotation_degrees = values
		light.light_energy = 1.0 if values.y < 0 else 0.65
		light.light_color = Color(0.9, 0.94, 1.0) if values.y < 0 else Color(0.25, 0.58, 1.0)
		add_child(light)
	var camera := Camera3D.new()
	add_child(camera)
	camera.fov = 40.0
	camera.near = maxf(radius / 100.0, 0.01)
	camera.far = radius * 30.0
	# Sphere fit is stable as the asset rotates and works for tall/wide assets.
	var aspect := get_viewport().get_visible_rect().size.aspect()
	var half_angle := deg_to_rad(camera.fov * 0.5)
	if aspect < 1.0:
		half_angle = atan(tan(half_angle) * aspect)
	camera.position = Vector3(0.9, 0.8, -1.1).normalized() * radius / sin(half_angle) * 1.12
	camera.look_at(Vector3.ZERO)
	camera.current = true
	var ring := MeshInstance3D.new()
	var torus := TorusMesh.new()
	torus.inner_radius = radius * 0.92
	torus.outer_radius = radius * 0.93
	torus.rings = 96
	torus.ring_segments = 6
	ring.mesh = torus
	ring.position.y = -bounds.size.y * 0.5 - radius * 0.07
	var ring_material := StandardMaterial3D.new()
	ring_material.albedo_color = Color(0.05, 0.16, 0.23)
	ring.material_override = ring_material
	add_child(ring)
	var hud := CanvasLayer.new()
	add_child(hud)
	var label := Label.new()
	label.position = Vector2(32, 28)
	label.text = asset_path.get_file().get_basename().to_upper() + "  /  ASSET PREVIEW\nSpace: pause   R: reset   Esc: exit"
	label.add_theme_font_size_override("font_size", 20)
	hud.add_child(label)

func _process(delta: float) -> void:
	elapsed += delta
	if rotating:
		pivot.rotation.y += delta * deg_to_rad(12.0)
	if not capture.is_empty() and elapsed >= 1.5 and not capturing:
		capturing = true
		_save_preview()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		match event.keycode:
			KEY_SPACE: rotating = not rotating
			KEY_R:
				pivot.rotation = Vector3.ZERO
				rotating = true
			KEY_ESCAPE: get_tree().quit()

func _save_preview() -> void:
	await RenderingServer.frame_post_draw
	var error := get_viewport().get_texture().get_image().save_png(capture)
	if error != OK:
		push_error("Preview save failed: " + error_string(error))
		get_tree().quit(1)
		return
	print("PIPELINE_PREVIEW_PASS: " + capture)
	get_tree().quit()
