extends SceneTree
func _initialize() -> void:call_deferred("run")
func run() -> void:
 var world=load("res://scenes/district_demo.tscn").instantiate();root.add_child(world)
 await create_timer(3).timeout
 var camera:=Camera3D.new();world.add_child(camera);camera.current=true
 var folder:=ProjectSettings.globalize_path("res://../generated/previews/district_two")
 DirAccess.make_dir_recursive_absolute(folder)
 for view in [["block_1",Vector3(22,3,6),Vector3(-14,3,-1)], ["block_2",Vector3(-40,4,6),Vector3(-78,4,-5)], ["district_wide",Vector3(-30,42,53),Vector3(-30,0,0)]]:
  world.player.enabled=false;world.player.position=Vector3(view[1].x,.35,6)
  camera.position=view[1];camera.look_at(view[2]);world.hud.visible=false
  for weather in ["clear","rain"]:
   world.director.set_hour(15);world.director.set_weather(weather)
   await create_timer(2).timeout;await RenderingServer.frame_post_draw
   assert(root.get_texture().get_image().save_png(folder+"/"+view[0]+"_"+weather+".png")==OK)
 world.queue_free();await process_frame;await create_timer(.3).timeout
 print("DISTRICT_REVIEW_PASS: six GPU views");quit()
