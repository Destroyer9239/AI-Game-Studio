extends Node3D
var streamer: Node3D
var camera: Camera3D
var capture := ""
var elapsed := 0.0
var saving := false
func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--capture="): capture=arg.trim_prefix("--capture=")
	streamer=load("res://scripts/world_streamer.gd").new()
	add_child(streamer)
	streamer.update_focus(Vector3.ZERO)
	var env := Environment.new()
	env.background_mode=Environment.BG_SKY
	env.sky=load("res://scripts/sky_factory.gd").create("procedural")
	env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
	env.ssao_enabled=true
	env.ssr_enabled=true
	env.glow_enabled=true
	env.volumetric_fog_enabled=true
	env.volumetric_fog_density=.004
	var world := WorldEnvironment.new()
	world.environment=env
	add_child(world)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees=Vector3(-35,-25,0)
	sun.light_energy=1.7
	sun.light_color=Color(1,.83,.65)
	sun.shadow_enabled=true
	add_child(sun)
	camera=Camera3D.new()
	camera.position=Vector3(48,38,48)
	camera.fov=55
	add_child(camera)
	camera.look_at(Vector3(0,4,0))
	camera.current=true
	var layer:=CanvasLayer.new()
	add_child(layer)
	var label:=Label.new()
	label.position=Vector2(24,20)
	label.text="CINDER EXCHANGE / BLOCK GENERATOR\n4 buildings / 3 archetypes / bounded streaming cells"
	label.add_theme_font_size_override("font_size",20)
	layer.add_child(label)
func _process(delta: float) -> void:
	elapsed+=delta
	if elapsed>4 and streamer.pending.is_empty() and not capture.is_empty() and not saving:
		saving=true
		await RenderingServer.frame_post_draw
		if get_viewport().get_texture().get_image().save_png(capture)!=OK:
			push_error("City capture failed")
			get_tree().quit(1)
			return
		print("CITY_PREVIEW_PASS: ",streamer.metrics())
		get_tree().quit()
