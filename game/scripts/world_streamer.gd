extends Node3D
## Threaded resource loading with bounded instances, hysteresis and state hooks.
signal chunk_loaded(id: String)
signal chunk_unloaded(id: String)
var loaded: Dictionary = {}
var pending: Dictionary = {}
var states: Dictionary = {}
var failures: Dictionary = {}
var spec: Dictionary
var focus := Vector3.ZERO
var loads := 0
var unloads := 0

func _ready() -> void:
	spec = JSON.parse_string(FileAccess.get_file_as_string("res://world/city_block.json"))

func request_cell(id: String) -> void:
	if loaded.has(id) or pending.has(id) or failures.has(id):
		return
	var path := "res://scenes/world/cell_"+id+".tscn"
	var result := ResourceLoader.load_threaded_request(path)
	if result == OK:
		pending[id] = path
	else:
		failures[id] = error_string(result)

func update_focus(value: Vector3) -> void:
	focus = value
	for cell in spec.cells:
		var distance := absf(focus.x-float(cell.x))
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
	# Instantiate at most one cell each frame, after its resource completes.
	for id in pending.keys():
		var path: String = pending[id]
		var status := ResourceLoader.load_threaded_get_status(path)
		if status == ResourceLoader.THREAD_LOAD_FAILED or status == ResourceLoader.THREAD_LOAD_INVALID_RESOURCE:
			failures[id] = "resource load failed"
			pending.erase(id)
		elif status == ResourceLoader.THREAD_LOAD_LOADED:
			var resource := ResourceLoader.load_threaded_get(path) as PackedScene
			pending.erase(id)
			var cell: Dictionary = {}
			for item in spec.cells:
				if item.id == id: cell = item
			if absf(focus.x-float(cell.x)) >= spec.load_radius or loaded.size() >= int(spec.max_loaded):
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
	return {"loaded":loaded.size(),"pending":pending.size(),"loads":loads,"unloads":unloads,"failures":failures}
