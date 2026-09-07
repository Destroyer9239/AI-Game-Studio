extends RefCounted
## Artistic PNG panoramas stay LDR; radiometric HDR requires real EXR/HDR data.
static func create(kind: String, panorama: Texture2D = null) -> Sky:
	var sky := Sky.new()
	match kind:
		"physical":
			sky.sky_material = PhysicalSkyMaterial.new()
		"procedural":
			sky.sky_material = ProceduralSkyMaterial.new()
		"panorama":
			assert(panorama != null, "Panorama requires a supplied texture")
			var material := PanoramaSkyMaterial.new()
			material.panorama = panorama
			sky.sky_material = material
		"scifi":
			var material := ShaderMaterial.new()
			material.shader = load("res://shaders/scifi_sky.gdshader")
			sky.sky_material = material
		_:
			push_error("Unknown sky kind: "+kind)
	return sky

static func set_time(sun: DirectionalLight3D, hour: float) -> void:
	sun.rotation_degrees.x = (fposmod(hour,24.0)-6.0)*-15.0
	sun.light_energy = maxf(0.0,sin((hour-6.0)*PI/12.0))*1.4
