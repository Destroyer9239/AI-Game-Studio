extends Node3D
## A bounded reusable cell. Four designed buildings only in the central block.
@export var cell_id := "center"
@export var building_scenes: Array[PackedScene] = []
static var shared: Dictionary = {}
var persistent_state: Dictionary = {}
var cell_data: Dictionary
var terminal: Node
var worker: Node
var nav_obstacles: Array[AABB]=[]

static func mat(key: String, color: Color, metallic: float = 0, roughness: float = .7) -> StandardMaterial3D:
	if not shared.has(key):
		var material := StandardMaterial3D.new()
		material.albedo_color = color
		material.metallic = metallic
		material.roughness = roughness
		material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
		shared[key] = material
	return shared[key]

func box(label: String, pos: Vector3, size: Vector3, material: Material, collision := false) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.name = label
	var mesh := BoxMesh.new()
	mesh.size = size
	node.mesh = mesh
	node.material_override = material
	node.position = pos
	add_child(node)
	if collision:
		nav_obstacles.append(AABB(pos-size*.5,size))
		var body := StaticBody3D.new()
		var shape := CollisionShape3D.new()
		var bounds := BoxShape3D.new()
		bounds.size = size
		shape.shape = bounds
		body.add_child(shape)
		node.add_child(body)
	return node

func multibox(label: String, size: Vector3, material: Material, offsets: Array) -> MultiMeshInstance3D:
	## Repeated collision-less street furniture: identical box and material, so
	## one instanced submission replaces one draw call per prop.
	var node := MultiMeshInstance3D.new()
	node.name = label
	var mesh := BoxMesh.new()
	mesh.size = size
	var batch := MultiMesh.new()
	batch.transform_format = MultiMesh.TRANSFORM_3D
	batch.mesh = mesh
	batch.instance_count = offsets.size()
	for index in offsets.size():
		batch.set_instance_transform(index, Transform3D(Basis(), offsets[index]))
	node.multimesh = batch
	node.material_override = material
	add_child(node)
	return node

