extends CharacterBody3D
signal interacted(target: Node)
var speed:=5.0
var camera: Camera3D
var enabled:=true
var persistence_id:="player"
var injected_move:=Vector2.ZERO

func _ready() -> void:
	for action in {"move_forward":KEY_W,"move_back":KEY_S,"move_left":KEY_A,"move_right":KEY_D,"interact":KEY_E,"jump":KEY_SPACE}:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
			var event:=InputEventKey.new()
			event.physical_keycode={"move_forward":KEY_W,"move_back":KEY_S,"move_left":KEY_A,"move_right":KEY_D,"interact":KEY_E,"jump":KEY_SPACE}[action]
			InputMap.action_add_event(action,event)
	var shape:=CollisionShape3D.new()
	var capsule:=CapsuleShape3D.new();capsule.radius=.32;capsule.height=1.8
	shape.shape=capsule;shape.position.y=.9
	add_child(shape)
	camera=Camera3D.new();camera.position.y=1.65;camera.fov=75
	add_child(camera)
	camera.current=true
	floor_snap_length=.35
	add_to_group("player")

func _physics_process(delta: float) -> void:
	if not enabled:return
	var axis:=Input.get_vector("move_left","move_right","move_forward","move_back")+injected_move
	var direction: Vector3=(transform.basis*Vector3(axis.x,0,axis.y)).normalized()
	velocity.x=direction.x*speed;velocity.z=direction.z*speed
	if not is_on_floor():velocity.y-=18*delta
	elif Input.is_action_just_pressed("jump"):velocity.y=6
	move_and_slide()
	if Input.is_action_just_pressed("interact"):try_interact()

func try_interact() -> bool:
	var query:=PhysicsRayQueryParameters3D.create(camera.global_position,camera.global_position-camera.global_basis.z*3.5)
	query.exclude=[get_rid()]
	var result:=get_world_3d().direct_space_state.intersect_ray(query)
	if result.is_empty():return false
	var target: Node=result.collider
	if target.has_method("interact"):
		target.interact(self)
		interacted.emit(target)
		return true
	return false

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.mouse_mode==Input.MOUSE_MODE_CAPTURED:
		rotation.y-=event.relative.x*.0025
		camera.rotation.x=clampf(camera.rotation.x-event.relative.y*.0025,-1.4,1.4)
	if event is InputEventMouseButton and event.pressed:Input.mouse_mode=Input.MOUSE_MODE_CAPTURED
	if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE:Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
