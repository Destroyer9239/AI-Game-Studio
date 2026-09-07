extends Node3D
signal state_changed(kind: String, state: Dictionary)
var weather := "clear"
var hour := 17.0
var wetness := 0.0
var indoors := false
var clock_running := false
var focus := Vector3.ZERO
var profiles: Dictionary
var environment: Environment
var sun: DirectionalLight3D
var rain: GPUParticles3D
var sky_kind := "procedural"

func _ready() -> void:
	profiles = JSON.parse_string(FileAccess.get_file_as_string("res://world/weather_profiles.json"))
	environment=Environment.new()
	environment.background_mode=Environment.BG_SKY
	environment.sky=load("res://scripts/sky_factory.gd").create("procedural")
	var sky := environment.sky.sky_material as ProceduralSkyMaterial
	sky.sky_top_color=Color(.035,.11,.23)
	sky.sky_horizon_color=Color(.25,.37,.48)
	sky.ground_bottom_color=Color(.025,.035,.05)
	sky.ground_horizon_color=Color(.14,.19,.23)
	environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color=Color(.48,.61,.76)
	environment.ambient_light_energy=.75
	environment.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	environment.tonemap_mode=Environment.TONE_MAPPER_FILMIC
	environment.ssao_enabled=true
	environment.ssr_enabled=true
	environment.glow_enabled=true
	environment.volumetric_fog_enabled=true
	var world:=WorldEnvironment.new()
	world.environment=environment
	add_child(world)
	sun=DirectionalLight3D.new()
	sun.shadow_enabled=true
	sun.rotation_degrees.y=-25
	add_child(sun)
	rain=GPUParticles3D.new()
	rain.amount=1800
	rain.lifetime=1.5
	rain.visibility_aabb=AABB(Vector3(-18,-5,-18),Vector3(36,30,36))
	var process:=ParticleProcessMaterial.new()
	process.emission_shape=ParticleProcessMaterial.EMISSION_SHAPE_BOX
	process.emission_box_extents=Vector3(16,1,16)
	process.direction=Vector3(0,-1,0)
	process.initial_velocity_min=12
	process.initial_velocity_max=18
	process.gravity=Vector3(1,-4,0)
	rain.process_material=process
	var mesh:=BoxMesh.new()
	mesh.size=Vector3(.012,.3,.012)
	var material:=StandardMaterial3D.new()
	material.albedo_color=Color(.35,.55,.7,.5)
	material.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA
	mesh.material=material
	rain.draw_pass_1=mesh
	add_child(rain)
	apply_state()

func set_weather(value: String) -> bool:
	if not profiles.has(value): return false
	weather=value
	apply_state()
	state_changed.emit("weather",snapshot())
	return true

func set_hour(value: float) -> void:
	hour=fposmod(value,24.0)
	apply_state()
	state_changed.emit("time",snapshot())

func snapshot() -> Dictionary:
	return {"weather":weather,"hour":hour,"wetness":wetness,"indoors":indoors,"sky_kind":sky_kind,"wind":profiles[weather].wind,"rain":profiles[weather].rain}

func set_sky(kind: String, texture: Texture2D=null, hdr_lighting:=false) -> void:
	environment.sky=load("res://scripts/sky_factory.gd").create(kind,texture)
	sky_kind=("HDR_lighting" if hdr_lighting else "SDR_artistic") if kind=="panorama" else kind

func apply_state() -> void:
	var profile: Dictionary=profiles[weather]
	var daylight:=maxf(0,sin((hour-6)*PI/12))
	environment.ambient_light_energy=.35+daylight*.65
	sun.rotation_degrees.x=(hour-6)*-15
	sun.light_energy=daylight*1.6*(1-float(profile.cloud)*.7)
	sun.light_color=Color(1,.79,.55).lerp(Color(.65,.77,.9),float(profile.cloud))
	environment.volumetric_fog_density=profile.fog
	environment.background_energy_multiplier=.2+daylight*.6
	if environment.sky.sky_material is ProceduralSkyMaterial:
		var sky := environment.sky.sky_material as ProceduralSkyMaterial
		sky.sky_top_color=Color(.035,.11,.23).lerp(Color(.11,.15,.20),float(profile.cloud))
		sky.sky_horizon_color=Color(.25,.37,.48).lerp(Color(.16,.20,.24),float(profile.cloud))
	rain.emitting=float(profile.rain)>0 and not indoors
	rain.amount_ratio=profile.rain
	for light in get_tree().get_nodes_in_group("city_lights"):
		light.light_energy=lerpf(1.6,.15,daylight)

func _process(delta: float) -> void:
	if clock_running: hour=fposmod(hour+delta*.02,24)
	wetness=move_toward(wetness,float(profiles[weather].wetness),delta*.12)
	rain.position=focus+Vector3(0,16,0)
	var materials: Dictionary=load("res://scripts/city_chunk.gd").shared
	if materials.has("road"):
		materials.road.roughness=lerpf(.87,.16,wetness)
		materials.road.albedo_color=Color(.055,.065,.075).lerp(Color(.018,.026,.035),wetness)
	apply_state()
