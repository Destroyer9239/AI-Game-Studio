extends Node3D
## Independent crossfaded layers; replace streams without changing zone logic.
var layers: Dictionary={}
var targets: Dictionary={}
var district := "industrial"
var indoors := false
var weather := "clear"
var hour := 17.0
var one_shot: AudioStreamPlayer
var timer := 0.0
var next_event := 23.0
var rng := RandomNumberGenerator.new()
var zones: Dictionary

func _ready() -> void:
	rng.seed=24819
	zones=JSON.parse_string(FileAccess.get_file_as_string("res://world/audio_zones.json"))
	for id in ["wind","city","rain","interior"]:
		var player:=AudioStreamPlayer.new()
		var stream:=load("res://assets/audio/"+id+".wav") as AudioStreamWAV
		stream=stream.duplicate()
		stream.loop_mode=AudioStreamWAV.LOOP_FORWARD
		stream.loop_end=88200
		player.stream=stream
		player.volume_db=-70
		add_child(player)
		player.play()
		layers[id]=player
	one_shot=AudioStreamPlayer.new()
	one_shot.stream=load("res://assets/audio/event.wav")
	one_shot.volume_db=-15
	add_child(one_shot)
	update_targets()

func on_environment(_kind: String,state: Dictionary) -> void:
	weather=state.weather
	hour=state.hour
	indoors=state.indoors
	update_targets()

func set_zone(value: String,interior: bool) -> void:
	district=value
	indoors=interior
	update_targets()

func update_listener(position: Vector3) -> void:
	var zone: Dictionary=zones.default
	for candidate in zones.zones:
		var c: Array=candidate.center
		var e: Array=candidate.half_extents
		var bounds:=AABB(Vector3(c[0]-e[0],c[1]-e[1],c[2]-e[2]),Vector3(e[0]*2,e[1]*2,e[2]*2))
		if bounds.has_point(position): zone=candidate
	set_zone(zone.district,zone.interior)

func update_targets() -> void:
	var raining:=weather in ["rain","heavy_rain","storm"]
	targets={"wind":-35.0 if indoors else -14.0,"city":-30.0 if indoors else -16.0 if district=="industrial" else -22.0,
		"rain":-27.0 if raining and indoors else -9.0 if raining else -70.0,"interior":-15.0 if indoors else -70.0}
	if hour<6 or hour>21: targets.city-=5

func trigger_event(_event: String) -> void:
	one_shot.play()

func _process(delta: float) -> void:
	for id in layers:
		layers[id].volume_db=move_toward(layers[id].volume_db,float(targets[id]),delta*18)
	timer+=delta
	if timer>next_event:
		timer=0
		next_event=rng.randf_range(18,34)
		trigger_event("distant_machinery")

func _exit_tree() -> void:
	for player in layers.values(): player.stop()
	if one_shot: one_shot.stop()
