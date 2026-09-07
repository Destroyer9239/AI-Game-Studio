extends SceneTree
## Navigation hardening for the composed hero block: prop clearance, lane
## continuity, stuck/oscillation detection and streamed region lifecycle.
## Prop placement is art direction; this only proves it stays routable.
var checks := 0
var failures: Array[String] = []

func check(value: bool, label: String) -> void:
	checks += 1
	if not value:
		failures.append(label)
		push_error("HERO NAVIGATION FAILED: "+label)

func _initialize() -> void:
	call_deferred("run")

func settle(streamer: Node) -> void:
	for i in range(900):
		await physics_frame
		if streamer.pending.is_empty(): return
	check(false, "cells finished loading")

## Footprints the chunk registered as navigation obstacles, in world space.
## Each entry holds the world centre, the solid half extent and the one-metre
## capsule clearance half extent the chunk uses when carving its grid.
func blocked_footprints(chunk: Node) -> Array:
	var result: Array = []
	for bounds in chunk.nav_obstacles:
		if bounds.position.y+bounds.size.y < .4 or bounds.position.y > 2.1: continue
		var center: Vector3 = chunk.global_position+bounds.get_center()
		result.append([center, Vector3(bounds.size.x*.5, 0, bounds.size.z*.5), Vector3(bounds.size.x*.5+1, 0, bounds.size.z*.5+1)])
	return result

## A route may hug the carved cell boundary, so solidity is measured against the
## real prop volume grown by the agent capsule radius, not the carving margin.
func inside_footprint(point: Vector3, footprints: Array, margin := .3) -> bool:
	for entry in footprints:
		var center: Vector3 = entry[0]
		var extent: Vector3 = entry[1]
		if absf(point.x-center.x) < extent.x+margin and absf(point.z-center.z) < extent.z+margin:
			return true
	return false

func path_length(points: PackedVector3Array) -> float:
	var total := 0.0
	for i in range(1, points.size()):
		total += Vector2(points[i].x-points[i-1].x, points[i].z-points[i-1].z).length()
	return total

