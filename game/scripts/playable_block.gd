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
var benchmarking:=false
var gpu_samples: Array[float]=[]
var cpu_render_samples: Array[float]=[]
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
		elif arg=="--benchmark":
			benchmarking=true
			DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_DISABLED)
			Engine.max_fps=0
			RenderingServer.viewport_set_measure_render_time(get_viewport().get_viewport_rid(),true)
		elif arg.begins_with("--hour="):director.set_hour(arg.trim_prefix("--hour=").to_float())
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
	director.rain.amount=[250,700,1800,2400,3000][quality]
	director.sun.shadow_enabled=quality>0
	director.sun.directional_shadow_max_distance=[30.0,45.0,70.0,95.0,120.0][quality]
	get_viewport().scaling_3d_scale=.75 if quality==0 else 1.0

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
	if elapsed>3:
		samples.append(float(now-last_tick)/1000)
		if benchmarking:
			gpu_samples.append(RenderingServer.viewport_get_measured_render_time_gpu(get_viewport().get_viewport_rid()))
			cpu_render_samples.append(RenderingServer.viewport_get_measured_render_time_cpu(get_viewport().get_viewport_rid()))
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
	if elapsed>(12 if benchmarking else 6) and not capture.is_empty() and not capture_done and ready_player:
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

func percentile(ordered: Array[float],fraction: float) -> float:
	if ordered.is_empty():return 0.0
	return ordered[clampi(int(ordered.size()*fraction),0,ordered.size()-1)]

func audio_census() -> Dictionary:
	var nodes:=0
	var playing:=0
	for node in get_tree().root.find_children("*","AudioStreamPlayer3D",true,false)+get_tree().root.find_children("*","AudioStreamPlayer",true,false):
		nodes+=1
		if node.playing:playing+=1
	return {"players":nodes,"playing":playing,"buses":AudioServer.bus_count}

func shadow_casting_lights() -> int:
	var count:=1 if director.sun.shadow_enabled else 0
	for light in get_tree().get_nodes_in_group("city_lights"):
		if light.shadow_enabled:count+=1
	return count

func metrics() -> Dictionary:
	var ordered:=samples.duplicate();ordered.sort()
	var total:=0.0
	for value in ordered:total+=value
	var mean:=total/maxi(1,ordered.size())
	var gpu:=gpu_samples.duplicate();gpu.sort()
	var cpu:=cpu_render_samples.duplicate();cpu.sort()
	return {
		# How the sample was taken. A benchmark run disables vsync and the FPS
		# cap for its own process only; gameplay presets are untouched.
		"quality":quality,"benchmark_uncapped":benchmarking,
		"vsync_mode":DisplayServer.window_get_vsync_mode(),"fps_cap":Engine.max_fps,
		"headless":DisplayServer.get_name()=="headless",
		"viewport_size":[get_viewport().size.x,get_viewport().size.y],
		"preset":{"msaa_3d":get_viewport().msaa_3d,"taa":get_viewport().use_taa,
			"scaling_3d_scale":get_viewport().scaling_3d_scale,
			"ssao":director.environment.ssao_enabled,"ssr":director.environment.ssr_enabled,
			"ssil":director.environment.ssil_enabled,"glow":director.environment.glow_enabled,
			"volumetric_fog":director.environment.volumetric_fog_enabled,
			"sun_shadows":director.sun.shadow_enabled,
			"shadow_max_distance":director.sun.directional_shadow_max_distance,
			"rain_particles":director.rain.amount},
		# Wall-clock frame intervals measured on the main thread.
		"samples":ordered.size(),"frame_ms_mean":mean,
		"frame_ms_median":percentile(ordered,.5),"frame_ms_p95":percentile(ordered,.95),
		"frame_ms_p99":percentile(ordered,.99),
		"frame_ms_min":ordered[0] if not ordered.is_empty() else 0.0,
		"frame_ms_max":ordered[-1] if not ordered.is_empty() else 0.0,
		"fps_mean":1000.0/maxf(mean,.0001),
		# RenderingServer render-only timings; zero unless --benchmark enabled them.
		"cpu_render_ms_mean":average(cpu_render_samples),"cpu_render_ms_p95":percentile(cpu,.95),
		"gpu_render_ms_mean":average(gpu_samples),"gpu_render_ms_p95":percentile(gpu,.95),
		"render_timing_measured":benchmarking,
		# Renderer counters for the captured view.
		"draw_calls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),
		"primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),
		"objects":Performance.get_monitor(Performance.RENDER_TOTAL_OBJECTS_IN_FRAME),
		"video_memory_bytes":Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED),
		"texture_memory_bytes":Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED),
		"buffer_memory_bytes":Performance.get_monitor(Performance.RENDER_BUFFER_MEM_USED),
		"static_memory_bytes":Performance.get_monitor(Performance.MEMORY_STATIC),
		"nodes":Performance.get_monitor(Performance.OBJECT_NODE_COUNT),
		"resources":Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT),
		"process_ms":Performance.get_monitor(Performance.TIME_PROCESS)*1000,
		"physics_ms":Performance.get_monitor(Performance.TIME_PHYSICS_PROCESS)*1000,
		# Scene contents behind those counters.
		"chunks":streamer.metrics(),"npcs":get_tree().get_nodes_in_group("npcs").size(),
		"lights":get_tree().get_nodes_in_group("city_lights").size(),
		"shadow_casting_lights":shadow_casting_lights(),
		"audio":audio_census(),
		"materials_shared":load("res://scripts/city_chunk.gd").shared.size(),
		"weather":director.weather,"hour":director.hour,
		"note":"CPU wall intervals; CPU/GPU render-only times come from RenderingServer viewport measurement and are zero unless --benchmark ran; fixed street camera on a bounded prototype block, not a full-city guarantee"}

func average(values: Array[float]) -> float:
	var total:=0.0
	for value in values:total+=value
	return total/maxi(1,values.size())
