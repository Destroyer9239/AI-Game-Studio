extends Node3D
var streamer: Node3D
var director: Node3D
var ambience: Node3D
var player: CharacterBody3D
var events: Node
var objective_model=preload("res://scripts/studio_objective.gd").new()
var objective:="RESTORE SERVICE LINK"
var objective_state:="ACTIVE"
var hud: Label
var elapsed:=0.0
var capture:=""
var report:=""
var capture_done:=false
var ready_player:=false
var quality:=2
var samples: Array[float]=[]
var last_tick:=0
var vehicle_hooks:={"enter_requested":false,"active_vehicle_id":""}

func _ready() -> void:
	add_to_group("studio_runtime")
	events=load("res://scripts/studio_events.gd").new();add_child(events)
	events.world_event.connect(objective_model.consume)
	objective_model.activate()
	director=load("res://scripts/environment_director.gd").new();add_child(director)
	ambience=load("res://scripts/ambient_director.gd").new();add_child(ambience)
	director.state_changed.connect(ambience.on_environment)
	director.state_changed.connect(func(kind,state):events.publish(kind,state))
	streamer=load("res://scripts/world_streamer.gd").new();add_child(streamer)
	streamer.chunk_loaded.connect(func(id):events.publish("chunk_loaded",{"id":id}))
	streamer.chunk_unloaded.connect(func(id):events.publish("chunk_unloaded",{"id":id}))
	player=load("res://scripts/studio_player.gd").new();player.position=Vector3(0,.35,-3);player.enabled=false;add_child(player)
	streamer.update_focus(player.position)
	var layer:=CanvasLayer.new();add_child(layer);hud=Label.new();hud.position=Vector2(20,18);hud.add_theme_font_size_override("font_size",18);layer.add_child(hud)
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--capture="):capture=arg.trim_prefix("--capture=")
		elif arg.begins_with("--report="):report=arg.trim_prefix("--report=")
		elif arg.begins_with("--weather="):director.set_weather(arg.trim_prefix("--weather="))
		elif arg.begins_with("--quality="):quality=clampi(arg.trim_prefix("--quality=").to_int(),0,4)
		elif arg=="--character-inspection":
			player.position=Vector3(-5,.35,2)
			player.camera.look_at(Vector3(-15,1.3,6))
		elif arg=="--inspection":
			player.position=Vector3(22,.35,6)
			player.camera.look_at(Vector3(-14,2,-1))
	apply_quality()
	last_tick=Time.get_ticks_usec()

func apply_quality() -> void:
	director.environment.ssao_enabled=quality>=1
	director.environment.ssr_enabled=quality>=2
	director.environment.ssil_enabled=quality>=3
	director.environment.glow_enabled=quality>=1
	director.environment.volumetric_fog_enabled=quality>=2
	get_viewport().msaa_3d=Viewport.MSAA_8X if quality==4 else Viewport.MSAA_4X if quality>=2 else Viewport.MSAA_DISABLED
	get_viewport().use_taa=quality>=3
	director.rain.amount=600 if quality<2 else 1800

func on_terminal(id: String) -> void:
	events.publish("service_activated",{"id":id})
	objective_state=objective_model.state
	objective="SERVICE LINK RESTORED"
	events.publish("objective_complete",{"id":id})
	ambience.trigger_event("service_online")

func save_game(file: String="user://studio_block_save.json") -> Error:
	for id in streamer.loaded:streamer.states[id]=streamer.loaded[id].capture_state()
	return load("res://scripts/studio_save.gd").save_state(file,{"player":[player.position.x,player.position.y,player.position.z],"yaw":player.rotation.y,"chunks":streamer.states,"objective":objective_state,"environment":director.snapshot(),"settings":{"quality":quality}})

