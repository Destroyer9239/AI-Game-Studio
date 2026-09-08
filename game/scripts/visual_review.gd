extends SceneTree
var views=[
 ["wide_day",Vector3(22,2,6),Vector3(-14,3,-1),15,"clear",2],
 ["foundry",Vector3(-5,4,-5),Vector3(-16,5,-17),15,"clear",2],
 ["market",Vector3(6,3,-5),Vector3(16,3,-17),15,"clear",2],
 ["office",Vector3(-5,5,7),Vector3(-16,8,17),15,"clear",2],
 ["night",Vector3(22,2,6),Vector3(-14,3,-1),22,"clear",3],
 ["rain",Vector3(22,2,6),Vector3(-14,3,-1),16,"rain",3],
 ["shelter",Vector3(0,1.9,-6),Vector3(0,2,4),16,"rain",3],
 ["service",Vector3(-29,3,-5),Vector3(-24,2,-12),16,"clear",2],
 ["robot",Vector3(-7,2,3),Vector3(-17,1,6),15,"clear",2],
 ["cinematic",Vector3(24,5,5),Vector3(-12,5,-3),18,"rain",4],
 ["low",Vector3(22,2,6),Vector3(-14,3,-1),16,"rain",0]]
func _initialize() -> void:call_deferred("run")
func run() -> void:
 var folder:=""
 for arg in OS.get_cmdline_user_args():
  if arg.begins_with("--review-dir="):folder=arg.trim_prefix("--review-dir=")
 assert(not folder.is_empty());DirAccess.make_dir_recursive_absolute(folder)
 var world=load("res://scenes/playable_block.tscn").instantiate();root.add_child(world)
 await create_timer(2).timeout
 var camera:=Camera3D.new();world.add_child(camera);camera.current=true;camera.fov=65
 for view in views:
  world.player.enabled=false;world.player.position=Vector3.ZERO
  camera.position=view[1];camera.look_at(view[2]);world.director.set_hour(view[3]);world.director.set_weather(view[4]);world.director.wetness=.8 if view[4]=="rain" else 0
  world.quality=view[5];world.apply_quality()
  if view[0]=="robot":
   var npc=world.streamer.loaded.center.worker
   npc.position=Vector3(-17,.3,6);npc.goals=[Vector3(-17,.3,6),Vector3(-10,.3,6)];npc.goal_index=1;npc.agent.target_position=npc.goals[1]
  world.hud.visible=false
  await create_timer(2).timeout;await RenderingServer.frame_post_draw
  assert(root.get_texture().get_image().save_png(folder+"/"+view[0]+".png")==OK)
 world.queue_free();await process_frame;await create_timer(.3).timeout
 print("VISUAL_REVIEW_PASS: 11 GPU views");quit()
