extends Node3D
## Minimal asset turntable; intentionally no flight or combat systems.

const ROTATION_SPEED := deg_to_rad(12.0)
var rotating := true
var elapsed := 0.0
var capture_path := ""
var capture_started := false
@onready var fighter_pivot: Node3D = $FighterPivot


func _ready() -> void:
	$Camera3D.look_at(Vector3(0, -0.3, 0))
	# Use the sky for hull reflections while retaining a solid dark background.
	var sky := Sky.new()
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color(0.12, 0.22, 0.34)
	sky_material.sky_horizon_color = Color(0.65, 0.72, 0.8)
	sky_material.ground_bottom_color = Color(0.035, 0.05, 0.09)
	sky.sky_material = sky_material
	$WorldEnvironment.environment.sky = sky
	$WorldEnvironment.environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	_make_depth_markers()
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--capture="):
			capture_path = argument.trim_prefix("--capture=")


func _process(delta: float) -> void:
	elapsed += delta
	if rotating:
		fighter_pivot.rotation.y += ROTATION_SPEED * delta
	if not capture_path.is_empty() and elapsed > 1.5 and not capture_started:
		capture_started = true
		_capture_and_quit()


func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	match event.keycode:
		KEY_SPACE:
			rotating = not rotating
		KEY_R:
			fighter_pivot.rotation = Vector3.ZERO
			rotating = true
		KEY_ESCAPE:
			get_tree().quit()
	$HUD/Status.text = "AUTO ROTATION  /  12 DEG PER SECOND" if rotating else "ROTATION PAUSED"


func _make_depth_markers() -> void:
	var marker_material := StandardMaterial3D.new()
	marker_material.albedo_color = Color(0.065, 0.15, 0.2)
	marker_material.metallic = 0.5
	marker_material.roughness = 0.55
	for radius in [5.0, 6.5]:
		var ring := MeshInstance3D.new()
		var torus := TorusMesh.new()
		torus.inner_radius = radius - 0.025
		torus.outer_radius = radius + 0.025
		torus.rings = 96
		torus.ring_segments = 6
		ring.mesh = torus
		ring.material_override = marker_material
		ring.position.y = -1.8
		$DepthMarkers.add_child(ring)
	var star_material := StandardMaterial3D.new()
	star_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	star_material.albedo_color = Color(0.4, 0.56, 0.7)
	var star_mesh := SphereMesh.new()
	star_mesh.radius = 0.035
	star_mesh.height = 0.07
	star_mesh.radial_segments = 6
	star_mesh.rings = 3
	var rng := RandomNumberGenerator.new()
	rng.seed = 94721
	for index in range(100):
		var star := MeshInstance3D.new()
		star.mesh = star_mesh
		star.material_override = star_material
		star.position = Vector3(rng.randf_range(-28, 28), rng.randf_range(-10, 20), rng.randf_range(12, 35))
		$DepthMarkers.add_child(star)


func _capture_and_quit() -> void:
	await RenderingServer.frame_post_draw
	var result := get_viewport().get_texture().get_image().save_png(capture_path)
	if result != OK:
		push_error("Screenshot save failed: %s" % error_string(result))
		get_tree().quit(1)
	else:
		print("PIPELINE_RENDER_PASS: " + capture_path)
		get_tree().quit()
