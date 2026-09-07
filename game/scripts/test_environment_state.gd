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
	print("ENVIRONMENT_STATE_TESTS_PASS: ",checks," checks")
	director.queue_free();audio.queue_free()
	await process_frame
	await create_timer(.15).timeout
	quit()
