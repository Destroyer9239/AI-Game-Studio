extends Node3D
## A bounded reusable cell. Four designed buildings only in the central block.
@export var cell_id := "center"
@export var building_scenes: Array[PackedScene] = []
static var shared: Dictionary = {}
var persistent_state: Dictionary = {}
var cell_data: Dictionary

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
		var body := StaticBody3D.new()
		var shape := CollisionShape3D.new()
		var bounds := BoxShape3D.new()
		bounds.size = size
		shape.shape = bounds
		body.add_child(shape)
		node.add_child(body)
	return node

func _ready() -> void:
	var spec: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://world/city_block.json"))
	for value in spec.cells:
		if value.id == cell_id:
			cell_data = value
	assert(cell_data != null, "Unknown cell")
	var pavement := mat("pavement",Color(.29,.31,.32),0,.83)
	if pavement.albedo_texture == null:
		pavement.albedo_texture = load("res://assets/textures/industrial_concrete/industrial_concrete_basecolor.png")
		pavement.uv1_scale = Vector3(8,8,8)
	box("Ground",Vector3(0,-.25,0),Vector3(64,.5,64),mat("ground",Color(.12,.14,.15)),true)
	box("Road",Vector3(0,.015,0),Vector3(64,.03,8),mat("road",Color(.055,.065,.075),0,.87))
	for side in [-1,1]:
		box("Sidewalk",Vector3(0,.12,side*6),Vector3(64,.24,4),pavement,true)
		box("Curb",Vector3(0,.16,side*4.1),Vector3(64,.32,.2),mat("curb",Color(.52,.5,.44)),true)
		for x in [-24,-8,8,24]:
			box("LampPost",Vector3(x,2.9,side*7.3),Vector3(.14,5.8,.14),mat("steel",Color(.055,.075,.09),.8,.3))
			box("LampArm",Vector3(x,5.7,side*6.5),Vector3(.12,.12,1.7),shared.steel)
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
			box("Drain",Vector3(x,.255,side*4.6),Vector3(.7,.025,.5),shared.steel)
	for x in range(-30,31,6):
		box("LaneMark",Vector3(x,.04,0),Vector3(2.5,.02,.1),mat("paint",Color(.8,.68,.34),0,.8))
	if cell_id=="center":
		box("ShelterRoof",Vector3(0,3,-6),Vector3(4.2,.2,3),shared.steel,true)
		for x in [-1.8,1.8]:
			box("ShelterPost",Vector3(x,1.5,-7),Vector3(.1,3,.1),shared.steel,true)
		var machine:=AudioStreamPlayer3D.new()
		machine.stream=load("res://assets/audio/city.wav")
		machine.position=Vector3(-16,8,-17)
		machine.volume_db=-20
		machine.max_distance=24
		add_child(machine)
		machine.finished.connect(machine.play)
		machine.play()
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
		sign.pixel_size = .013
		sign.position = building.position + Vector3(0,3.6,0) + Vector3.FORWARD.rotated(Vector3.UP,deg_to_rad(b.yaw))*float(b.front_offset)
		sign.rotation_degrees.y = b.yaw+180
		add_child(sign)
	# Reviewed rectangular navigation strip avoids every building footprint.
	var region := NavigationRegion3D.new()
	var navigation := NavigationMesh.new()
	navigation.set_vertices(PackedVector3Array([Vector3(-32,.3,-8),Vector3(32,.3,-8),Vector3(32,.3,8),Vector3(-32,.3,8)]))
	navigation.add_polygon(PackedInt32Array([0,1,2,3]))
	region.navigation_mesh = navigation
	add_child(region)
	set_meta("ready_for_streaming",true)

func capture_state() -> Dictionary:
	return persistent_state.duplicate(true)

func restore_state(state: Dictionary) -> void:
	persistent_state = state.duplicate(true)

func _exit_tree() -> void:
	for child in find_children("*","AudioStreamPlayer3D",true,false):
		child.stop()
