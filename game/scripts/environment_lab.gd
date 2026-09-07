extends Node3D
## Small repeatable rendering lab. CLI captures metrics after shader warm-up.
const LEVELS := ["LOW", "MEDIUM", "HIGH", "ULTRA", "CINEMATIC"]
var quality := 2
var count := 100
var frame := 0
var capture := ""
var report := ""
var samples: Array[float] = []
var camera: Camera3D
var world_environment: Environment
var hud: Label
var started_usec := 0
var previous_usec := 0
var sample_start_usec := 0
var finishing := false

func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--quality="):
			quality = LEVELS.find(arg.trim_prefix("--quality=").to_upper())
		elif arg.begins_with("--instances="):
			count = clampi(arg.trim_prefix("--instances=").to_int(), 0, 20000)
		elif arg.begins_with("--capture="):
			capture = arg.trim_prefix("--capture=")
		elif arg.begins_with("--report="):
			report = arg.trim_prefix("--report=")
	if quality < 0:
		set_process(false)
		push_error("Unknown quality level")
		get_tree().quit(1)
		return
	var module: Node = load("res://scenes/assets/environment_probe.tscn").instantiate()
	add_child(module)
	for child in module.find_children("*","MeshInstance3D",true,false):
		for surface in range(child.mesh.get_surface_count()):
			var material: Material = child.mesh.surface_get_material(surface)
			if material is BaseMaterial3D:
				material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	world_environment = Environment.new()
	world_environment.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sky_material := PhysicalSkyMaterial.new()
	sky_material.energy_multiplier = 0.55
	sky_material.ground_color = Color(.025,.04,.06)
	sky.sky_material = sky_material
	world_environment.sky = sky
	world_environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	world_environment.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	world_environment.ambient_light_energy = 0.6
	world_environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	var world := WorldEnvironment.new()
	world.environment = world_environment
	add_child(world)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-35,-25,0)
	sun.light_color = Color(1,.84,.65)
	sun.light_energy = 1.4
	sun.shadow_enabled = true
	add_child(sun)
	var fill := OmniLight3D.new()
	fill.position = Vector3(0,2,1)
	fill.light_color = Color(.05,.6,1)
	fill.light_energy = 2
	fill.omni_range = 8
	fill.shadow_enabled = quality >= 2
	add_child(fill)
	var probe := ReflectionProbe.new()
	probe.position = Vector3(0,1,0)
	probe.size = Vector3(12,6,12)
	probe.box_projection = true
	add_child(probe)
	var props := MultiMeshInstance3D.new()
	var multimesh := MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	var mesh := BoxMesh.new()
	mesh.size = Vector3(.28,.4,.28)
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(.1,.14,.18)
	mat.metallic = .85
	mat.roughness = .25
	mesh.material = mat
	multimesh.mesh = mesh
	multimesh.instance_count = count
	for i in range(count):
		multimesh.set_instance_transform(i,Transform3D(Basis.IDENTITY,Vector3(-3.5+(i%20)*.35,.2,-2.6+float(i/20)*.38)))
	props.multimesh = multimesh
	add_child(props)
	var particles := GPUParticles3D.new()
	particles.amount = 64
	particles.position = Vector3(0,2,0)
	var process := ParticleProcessMaterial.new()
	process.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_BOX
	process.emission_box_extents = Vector3(4,1,3)
	process.gravity = Vector3(0,-.03,0)
	process.scale_min = .015
	process.scale_max = .03
	particles.process_material = process
	particles.draw_pass_1 = SphereMesh.new()
	particles.emitting = quality >= 1
	add_child(particles)
	var decal := Decal.new()
	decal.position = Vector3(2,.01,1)
	decal.size = Vector3(1,.1,1)
	decal.texture_albedo = load("res://assets/textures/lab_warning.png")
	add_child(decal)
	camera = Camera3D.new()
	add_child(camera)
	camera.position = Vector3(7,4.8,8)
	camera.look_at(Vector3(0,1,0))
	camera.current = true
	camera.fov = 50
	var canvas := CanvasLayer.new()
	add_child(canvas)
	hud = Label.new()
	hud.position = Vector2(24,20)
	hud.add_theme_font_size_override("font_size",20)
	canvas.add_child(hud)
	var concept := Sprite2D.new()
	concept.texture = load("res://assets/textures/strake_concept.png")
	concept.position = Vector2(1040,24)
	concept.centered = false
	concept.scale = Vector2.ONE * (216.0/concept.texture.get_width())
	canvas.add_child(concept)
	apply_quality()
	started_usec = Time.get_ticks_usec()
	previous_usec = started_usec

