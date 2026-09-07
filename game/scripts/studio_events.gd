extends Node
signal world_event(kind: String, payload: Dictionary)
var history: Array[Dictionary] = []
func publish(kind: String,payload: Dictionary={}) -> void:
	history.append({"kind":kind,"payload":payload.duplicate(true)})
	if history.size()>128:history.pop_front()
	world_event.emit(kind,payload)
