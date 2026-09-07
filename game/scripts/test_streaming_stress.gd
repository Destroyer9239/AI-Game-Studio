extends SceneTree
var checks:=0
func _initialize() -> void:call_deferred("run")
func check(value: bool,label: String) -> void:
	if not value:
		push_error("STRESS: "+label);quit(1)
		assert(value,label)
	checks+=1
func settle(s: Node) -> void:
	for i in range(600):
		await physics_frame
		if s.pending.is_empty():return
	check(false,"load timeout")
func run() -> void:
	var world=load("res://scenes/playable_block.tscn").instantiate();root.add_child(world)
	world.set_process(false);world.player.enabled=false
	var s=world.streamer
	await settle(s)
	for i in range(3):await physics_frame
	world.on_terminal("service_terminal")
	s.loaded.center.terminal.active=true
	s.loaded.center.worker.health=73
	world.director.set_weather("rain")
	check(world.save_game("user://studio_stress_save.json")==OK,"integrated save")
	var baseline_regions:=NavigationServer3D.map_get_regions(world.get_world_3d().navigation_map).size()
	var max_nodes:=0
	for cycle in range(20):
		var old_worker=weakref(s.loaded.center.worker)
		s.update_focus(Vector3(160,0,0))
		await settle(s);await process_frame
		check(not s.loaded.has("center") and old_worker.get_ref()==null,"unload destroys worker")
		check(get_nodes_in_group("npcs").is_empty(),"no stale NPC group entry")
		# Rapid crossing changes the target while a resource may be pending.
		s.update_focus(Vector3.ZERO);await process_frame
		s.update_focus(Vector3(-160,0,0));await process_frame
		s.update_focus(Vector3(160,0,0));await settle(s)
		check(not s.loaded.has("center"),"stale pending center never instantiated")
		s.update_focus(Vector3.ZERO);s.update_focus(Vector3.ZERO)
		await settle(s)
		check(s.loaded.size()==3 and s.get_child_count()==3,"bounded cell ownership")
		check(get_nodes_in_group("npcs").size()==1,"one restored worker")
		check(s.loaded.center.worker.health==73,"worker entity persistence")
		check(s.loaded.center.worker.state=="SEEK_SHELTER","current weather applied on reload")
		check(s.loaded.center.terminal.active and world.objective_state=="COMPLETE","terminal and objective persistence")
		check(s.failures.is_empty() and s.pending.is_empty(),"no failed or stranded loads")
		for i in range(3):await physics_frame
		check(NavigationServer3D.map_get_regions(world.get_world_3d().navigation_map).size()==baseline_regions,"navigation region budget")
		max_nodes=maxi(max_nodes,int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)))
	check(world.load_game("user://studio_stress_save.json"),"disk restore after cycles")
	check(s.loaded.center.worker.health==73 and s.loaded.center.terminal.active,"disk entity restore")
	print("STREAMING_STRESS_PASS: ",checks," checks / 20 cycles; max nodes ",max_nodes,"; ",s.metrics())
	DirAccess.remove_absolute("user://studio_stress_save.json")
	world.queue_free();await process_frame;await create_timer(.3).timeout
	quit()
