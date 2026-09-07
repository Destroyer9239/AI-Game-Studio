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
	world.director.set_weather("clear");world.director.set_hour(22)
	check(npc.state=="REST","night schedule hook")
	world.director.set_hour(12)
	check(npc.state=="PATROL","day schedule resumes patrol")
	var skeletons: Array=npc.visual.find_children("*","Skeleton3D",true,false)
	check(skeletons.size()==1 and skeletons[0].get_bone_count()>=8,"imported skeleton")
	check(npc.animation!=null and npc.animation.get_animation_list().size()>=2,"imported animation clips")
	var playhead: float=npc.animation.current_animation_position
	for i in range(5):await physics_frame
	check(npc.animation.is_playing() and npc.animation.current_animation_position!=playhead,"animation actually advances")
	check(npc.find_children("*","MeshInstance3D",true,false).any(func(n):return n.visibility_range_begin==70),"distant character proxy")
	check(world.vehicle_hooks.has("enter_requested"),"vehicle interface reservation")
	var saved: Dictionary=load("res://scripts/studio_save.gd").load_state("user://studio_unit_save.json")
	for field in ["player","chunks","environment","settings"]:
		var malformed:=saved.duplicate(true);malformed[field]="invalid"
		check(not load("res://scripts/studio_save.gd").valid_world(malformed),"reject malformed "+field)
	var door=load("res://scripts/studio_interactable.gd").new();door.kind="door";root.add_child(door)
	var collision:=CollisionShape3D.new();collision.shape=BoxShape3D.new();door.add_child(collision)
	door.interact(player);await process_frame
	check(not door.visible and collision.disabled,"door hook opens collision")
	door.interact(player);await process_frame
	check(door.visible and not collision.disabled,"door hook closes collision")
	door.apply_damage(10);check(door.health==90,"health hook")
	door.kind="pickup";door.interact(player);door.interact(player)
	check(door.active,"pickup consumed only once")
	door.queue_free()
	var objective=load("res://scripts/studio_objective.gd").new();objective.activate();objective.consume("unrelated")
	check(objective.state=="ACTIVE" and objective.progress==0,"objective event filtering")
	objective.fail();objective.consume("service_activated")
	check(objective.state=="FAILED","objective failure is terminal")
	DirAccess.remove_absolute("user://studio_unit_save.json")
	world.queue_free();await process_frame;await create_timer(.2).timeout
	print("GAMEPLAY_TESTS_PASS: ",checks," checks")
	quit()
