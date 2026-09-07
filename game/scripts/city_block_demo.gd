extends Node3D
var streamer: Node3D
var camera: Camera3D
var capture := ""
var elapsed := 0.0
var saving := false
var director: Node3D
var ambience: Node3D
func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--capture="): capture=arg.trim_prefix("--capture=")
	streamer=load("res://scripts/world_streamer.gd").new()
	add_child(streamer)
	streamer.update_focus(Vector3.ZERO)
	director=load("res://scripts/environment_director.gd").new()
	add_child(director)
	ambience=load("res://scripts/ambient_director.gd").new()
	add_child(ambience)
	director.state_changed.connect(ambience.on_environment)
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--weather="): director.set_weather(arg.trim_prefix("--weather="))
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

func _unhandled_key_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode==KEY_R:
			director.set_weather("rain" if director.weather=="clear" else "clear")
		elif event.keycode==KEY_T:
			director.set_hour(22 if director.hour<20 else 12)
		elif event.keycode==KEY_ESCAPE: get_tree().quit()
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
