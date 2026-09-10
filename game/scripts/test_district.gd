extends SceneTree
var checks:=0
var failures:=0
func check(ok:bool,label:String)->void:
 checks+=1
 if not ok:failures+=1;push_error(label)
func settle(streamer:Node)->void:
 for i in range(900):
  await physics_frame
  if streamer.pending.is_empty():return
 check(false,"district request timed out")
func _initialize()->void:call_deferred("run")
func run()->void:
 var streamer=load("res://scripts/world_streamer.gd").new();streamer.spec_path="res://world/district.json";root.add_child(streamer)
 streamer.update_focus(Vector3.ZERO);await settle(streamer)
 check(streamer.loaded.size()==2,"two generated blocks loaded")
 check(streamer.loaded.west.cell_data.buildings.size()==2,"service block uses two buildings")
 check(streamer.loaded.center.cell_data.buildings.size()==4,"first block preserved")
 var map=streamer.get_world_3d().navigation_map
 for i in range(5):await physics_frame
 var path=NavigationServer3D.map_get_path(map,Vector3(-80,.3,0),Vector3(10,.3,0),true)
 check(path.size()>1 and path[-1].distance_to(Vector3(10,.3,0))<.5,"cross-boundary road route")
 for cycle in range(10):
  streamer.loaded.west.persistent_state["district_event"]=cycle
  streamer.update_focus(Vector3(220,0,0));await settle(streamer);await create_timer(.05).timeout
  check(streamer.loaded.is_empty(),"district unload")
  streamer.update_focus(Vector3(-64,0,0));await settle(streamer)
  check(streamer.loaded.west.persistent_state.get("district_event")==cycle,"block event restored")
  check(streamer.loaded.size()<=3 and streamer.failures.is_empty(),"bounded failure-free reload")
 streamer.queue_free();await process_frame;await create_timer(.2).timeout
 if failures==0:print("DISTRICT_TEST_PASS: ",checks," checks / 10 cycles")
 quit(0 if failures==0 else 1)
