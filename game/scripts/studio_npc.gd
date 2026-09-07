extends CharacterBody3D
var agent: NavigationAgent3D
var state:="PATROL"
var weather:="clear"
var persistence_id:="worker_01"
var goal_index:=0
var goals:=[Vector3(-22,.3,6),Vector3(22,.3,6)]
var visual: Node3D
var animation: AnimationPlayer
var ready_frames:=0
var health:=100
var activity:="patrol"
signal perceived(entity: Node)

func snapshot() -> Dictionary:
	return {"id":persistence_id,"position":[position.x,position.y,position.z],"goal":goal_index,"health":health}

func restore(value: Dictionary) -> void:
	var point: Array=value.get("position",[-20,.3,6])
	position=Vector3(point[0],point[1],point[2])
	goal_index=clampi(int(value.get("goal",0)),0,1)
	health=clampi(int(value.get("health",100)),0,100)
	velocity=Vector3.ZERO
	agent.target_position=Vector3(0,.3,6) if state=="SEEK_SHELTER" else goals[goal_index]

func _ready() -> void:
	var shape:=CollisionShape3D.new();var capsule:=CapsuleShape3D.new();capsule.radius=.3;capsule.height=1.8;shape.shape=capsule;shape.position.y=.9;add_child(shape)
	visual=load("res://assets/models/worker_fixture.glb").instantiate()
	add_child(visual)
	for child in visual.find_children("*","AnimationPlayer",true,false):animation=child
	if animation:
		for clip in animation.get_animation_list():
			if "Walk" in clip:
				animation.get_animation(clip).loop_mode=Animation.LOOP_LINEAR
				animation.play(clip)
	for child in visual.find_children("*","GeometryInstance3D",true,false):child.visibility_range_end=35
	var proxy:=MeshInstance3D.new();var mesh:=CapsuleMesh.new();mesh.height=1.8;mesh.radius=.3;mesh.radial_segments=6;mesh.rings=1;proxy.mesh=mesh;proxy.position.y=.9;proxy.visibility_range_begin=35
	add_child(proxy)
	agent=NavigationAgent3D.new();agent.path_desired_distance=.5;agent.target_desired_distance=.6;add_child(agent)
	floor_snap_length=.35
	add_to_group("npcs")

func on_environment(kind: String,value: Dictionary) -> void:
	if kind=="weather":
		weather=value.weather
		state="SEEK_SHELTER" if weather in ["rain","heavy_rain","storm"] else "PATROL"
		if state=="SEEK_SHELTER":agent.target_position=Vector3(0,.3,6)
		else:agent.target_position=goals[goal_index]

func _physics_process(delta: float) -> void:
	ready_frames+=1
	if ready_frames<20:return
	if ready_frames==20:agent.target_position=Vector3(0,.3,6) if state=="SEEK_SHELTER" else goals[goal_index]
	if agent.is_navigation_finished():
		if state=="PATROL":goal_index=1-goal_index;agent.target_position=goals[goal_index]
		else:velocity=Vector3.ZERO;return
	var next:=agent.get_next_path_position()
	var direction:=next-global_position;direction.y=0
	if direction.length()>.05:
		direction=direction.normalized()
		visual.rotation.y=atan2(-direction.x,-direction.z)
	velocity.x=direction.x*1.6;velocity.z=direction.z*1.6
	if not is_on_floor():velocity.y-=18*delta
	move_and_slide()
