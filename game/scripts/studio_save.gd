extends RefCounted
const VERSION:=1
static func vector_data(value: Variant) -> bool:
	if not value is Array or value.size()!=3:return false
	return value.all(func(v):return (v is float or v is int) and is_finite(float(v)) and absf(float(v))<100000)

static func valid_world(state: Dictionary) -> bool:
	if not vector_data(state.get("player")):return false
	if not state.get("chunks") is Dictionary or state.get("objective") not in ["ACTIVE","COMPLETE","FAILED"]:return false
	if not state.get("environment") is Dictionary or not state.get("settings",{}) is Dictionary:return false
	var environment: Dictionary=state.environment
	if environment.get("weather") not in ["clear","cloudy","rain","heavy_rain","fog","storm"]:return false
	for key in ["hour","wetness"]:
		if not (environment.get(key) is float or environment.get(key) is int) or not is_finite(float(environment[key])):return false
	if float(environment.wetness)<0 or float(environment.wetness)>1:return false
	if not (state.get("yaw",0) is float or state.get("yaw",0) is int):return false
	if not is_finite(float(state.get("yaw",0))):return false
	var quality=state.get("settings",{}).get("quality",2)
	if not (quality is int or quality is float) or quality<0 or quality>4:return false
	for id in state.chunks:
		if id not in ["west","center","east"] or not state.chunks[id] is Dictionary:return false
		var chunk: Dictionary=state.chunks[id]
		for entity in ["worker","terminal"]:
			if not chunk.has(entity):continue
			if not chunk[entity] is Dictionary:return false
			var data: Dictionary=chunk[entity]
			if not (data.get("health",100) is int or data.get("health",100) is float):return false
			if entity=="worker":
				if not vector_data(data.get("position")):return false
				if not (data.get("goal",0) is int or data.get("goal",0) is float):return false
			elif not data.get("active",false) is bool:return false
	return true

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