func _ready() -> void:
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://world/city_block.json"))
	for value in spec.cells:
		if value.id == cell_id:
			cell_data = value
	assert(cell_data != null, "Unknown cell")
	var pavement := mat("pavement",Color(.29,.31,.32),0,.83)
	if pavement.albedo_texture == null:
		pavement.albedo_texture = load("res://assets/textures/hero_surfaces/aggregate.png")
		pavement.uv1_triplanar=true
		pavement.uv1_world_triplanar=true
		pavement.uv1_scale = Vector3(.5,.5,.5)
		pavement.normal_enabled=true
		pavement.normal_texture=load("res://assets/textures/hero_surfaces/normal.png")
		pavement.roughness_texture=load("res://assets/textures/hero_surfaces/roughness.png")
	box("Ground",Vector3(0,-.25,0),Vector3(64,.5,64),mat("ground",Color(.12,.14,.15)),true)
	box("Road",Vector3(0,.015,0),Vector3(64,.03,8),mat("road",Color(.055,.065,.075),0,.87))
	shared.road.normal_enabled=true;shared.road.normal_texture=pavement.normal_texture
	shared.road.uv1_triplanar=true;shared.road.uv1_world_triplanar=true;shared.road.uv1_scale=Vector3(.5,.5,.5)
	var steel := mat("steel",Color(.055,.075,.09),.8,.3)
	var lamp_material := mat("lamp_emitter",Color(.8,.62,.34),0,.4)
	lamp_material.emission_enabled=true;lamp_material.emission=Color(1,.65,.28);lamp_material.emission_energy_multiplier=2
	var posts:Array[Vector3]=[];var arms:Array[Vector3]=[];var heads:Array[Vector3]=[];var drains:Array[Vector3]=[]
	for side in [-1,1]:
		box("Sidewalk",Vector3(0,.12,side*6),Vector3(64,.24,4),pavement,true)
		box("Curb",Vector3(0,.16,side*4.1),Vector3(64,.32,.2),mat("curb",Color(.52,.5,.44)),true)
		for x in [-24,-8,8,24]:
			posts.append(Vector3(x,2.9,side*7.3))
			arms.append(Vector3(x,5.7,side*6.5))
			heads.append(Vector3(x,5.58,side*5.75))
			drains.append(Vector3(x,.255,side*4.6))
			var light := OmniLight3D.new()
			light.position = Vector3(x,5.4,side*5.8)
			light.light_color = Color(1,.73,.42)
			light.light_energy = .6
			light.omni_range = 9
			light.distance_fade_enabled = true
			light.distance_fade_begin = 35
			light.distance_fade_length = 15
			light.add_to_group("city_lights")
			add_child(light)
	multibox("LampPosts",Vector3(.14,5.8,.14),steel,posts)
	multibox("LampArms",Vector3(.12,.12,1.7),steel,arms)
	multibox("LampHeads",Vector3(.4,.09,.75),lamp_material,heads)
	multibox("Drains",Vector3(.7,.025,.5),steel,drains)
	var lane_marks:Array[Vector3]=[]
	for x in range(-30,31,6):lane_marks.append(Vector3(x,.04,0))
	multibox("LaneMarks",Vector3(2.5,.02,.1),mat("paint",Color(.8,.68,.34),0,.8),lane_marks)
	if cell_id=="center":
		# Composed service-edge clusters leave a continuous pedestrian route.
		var paint:=mat("service_paint",Color(.45,.22,.07),0,.65)
		var stripes:Array[Vector3]=[];var feet:Array[Vector3]=[];var bands:Array[Vector3]=[];var joints:Array[Vector3]=[]
		for side in [-1,1]:
			for x in [-27,-11,11,27]:
				box("Bollard",Vector3(x,.7,side*7.6),Vector3(.18,.92,.18),paint,true)
				stripes.append(Vector3(x,.96,side*7.6))
			for x in [-12,12]:
				box("BenchSeat",Vector3(x,.72,side*7.4),Vector3(2.3,.12,.55),shared.steel,true)
				for dx in [-.8,.8]:feet.append(Vector3(x+dx,.46,side*7.4))
			for x in [-24,24]:
				box("ServiceCrate",Vector3(x,.75,side*10),Vector3(1.4,1.5,1.2),paint,true)
				bands.append(Vector3(x,.76,side*10))
			for x in range(-30,31,2):joints.append(Vector3(x,.244,side*6))
		multibox("BollardStripes",Vector3(.19,.12,.19),shared.curb,stripes)
		multibox("BenchFeet",Vector3(.12,.44,.4),shared.steel,feet)
		multibox("CrateBands",Vector3(1.43,.13,1.23),shared.steel,bands)
		multibox("PavementJoints",Vector3(.025,.007,3.8),shared.steel,joints)
		box("UtilityCabinet",Vector3(8,.94,6),Vector3(.8,1.4,.7),paint,true)
		box("UtilityVent",Vector3(8,1.15,5.64),Vector3(.6,.35,.035),shared.steel)
		var crossings:Array[Vector3]=[]
		for x in [-28,28]:
			for z in [-2,-1,0,1,2]:crossings.append(Vector3(x,.045,z))
		multibox("Crosswalks",Vector3(2,.016,.5),shared.paint,crossings)
		for side in [-1,1]:
			box("ShelterRoof",Vector3(0,3,side*6),Vector3(4.2,.2,3),shared.steel,true)
			for x in [-1.8,1.8]:
				box("ShelterPost",Vector3(x,1.5,side*7),Vector3(.1,3,.1),shared.steel,true)
		var machine:=AudioStreamPlayer3D.new()
		machine.stream=load("res://assets/audio/city.wav")
		machine.position=Vector3(-16,8,-17)
		machine.volume_db=-20
		machine.unit_size=5
		machine.max_distance=24
		add_child(machine)
		machine.finished.connect(machine.play)
		machine.play()
		terminal=load("res://scripts/studio_terminal.gd").new()
		terminal.position=Vector3(0,.95,-6.6)
		add_child(terminal)
		var runtime:=get_tree().get_first_node_in_group("studio_runtime")
		if runtime:
			terminal.activated.connect(runtime.on_terminal)
			worker=load("res://scripts/studio_npc.gd").new()
			worker.position=Vector3(-20,.3,6)
			add_child(worker)
			runtime.director.state_changed.connect(worker.on_environment)
			worker.on_environment("weather",runtime.director.snapshot())
	for b in cell_data.buildings:
		var packed: PackedScene
		for candidate in building_scenes:
			if candidate.resource_path.get_file().get_basename() == b.asset:
				packed = candidate
		assert(packed != null, "Missing preloaded building dependency")
		var building: Node3D = packed.instantiate()
		building.name = b.id
		building.position = Vector3(b.position[0],b.position[1],b.position[2])
		building.rotation_degrees.y = b.yaw
		add_child(building)
		var sign := Label3D.new()
		sign.text = {"market_a":"CINDER / EXCHANGE", "relay_a":"RELAY 07"}.get(b.id,"CINDER / WORKS")
		sign.font_size = 48
		sign.pixel_size = .008
		sign.position = building.position + Vector3(0,3.6,0) + Vector3.FORWARD.rotated(Vector3.UP,deg_to_rad(b.yaw))*float(b.front_offset)
		sign.rotation_degrees.y = b.yaw+180
		add_child(sign)
	# One-meter navigation grid excludes expanded prop footprints for capsule clearance.
	var region := NavigationRegion3D.new()
	var navigation := NavigationMesh.new()
	var vertices:=PackedVector3Array()
	for z in range(-8,9):
		for x in range(-32,33):vertices.append(Vector3(x,.3,z))
	navigation.set_vertices(vertices)
	for z in range(16):
		for x in range(64):
			var center:=Vector3(x-31.5,.3,z-7.5)
			var blocked:=false
			for bounds in nav_obstacles:
				if bounds.position.y+bounds.size.y<.4 or bounds.position.y>2.1:continue
				if absf(center.x-bounds.get_center().x)<bounds.size.x*.5+1 and absf(center.z-bounds.get_center().z)<bounds.size.z*.5+1:blocked=true;break
			if not blocked:
				var a:=z*65+x
				navigation.add_polygon(PackedInt32Array([a,a+1,a+66,a+65]))
	region.navigation_mesh = navigation
	add_child(region)
	set_meta("ready_for_streaming",true)

func capture_state() -> Dictionary:
	var result:=persistent_state.duplicate(true)
	if terminal:result["terminal"]=terminal.snapshot()
	if worker:result["worker"]=worker.snapshot()
	return result

func restore_state(state: Dictionary) -> void:
	persistent_state = state.duplicate(true)
	if terminal and state.has("terminal"):terminal.restore(state.terminal)
	if worker and state.has("worker"):worker.restore(state.worker)

func _exit_tree() -> void:
	for child in find_children("*","AudioStreamPlayer3D",true,false):
		child.stop()
