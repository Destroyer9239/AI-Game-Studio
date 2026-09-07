extends SceneTree
var checks:=0
func _initialize() -> void: call_deferred("run")
func check(value: bool,label: String) -> void:
	assert(value,label)
	checks+=1
func run() -> void:
	var director=load("res://scripts/environment_director.gd").new()
	root.add_child(director)
	var audio=load("res://scripts/ambient_director.gd").new()
	root.add_child(audio)
	director.state_changed.connect(audio.on_environment)
	check(not director.set_weather("invalid"),"reject unknown weather")
	check(director.set_weather("rain"),"rain accepted")
	check(audio.weather=="rain","weather/audio event connection")
	director._process(2.0)
	check(director.wetness>0,"wetness transition")
	check(director.rain.emitting,"precipitation enabled")
	check(audio.targets.rain> -20,"rain audio layer")
	audio.set_zone("industrial",true)
	check(audio.targets.rain< -20 and audio.targets.interior> -20,"interior response")
	director.set_hour(27)
	check(director.hour==3,"clock wraps")
	check(director.sun.light_energy==0,"night sun off")
	director.set_weather("clear")
	director._process(10)
	check(director.wetness==0 and not director.rain.emitting,"dry transition")
	check(audio.layers.size()==4,"independent audio layers")
	audio.update_listener(Vector3(0,1,-6))
	check(audio.indoors,"spatial shelter zone")
	audio.update_listener(Vector3(20,1,0))
	check(not audio.indoors,"spatial exterior zone")
	audio.update_listener(Vector3(0,1,6));audio._process(1)
	check(audio.indoors and audio.muffler.cutoff_hz==1500,"second shelter filters exterior layers")
	audio.active_cells=[];audio.update_listener(Vector3(0,1,6));audio._process(1)
	check(not audio.indoors and audio.muffler.cutoff_hz==18000,"unloaded zone no longer applies")
	# Ambience regression: exactly one player per layer, each on its own looping
	# stream, a crossfade that converges, and no bus or node left behind.
	var streams:={}
	for id in audio.layers:
		var player: AudioStreamPlayer=audio.layers[id]
		check(player.playing,"layer "+id+" plays exactly once")
		check(player.stream.loop_mode==AudioStreamWAV.LOOP_FORWARD,"layer "+id+" loops forward")
		check(not streams.has(player.stream.get_instance_id()),"layer "+id+" owns its own stream copy")
		streams[player.stream.get_instance_id()]=true
	check(root.find_children("*","AudioStreamPlayer",true,false).size()==audio.layers.size()+1,"no orphaned ambience players")
	audio.set_zone("industrial",false)
	for i in range(140):audio._process(.05)
	for id in audio.layers:
		check(is_finite(audio.layers[id].volume_db),"layer "+id+" volume stays finite")
		check(absf(audio.layers[id].volume_db-float(audio.targets[id]))<.01,"layer "+id+" crossfade reaches its exterior target")
	check(audio.muffler.cutoff_hz==18000,"exterior crossfade restores the unfiltered bus")
	var pitches:={}
	for i in range(24):
		audio.trigger_event("distant_machinery")
		check(audio.one_shot.pitch_scale>=.88 and audio.one_shot.pitch_scale<=1.12,"event pitch stays inside its declared range")
		pitches[audio.one_shot.pitch_scale]=true
	check(pitches.size()>1,"event pitch actually varies")
	var second=load("res://scripts/ambient_director.gd").new();root.add_child(second)
	var second_bus: String=second.filter_bus_name
	check(second_bus!=audio.filter_bus_name,"each ambience owns a distinct filter bus")
	second.queue_free();await process_frame;await create_timer(.15).timeout
	check(AudioServer.get_bus_index(second_bus)==-1,"a released ambience frees its bus")
	check(AudioServer.get_bus_index(audio.filter_bus_name)>0,"the surviving ambience keeps its bus")
	var owned_bus: String=audio.filter_bus_name
	print("ENVIRONMENT_STATE_TESTS_PASS: ",checks," checks")
	director.queue_free();audio.queue_free()
	await process_frame
	await create_timer(.15).timeout
	check(AudioServer.get_bus_index(owned_bus)==-1,"owned audio bus released")
	print("ENVIRONMENT_FINAL_PASS: ",checks," checks")
	quit()
