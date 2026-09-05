extends SceneTree
## Load every script and scene, including resources outside the main scene.
var failed := false
var checked := 0

func _initialize() -> void:
	_scan("res://")
	var main: String = ProjectSettings.get_setting("application/run/main_scene", "")
	if main.is_empty() or not ResourceLoader.exists(main):
		push_error("Missing configured main scene")
		failed = true
	print("PIPELINE_RESOURCES_%s: %d resources" % ["FAIL" if failed else "PASS", checked])
	quit(1 if failed else 0)

func _scan(path: String) -> void:
	for folder in DirAccess.get_directories_at(path):
		if not folder.begins_with("."):
			_scan(path.path_join(folder))
	for file in DirAccess.get_files_at(path):
		if file.get_extension() in ["gd", "tscn", "tres", "glb"]:
			checked += 1
			if ResourceLoader.load(path.path_join(file)) == null:
				push_error("Cannot load resource: " + path.path_join(file))
				failed = true
