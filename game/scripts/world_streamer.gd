extends Node3D
## Threaded resource loading with bounded instances, hysteresis and state hooks.
signal chunk_loaded(id: String)
signal chunk_unloaded(id: String)
var loaded: Dictionary = {}
var pending: Dictionary = {}
var states: Dictionary = {}
var failures: Dictionary = {}
var spec: Dictionary
var spec_path := "res://world/city_block.json"
var focus := Vector3.ZERO
var loads := 0
var unloads := 0
var active_load := ""
var discarded_loads := 0
var duplicate_requests := 0

func _ready() -> void:
	spec = JSON.parse_string(FileAccess.get_file_as_string(spec_path))

func request_cell(id: String) -> void:
	if loaded.has(id) or pending.has(id) or failures.has(id):
		duplicate_requests += 1
		return
	var path := str(spec.get("scene_directory","res://scenes/world"))+"/cell_"+id+".tscn"
	pending[id] = path

func update_focus(value: Vector3) -> void:
	focus = value
	for cell in spec.cells:
		var distance := absf(focus.x-float(cell.x))
		# Godot has no threaded cancellation API. Cancel queued work; drain the
		# active request and discard its result when no longer inside load radius.
		if distance >= spec.load_radius and pending.has(cell.id) and active_load != cell.id:
			pending.erase(cell.id)
		if distance < spec.load_radius:
			request_cell(cell.id)
		elif distance > spec.unload_radius and loaded.has(cell.id):
			var node: Node = loaded[cell.id]
			states[cell.id] = node.capture_state()
			remove_child(node)
			node.queue_free()
			loaded.erase(cell.id)
			unloads += 1
			chunk_unloaded.emit(cell.id)

func _process(_delta: float) -> void:
	# One background loader owns shared resources at a time. Do not create render
	# primitives on the main thread while another cell's meshes are still loading.
	if active_load.is_empty() and not pending.is_empty():
		active_load=pending.keys()[0]
		var result:=ResourceLoader.load_threaded_request(pending[active_load])
		if result!=OK:
			failures[active_load]=error_string(result)
			pending.erase(active_load)
			active_load=""
		return
	# Instantiate at most one cell each frame, after its resource completes.
	for id in pending.keys():
		if id!=active_load:continue
		var path: String = pending[id]
		var status := ResourceLoader.load_threaded_get_status(path)
		if status == ResourceLoader.THREAD_LOAD_FAILED or status == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
			failures[id] = "resource load failed"
			pending.erase(id)
			active_load=""
		elif status == ResourceLoader.THREAD_LOAD_LOADED:
			var resource := ResourceLoader.load_threaded_get(path) as PackedScene
			pending.erase(id)
			active_load=""
			var cell: Dictionary = {}
			for item in spec.cells:
				if item.id == id: cell = item
			if absf(focus.x-float(cell.x)) >= spec.load_radius or loaded.size() >= int(spec.max_loaded):
				discarded_loads += 1
				continue
			if resource == null:
				failures[id] = "not a PackedScene"
				continue
			var node := resource.instantiate() as Node3D
			node.position.x = cell.x
			loaded[id] = node
			add_child(node)
			node.restore_state(states.get(id,{}))
			loads += 1
			chunk_loaded.emit(id)
			break

func metrics() -> Dictionary:
	return {"loaded":loaded.size(),"pending":pending.size(),"loads":loads,"unloads":unloads,"failures":failures,"discarded":discarded_loads,"duplicate_requests":duplicate_requests}

func _exit_tree() -> void:
	# Drain only our outstanding request before releasing shared scene resources.
	if not active_load.is_empty() and pending.has(active_load):
		ResourceLoader.load_threaded_get(pending[active_load])
	pending.clear()
	active_load=""
