extends StaticBody3D
## Reusable terminal/switch/door/pickup hook. Art belongs in child nodes.
signal activated(id: String)
signal damaged(amount: int)
@export var persistence_id:=""
@export_enum("terminal","switch","door","pickup") var kind:="switch"
var active:=false
var health:=100
func interact(_actor: Node) -> void:
	if health<=0:return
	if kind in ["terminal","pickup"] and active:return
	active=not active
	apply_state()
	activated.emit(persistence_id)
func apply_damage(amount: int) -> void:
	var applied:=maxi(0,amount);health=maxi(0,health-applied);damaged.emit(applied)
func apply_state() -> void:
	if kind in ["door","pickup"]:
		visible=not active
		for shape in find_children("*","CollisionShape3D",true,false):shape.set_deferred("disabled",active)
func snapshot() -> Dictionary:return {"id":persistence_id,"active":active,"health":health}
func restore(value: Dictionary) -> void:
	active=value.get("active",false);health=clampi(int(value.get("health",100)),0,100);apply_state()
