shader_type spatial;
// Original opaque room illusion, not a modeled interior or a transmission material.
// Window-local UVs describe one room; view-dependent box intersection gives parallax.
uniform vec3 glazing : source_color = vec3(0.025, 0.060, 0.071);
void fragment() {
    vec3 origin = vec3(UV * 2.0 - 1.0, 1.0);
    vec3 ray = vec3(dot(-VIEW,TANGENT), dot(-VIEW,BINORMAL), -max(abs(dot(VIEW,NORMAL)),0.05));
    ray = normalize(ray);
    vec3 safe_ray = sign(ray + vec3(0.00001)) * max(abs(ray),vec3(0.0001));
    vec3 travel = (sign(safe_ray) - origin) / safe_ray;
    float distance_to_wall = min(travel.x,min(travel.y,travel.z));
    vec3 room = origin + ray * max(distance_to_wall,0.0);
    vec3 walls = vec3(0.085,0.10,0.105);
    if (abs(room.y)>0.999) walls = room.y>0.0 ? vec3(0.13,0.14,0.14) : vec3(0.045,0.04,0.035);
    float rear = 1.0-smoothstep(-0.999,-0.97,room.z);
    float shelf = (1.0-smoothstep(0.018,0.035,abs(room.y+0.35))) * rear;
    float lamp = (1.0-smoothstep(0.025,0.065,abs(room.y-0.64))) * (1.0-smoothstep(0.35,0.6,abs(room.x))) * rear;
    float edge = smoothstep(0.78,1.0,max(abs(origin.x),abs(origin.y)));
    ALBEDO = mix(walls*(1.0-shelf*0.65),glazing,0.55+edge*0.35);
    EMISSION = vec3(0.8,0.65,0.42)*lamp*0.32;
    ROUGHNESS = 0.19;
    METALLIC = 0.0;
    SPECULAR = 0.7;
}
