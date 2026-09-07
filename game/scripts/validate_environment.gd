extends SceneTree

func _initialize() -> void:
	var factory = load("res://scripts/sky_factory.gd")
	for kind in ["physical","procedural","scifi"]:
		assert(factory.create(kind).sky_material != null)
	var texture := load("res://assets/textures/industrial_concrete/industrial_concrete_basecolor.png") as Texture2D
	assert(texture.get_width() == 4096 and texture.get_height() == 4096)
	assert(factory.create("panorama",texture).sky_material is PanoramaSkyMaterial)
	var sun := DirectionalLight3D.new()
	factory.set_time(sun,12.0)
	assert(sun.light_energy > 1.0)
	factory.set_time(sun,0.0)
	assert(sun.light_energy == 0.0)
	sun.free()
	var scene := load("res://scenes/environment_lab.tscn") as PackedScene
	assert(scene != null)
	print("ENVIRONMENT_CONTRACT_PASS: sky factories, day/night hook, 4K imported texture, scene")
	quit()
