extends SceneTree
func _initialize()->void:call_deferred("run")
func run()->void:
	var packed=load(ProjectSettings.get_setting("application/run/main_scene")) as PackedScene
	assert(packed!=null)
	var scene:=packed.instantiate();root.add_child(scene)
	await create_timer(2).timeout
	scene.queue_free();await process_frame;await create_timer(.3).timeout
	print("PIPELINE_MAIN_PASS: configured main scene and orderly shutdown")
	quit()