func apply_quality() -> void:
	world_environment.ssao_enabled = quality >= 1
	world_environment.ssil_enabled = quality >= 3
	world_environment.ssr_enabled = quality >= 2
	world_environment.glow_enabled = quality >= 1
	world_environment.volumetric_fog_enabled = quality >= 2
	world_environment.volumetric_fog_density = .012 if quality >= 2 else 0.0
	get_viewport().use_taa = quality >= 3
	get_viewport().msaa_3d = Viewport.MSAA_4X if quality >= 2 else Viewport.MSAA_DISABLED
	if quality == 4:
		get_viewport().msaa_3d = Viewport.MSAA_8X
	world_environment.ssr_max_steps = 128 if quality >= 3 else 64
	hud.text = "INDUSTRIAL MATERIAL LAB / " + LEVELS[quality] + "\n1–5 quality • arrows orbit • Esc exit\n4K concrete / authored steel / " + str(count) + " instanced props"

func _process(delta: float) -> void:
	frame += 1
	var current_usec := Time.get_ticks_usec()
	if frame > 120 and current_usec-started_usec > 2000000:
		if sample_start_usec == 0:
			sample_start_usec = current_usec
		samples.append(float(current_usec-previous_usec)/1000.0)
	previous_usec = current_usec
	if Input.is_physical_key_pressed(KEY_LEFT):
		camera.position = camera.position.rotated(Vector3.UP,delta*.4)
	if Input.is_physical_key_pressed(KEY_RIGHT):
		camera.position = camera.position.rotated(Vector3.UP,-delta*.4)
	camera.look_at(Vector3(0,1,0))
	if samples.size() >= 240 and current_usec-sample_start_usec >= 2000000 and not finishing and (not capture.is_empty() or not report.is_empty()):
		finishing = true
		finish()

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed:
		if event.keycode >= KEY_1 and event.keycode <= KEY_5:
			quality = event.keycode - KEY_1
			apply_quality()
		elif event.keycode == KEY_ESCAPE:
			get_tree().quit()

func finish() -> void:
	await RenderingServer.frame_post_draw
	if not capture.is_empty():
		if get_viewport().get_texture().get_image().save_png(capture) != OK:
			push_error("Lab capture failed")
			get_tree().quit(1)
			return
	samples.sort()
	var total := 0.0
	for value in samples:
		total += value
	var data := {"quality":LEVELS[quality], "instances":count,
		"renderer":RenderingServer.get_current_rendering_method(),
		"adapter":RenderingServer.get_video_adapter_name(),
		"sample_count":samples.size(), "mean_frame_ms":total/samples.size(),
		"p95_frame_ms":samples[int(samples.size()*.95)],
		"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		"rendered_objects":Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
		"video_memory_bytes":Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED),
		"elapsed_seconds":float(Time.get_ticks_usec()-started_usec)/1000000,
		"notes":"At least 2 seconds/120 frames warm-up and 2 seconds/240 samples; CPU wall intervals, not isolated GPU timing; small scene, not city capacity"}
	if not report.is_empty():
		var file := FileAccess.open(report,FileAccess.WRITE)
		if file == null:
			push_error("Cannot write benchmark report")
			get_tree().quit(1)
			return
		file.store_string(JSON.stringify(data,"  "))
	print("ENVIRONMENT_LAB_PASS: "+JSON.stringify(data))
	get_tree().quit()
