shader_type spatial;
render_mode unshaded, cull_disabled;
uniform vec4 shelter_bounds[8]; // center X/Z, half width/depth in world meters
uniform int shelter_count=0;
uniform float shelter_roof_y=3.15;
varying vec3 world_position;
void vertex() { world_position=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz; }
void fragment() {
	for(int i=0;i<8;i++) {
		if(i>=shelter_count) break;
		vec4 b=shelter_bounds[i];
		if(world_position.y<shelter_roof_y && abs(world_position.x-b.x)<b.z && abs(world_position.z-b.y)<b.w) discard;
	}
	ALBEDO=vec3(0.35,0.55,0.7);
	ALPHA=0.4;
}