func load_game(file: String="user://studio_block_save.json") -> bool:
	var state: Dictionary=load("res://scripts/studio_save.gd").load_state(file)
	if not load("res://scripts/studio_save.gd").valid_world(state):return false
	player.position=Vector3(state.player[0],state.player[1],state.player[2]);player.rotation.y=state.get("yaw",0);player.velocity=Vector3.ZERO
	streamer.states=state.chunks
	for id in streamer.loaded:streamer.loaded[id].restore_state(streamer.states.get(id,{}))
	objective_state=state.objective;objective_model.state=objective_state
	objective_model.progress=1 if objective_state=="COMPLETE" else 0
	objective="SERVICE LINK RESTORED" if objective_state=="COMPLETE" else "RESTORE SERVICE LINK"
	director.set_weather(state.environment.weather);director.set_hour(state.environment.hour);director.wetness=state.environment.wetness
	quality=state.get("settings",{}).get("quality",2);apply_quality()
	streamer.update_focus(player.position)
	events.publish("save_loaded",{})
	return true

func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:return
	match event.keycode:
		KEY_R:director.set_weather("rain" if director.weather=="clear" else "clear")
		KEY_T:director.set_hour(22 if director.hour<20 else 12)
		KEY_F5:
			if save_game()!=OK:push_error("Save failed")
		KEY_F9:load_game()
		KEY_1,KEY_2,KEY_3,KEY_4,KEY_5:
			quality=event.keycode-KEY_1;apply_quality()

func _process(delta: float) -> void:
	elapsed+=delta
	var now:=Time.get_ticks_usec()
	if elapsed>2:samples.append(float(now-last_tick)/1000)
	last_tick=now
	if samples.size()>10000:samples.pop_front()
	streamer.update_focus(player.position)
	if not ready_player and streamer.loaded.has("center"):
		ready_player=true;player.enabled=true
	if player.position.y< -10:player.position=Vector3(0,.5,-3);player.velocity=Vector3.ZERO
	director.focus=player.position
	ambience.active_cells=streamer.loaded.keys()
	ambience.update_listener(player.position)
	director.indoors=ambience.indoors
	hud.text="CINDER EXCHANGE / "+objective+"\nWASD move • click/mouse look • E interact • Space jump\nR rain • T day/night • F5 save / F9 load • 1–5 quality • Esc release mouse\nCells %d • NPCs %d • FPS %d • wetness %.2f • %s"%[streamer.loaded.size(),get_tree().get_nodes_in_group("npcs").size(),Engine.get_frames_per_second(),director.wetness,director.weather]
	if elapsed>6 and not capture.is_empty() and not capture_done and ready_player:
		capture_done=true
		await RenderingServer.frame_post_draw
		if get_viewport().get_texture().get_image().save_png(capture)!=OK:push_error("Playable capture failed");get_tree().quit(1);return
		var data:=metrics()
		if not report.is_empty():
			var file:=FileAccess.open(report,FileAccess.WRITE);file.store_string(JSON.stringify(data,"  "))
		print("PLAYABLE_PREVIEW_PASS: ",data)
		# Let audio and navigation servers release cell-owned resources before exit.
		set_process(false)
		streamer.queue_free();ambience.queue_free()
		await get_tree().process_frame
		await get_tree().create_timer(.3).timeout
		get_tree().quit()

func metrics() -> Dictionary:
	var ordered:=samples.duplicate();ordered.sort();var total:=0.0
	for value in ordered:total+=value
	return {"quality":quality,"frame_ms_mean":total/maxi(1,ordered.size()),"frame_ms_p95":ordered[int(ordered.size()*.95)] if not ordered.is_empty() else 0,"samples":ordered.size(),"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),"triangles":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),"objects":Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),"video_memory_bytes":Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED),"chunks":streamer.metrics(),"npcs":get_tree().get_nodes_in_group("npcs").size(),"lights":get_tree().get_nodes_in_group("city_lights").size(),"materials_shared":load("res://scripts/city_chunk.gd").shared.size(),"note":"CPU observed frame intervals; prototype block, not a large-city guarantee"}
