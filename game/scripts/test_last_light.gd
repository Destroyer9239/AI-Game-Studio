extends SceneTree
var checks:=0
var failures:=0
func check(ok:bool,label:String)->void:
	checks+=1
	if not ok:failures+=1;push_error(label)
func settle(world:Node)->void:
	for i in range(900):
		await physics_frame
		if world.streamer.pending.is_empty():return
	check(false,"streaming timeout")
func _initialize()->void:call_deferred("run")
func run()->void:
	var world=load("res://scenes/last_light.tscn").instantiate()
	world.save_slot="user://last_light_test.json";root.add_child(world)
	await settle(world);await create_timer(.2).timeout
	world.set_process(false);world.player.enabled=false
	check(world.panel.visible and not world.started,"start menu shown")
	var click:=InputEventMouseButton.new();click.pressed=true;click.button_index=MOUSE_BUTTON_LEFT
	world.player._unhandled_input(click)
	check(Input.mouse_mode==Input.MOUSE_MODE_VISIBLE,"disabled player cannot steal menu cursor")
	check(world.streamer.loaded.has("west"),"mission relay cell loaded")
	world.started=true;world.panel.hide()
	var center=world.streamer.loaded.center.terminal
	center.interact(world.player)
	check(world.mission_stage==0 and not center.active,"out-of-order terminal remains usable")
	var relay=world.streamer.loaded.west.terminal
	world.player.position=Vector3(-50,.35,8)
	world.player.camera.look_at(relay.global_position)
	await physics_frame;await physics_frame
	check(world.player.try_interact(),"actual player ray hits relay")
	check(world.mission_stage==1 and relay.active,"relay advances mission")
	check(FileAccess.file_exists(world.save_slot),"progress autosaved")
	world.mission_stage=0
	check(world.load_game() and world.mission_stage==1,"disk checkpoint restored")
	world.streamer.update_focus(Vector3(220,0,0));await settle(world);await create_timer(.1).timeout
	check(world.streamer.loaded.is_empty(),"mission cells unload")
	world.streamer.update_focus(Vector3.ZERO);await settle(world)
	check(world.streamer.loaded.west.terminal.active,"relay restored after stream reload")
	center=world.streamer.loaded.center.terminal
	world.player.position=Vector3(0,.35,-4.6);world.player.camera.look_at(center.global_position)
	await physics_frame;await physics_frame
	check(world.player.try_interact(),"actual player ray hits service terminal")
	check(world.mission_stage==2 and world.objective_state=="COMPLETE","existing objective integrated")
	world.player.position=Vector3(22,.4,6);world._process(.016)
	check(world.mission_stage==3 and world.panel.visible,"extraction completes mission and shows ending")
	check(world.load_game() and world.mission_stage==3,"completed operation restores")
	var data:Dictionary=world.capture_save_data();data.mission_stage=-1
	load("res://scripts/studio_save.gd").save_state("user://last_light_invalid_test.json",data)
	check(not world.load_game("user://last_light_invalid_test.json") and world.mission_stage==3,"invalid mission save rejected before mutation")
	world.queue_free();await process_frame;await create_timer(.3).timeout
	if failures==0:print("LAST_LIGHT_TEST_PASS: ",checks," checks")
	quit(0 if failures==0 else 1)
