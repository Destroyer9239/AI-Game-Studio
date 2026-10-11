extends Node3D
## Original cheap scenery beyond the playable corridor; no collision or simulated city.
func _ready()->void:
	var rng:=RandomNumberGenerator.new();rng.seed=719
	var mesh:=BoxMesh.new();mesh.size=Vector3.ONE
	var material:=StandardMaterial3D.new();material.albedo_color=Color(.12,.17,.19);material.roughness=.9
	var batch:=MultiMesh.new();batch.transform_format=MultiMesh.TRANSFORM_3D;batch.mesh=mesh;batch.instance_count=64
	var index:=0
	for side in [-1,1]:
		for column in range(16):
			var width:=rng.randf_range(8,15);var height:=rng.randf_range(18,52);var depth:=rng.randf_range(10,20)
			var x:float=-190+column*22+rng.randf_range(-3,3)
			var z:float=side*rng.randf_range(90,125)
			batch.set_instance_transform(index,Transform3D(Basis.from_scale(Vector3(width,height,depth)),Vector3(x,height*.5,z)));index+=1
			batch.set_instance_transform(index,Transform3D(Basis.from_scale(Vector3(width*.55,height*.18,depth*.7)),Vector3(x,height*1.09,z)));index+=1
	var buildings:=MultiMeshInstance3D.new();buildings.multimesh=batch;buildings.material_override=material
	buildings.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(buildings)
