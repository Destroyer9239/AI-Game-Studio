extends SceneTree
var checks := 0
func _initialize() -> void:
	call_deferred("run")
func check(value: bool, label: String) -> void:
	if not value:
		push_error("Streaming test failed: "+label)
		quit(1)
	checks += 1
func settle(streamer: Node) -> void:
	for i in range(600):
		await process_frame
		if streamer.pending.is_empty(): return
	push_error("Streaming timeout")
	quit(1)
func run() -> void:
	var streamer = load("res://scripts/world_streamer.gd").new()
	root.add_child(streamer)
	streamer.update_focus(Vector3.ZERO)
	streamer.update_focus(Vector3.ZERO)
	check(streamer.pending.size()==3,"duplicate request prevention")
	await settle(streamer)
	check(streamer.loaded.size()==3,"neighbor preload")
	check(streamer.loads==3,"one instance per cell")
	check(streamer.failures.is_empty(),"no load failures")
	var center: Node = streamer.loaded.center
	check(center.cell_data.buildings.size()==4,"four designed buildings")
	# Material batching cut per-building submissions; guard against a future
	# "cheaper" import that is really missing geometry.
	var building_meshes:=0
	var building_triangles:=0
	for lot in center.cell_data.buildings:
		var node: Node=center.get_node(str(lot.id))
		var meshes:=node.find_children("*","MeshInstance3D",true,false)
		check(meshes.size()>0 and meshes.size()<=20,"building "+str(lot.id)+" stays batched by material")
		building_meshes+=meshes.size()
		for instance in meshes:
			check(instance.mesh!=null and instance.mesh.get_surface_count()>0,"batched building surface present")
			for surface in range(instance.mesh.get_surface_count()):
				var arrays: Array=instance.mesh.surface_get_arrays(surface)
				var index=arrays[Mesh.ARRAY_INDEX]
				building_triangles+=int(index.size()/3) if index!=null else int(arrays[Mesh.ARRAY_VERTEX].size()/3)
				check(instance.mesh.surface_get_material(surface)!=null,"batched building surface keeps its material")
	check(building_meshes<=80,"block buildings stay material batched (%d instances)"%building_meshes)
	check(building_triangles>=10000,"batching preserved building geometry (%d triangles)"%building_triangles)
	check(center.find_children("*","StaticBody3D",true,false).size()>=7,"static collisions")
	check(center.find_children("*","NavigationRegion3D",true,false).size()==1,"navigation lifecycle")
	center.persistent_state={"terminal_active":true}
	streamer.update_focus(Vector3(160,0,0))
	await process_frame
	check(not streamer.loaded.has("center"),"unload outside hysteresis")
	check(streamer.states.center.terminal_active,"state captured")
	streamer.update_focus(Vector3.ZERO)
	await settle(streamer)
	check(streamer.loaded.center.persistent_state.terminal_active,"state restored")
	check(streamer.loaded.size()<=3,"loaded cell budget")
	print("STREAMING_TESTS_PASS: ",checks," checks ",streamer.metrics())
	streamer.queue_free()
	await process_frame
	await create_timer(.15).timeout
	quit()
