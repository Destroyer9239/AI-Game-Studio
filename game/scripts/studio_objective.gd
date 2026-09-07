extends RefCounted
signal changed(state: String, progress: int)
var definition:={"id":"service_link","target":1,"event":"service_activated"}
var state:="INACTIVE"
var progress:=0
func activate() -> void:
	if state!="INACTIVE":return
	state="ACTIVE";changed.emit(state,progress)
func consume(kind: String,_payload: Dictionary={}) -> void:
	if state!="ACTIVE" or kind!=definition.event:return
	progress=mini(int(definition.target),progress+1)
	if progress>=int(definition.target):state="COMPLETE"
	changed.emit(state,progress)
func fail() -> void:
	if state!="ACTIVE":return
	state="FAILED";changed.emit(state,progress)
