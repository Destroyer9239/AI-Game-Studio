extends SceneTree
var checks:=0
func _initialize() -> void:call_deferred("run")
func check(value: bool,label: String) -> void:
	assert(value,label);checks+=1
func run() -> void:
	var world=load("res://scenes/playable_block.tscn").instantiate();root.add_child(world)
	for i in range(600):
		await physics_frame
		if world.ready_player and world.streamer.pending.is_empty():break
	check(world.ready_player,"player waits for collision-ready chunk")
	for i in range(40):await physics_frame
	check(world.player.is_on_floor(),"player ground collision")
	var player=world.player
	var before: Vector3=player.position
	player.injected_move=Vector2(1,0)
	for i in range(30):await physics_frame
	player.injected_move=Vector2.ZERO
	check(player.position.x>before.x+1,"player movement")
	player.position=Vector3(0,.24,-4.1);player.rotation=Vector3.ZERO;player.camera.rotation=Vector3(-.3,0,0)
	for i in range(3):await physics_frame
	check(player.try_interact(),"ray interaction")
	check(world.objective_state=="COMPLETE","objective completion")
	check(world.events.history.any(func(e):return e.kind=="objective_complete"),"event bus")
	check(world.save_game("user://studio_unit_save.json")==OK,"save write")
	player.position.x=10;world.objective_state="ACTIVE"
	check(world.load_game("user://studio_unit_save.json"),"save load")
	check(absf(player.position.x)<.1 and world.objective_state=="COMPLETE","state restored")
	check(world.save_game("user://studio_unit_save.json")==OK,"replace existing save")
	var npcs:=get_nodes_in_group("npcs")
	check(npcs.size()==1,"NPC spawned with cell")
	var npc=npcs[0]
	var npc_before: Vector3=npc.position
	for i in range(120):await physics_frame
	check(npc.position.distance_to(npc_before)>.5,"actual NPC navigation movement")
	world.director.set_weather("rain")
	check(npc.state=="SEEK_SHELTER","NPC weather reaction")
	var skeletons: Array=npc.visual.find_children("*","Skeleton3D",true,false)
	check(skeletons.size()==1 and skeletons[0].get_bone_count()>=8,"imported skeleton")
	check(npc.animation!=null and npc.animation.get_animation_list().size()>=2,"imported animation clips")
	check(npc.find_children("*","MeshInstance3D",true,false).any(func(n):return n.visibility_range_begin==35),"distant character proxy")
	check(world.vehicle_hooks.has("enter_requested"),"vehicle interface reservation")
	DirAccess.remove_absolute("user://studio_unit_save.json")
	world.queue_free();await process_frame;await create_timer(.2).timeout
	print("GAMEPLAY_TESTS_PASS: ",checks," checks")
	quit()
