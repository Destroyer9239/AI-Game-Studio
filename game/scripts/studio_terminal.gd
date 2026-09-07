extends "res://scripts/studio_interactable.gd"
func _init() -> void:
	persistence_id="service_terminal";kind="terminal"
func _ready() -> void:
	var visual:=MeshInstance3D.new();var box:=BoxMesh.new();box.size=Vector3(.8,1.4,.35);visual.mesh=box
	var material:=StandardMaterial3D.new();material.albedo_color=Color(.04,.13,.17);material.metallic=.6
	material.emission_enabled=true;material.emission=Color(.03,.3,.4);material.emission_energy_multiplier=.4
	visual.material_override=material
	add_child(visual)
	var collision:=CollisionShape3D.new();var shape:=BoxShape3D.new();shape.size=box.size;collision.shape=shape
	add_child(collision)
	var label:=Label3D.new();label.text="SERVICE LINK\n[E] RESTORE POWER";label.position=Vector3(0,.15,.19);label.pixel_size=.0025
	add_child(label)
