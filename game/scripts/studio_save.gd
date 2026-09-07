extends RefCounted
const VERSION:=1
static func save_state(file: String,data: Dictionary) -> Error:
	if not file.begins_with("user://"):return ERR_INVALID_PARAMETER
	var stream:=FileAccess.open(file+".tmp",FileAccess.WRITE)
	if stream==null:return FileAccess.get_open_error()
	stream.store_string(JSON.stringify({"version":VERSION,"state":data}))
	stream.close()
	return DirAccess.rename_absolute(file+".tmp",file)
static func load_state(file: String) -> Dictionary:
	if not FileAccess.file_exists(file):return {}
	var value=JSON.parse_string(FileAccess.get_file_as_string(file))
	if not value is Dictionary or value.get("version")!=VERSION or not value.get("state") is Dictionary:return {}
	return value.state