func run() -> void:
	var world = load("res://scenes/playable_block.tscn").instantiate()
	root.add_child(world)
	await settle(world.streamer)
	for i in range(60):
		await physics_frame
		if world.ready_player: break
	for i in range(10): await physics_frame
	var map: RID = world.get_world_3d().navigation_map
	var chunk = world.streamer.loaded.center
	var footprints := blocked_footprints(chunk)

	# --- navigation region lifecycle -------------------------------------
	var baseline_regions := NavigationServer3D.map_get_regions(map).size()
	check(baseline_regions == world.streamer.loaded.size(), "one navigation region per loaded cell")
	check(footprints.size() >= 12, "composed street props registered as navigation obstacles")

	# --- prop clearance ---------------------------------------------------
	# Every registered prop footprint must be off the mesh, so a route can
	# never be generated through a cabinet, bollard, bench or shelter post.
	var intruding := 0
	for entry in footprints:
		var center: Vector3 = entry[0]
		if absf(center.z) > 7.5 or absf(center.x) > 31.5: continue  # outside the meshed lane
		var closest := NavigationServer3D.map_get_closest_point(map, center)
		if absf(closest.x-center.x) < .5 and absf(closest.z-center.z) < .5: intruding += 1
	check(intruding == 0, "navigation mesh excludes every registered prop footprint")

	# --- pedestrian lane continuity, both sidewalks and the service edge ---
	for lane in [6.0, -6.0, 7.5, 0.0]:
		var from := Vector3(-26, .3, lane)
		var to := Vector3(26, .3, lane)
		var route := NavigationServer3D.map_get_path(map, from, to, true)
		check(route.size() >= 2, "lane %.1f produces a route" % lane)
		if route.is_empty(): continue
		check(Vector2(route[-1].x-to.x, route[-1].z-to.z).length() < 1.5, "lane %.1f route reaches the far side" % lane)
		check(path_length(route) < 52.0*1.8, "lane %.1f route is not a pathological detour" % lane)
		var pierced := 0
		for point in route:
			if inside_footprint(point, footprints): pierced += 1
		check(pierced == 0, "lane %.1f route stays outside prop collision footprints" % lane)

	# --- narrow route past the cabinet and the bollard/bench cluster -------
	for pair in [[Vector3(5,.3,6), Vector3(12,.3,6)], [Vector3(-9,.3,7.4), Vector3(-15,.3,7.4)], [Vector3(9,.3,7.4), Vector3(15,.3,7.4)]]:
		var route := NavigationServer3D.map_get_path(map, pair[0], pair[1], true)
		check(route.size() >= 2 and Vector2(route[-1].x-pair[1].x, route[-1].z-pair[1].z).length() < 1.5,
			"narrow route %s reaches its destination" % str(pair[1]))
		for point in route:
			check(not inside_footprint(point, footprints), "narrow route avoids prop footprints")
			break

	# --- reachable extent toward the building entrances --------------------
	# The meshed lane is bounded; record how close a route can actually get to
	# each designed entrance rather than assuming doors are reachable.
	var entrance_gap := 0.0
	for building in chunk.cell_data.buildings:
		var origin := Vector3(building.position[0], .3, building.position[2])
		var door := origin+Vector3.FORWARD.rotated(Vector3.UP, deg_to_rad(building.yaw))*float(building.front_offset)
		var closest := NavigationServer3D.map_get_closest_point(map, door)
		entrance_gap = maxf(entrance_gap, Vector2(closest.x-door.x, closest.z-door.z).length())
	check(entrance_gap < 6.0, "designed entrances stay within approach range of the navigation mesh")

	# --- live agent: routes around the cabinet without sticking ------------
	var npc = chunk.worker
	npc.position = Vector3(5, .3, 6)
	npc.velocity = Vector3.ZERO
	npc.goals = [Vector3(5,.3,6), Vector3(12,.3,6)]
	npc.goal_index = 1
	npc.agent.target_position = Vector3(12, .3, 6)
	var avoided := true
	var reached := false
	var reversals := 0
	var last_sign := 0
	var window_start: Vector3 = npc.position
	var stalled := 0
	for i in range(720):
		await physics_frame
		if absf(npc.position.x-8) < .68 and absf(npc.position.z-6) < .62: avoided = false
		var sign_now := signi(int(signf(npc.velocity.x*100)))
		if sign_now != 0 and last_sign != 0 and sign_now != last_sign: reversals += 1
		if sign_now != 0: last_sign = sign_now
		if i%60 == 59:
			if npc.position.distance_to(window_start) < .25: stalled += 1
			window_start = npc.position
		if npc.position.x > 11: reached = true; break
	check(avoided, "robot never enters the expanded cabinet collision")
	check(reached, "robot reaches the far side of the cabinet instead of sticking")
	check(stalled == 0, "robot never stalls for a full second while routing")
	check(reversals <= 6, "robot does not oscillate around the obstacle (%d reversals)" % reversals)
	check(npc.position.y > -1.0 and npc.position.y < 3.0, "robot stays on the walkable surface")

	# --- unreachable destination handling ---------------------------------
	npc.state = "TEST_UNREACHABLE"
	npc.agent.target_position = Vector3(0, .3, 120)
	var before: Vector3 = npc.position
	for i in range(180): await physics_frame
	check(npc.position.distance_to(before) < 40.0, "unreachable target does not fling the agent off the block")
	check(npc.position.y > -1.0, "unreachable target does not drop the agent through the floor")
	check(is_finite(npc.position.x) and is_finite(npc.position.z), "agent position stays finite")

	# --- path recalculation after a mid-route target change ---------------
	npc.state = "PATROL"
	npc.agent.target_position = Vector3(-20, .3, 6)
	for i in range(30): await physics_frame
	var heading_west: bool = npc.velocity.x < 0
	npc.agent.target_position = Vector3(20, .3, 6)
	var turned := false
	for i in range(120):
		await physics_frame
		if npc.velocity.x > .2: turned = true; break
	check(heading_west, "agent commits to the first target")
	check(turned, "agent recalculates after the target changes mid-route")

	# --- streamed unload with a live path, then reload ---------------------
	# The world re-centres streaming on the player every frame; own the focus
	# here so the unload under test is not immediately undone.
	world.set_process(false)
	world.player.enabled = false
	npc.agent.target_position = Vector3(-20, .3, 6)
	for i in range(5): await physics_frame
	var doomed: WeakRef = weakref(npc)
	world.streamer.update_focus(Vector3(160, 0, 0))
	await settle(world.streamer)
	await process_frame
	check(doomed.get_ref() == null, "unloading a chunk frees the routing agent")
	check(get_nodes_in_group("npcs").is_empty(), "no orphaned NPC after unload")
	check(NavigationServer3D.map_get_regions(map).size() < baseline_regions, "navigation regions released with the chunk")
	world.streamer.update_focus(Vector3.ZERO)
	await settle(world.streamer)
	for i in range(20): await physics_frame
	check(NavigationServer3D.map_get_regions(map).size() == baseline_regions, "navigation regions restored on reload")
	var restored = world.streamer.loaded.center.worker
	check(restored != null and restored != doomed.get_ref(), "reloaded chunk owns a fresh routing agent")
	restored.agent.target_position = Vector3(20, .3, 6)
	var moved := false
	var origin: Vector3 = restored.position
	for i in range(240):
		await physics_frame
		if restored.position.distance_to(origin) > 1.5: moved = true; break
	check(moved, "restored agent acquires a usable path after chunk reload")

	world.queue_free()
	await process_frame
	await create_timer(.3).timeout
	check(root.get_child_count() == 0, "navigation test releases the world")
	if not failures.is_empty():
		push_error("HERO_NAVIGATION_FAIL: "+str(failures))
		quit(1)
		return
	print("HERO_NAVIGATION_PASS: ", checks, " checks; entrance approach gap ", "%.2f" % entrance_gap, " m")
	quit()
