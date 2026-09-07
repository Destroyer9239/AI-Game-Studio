shader_type sky;
uniform vec3 zenith : source_color = vec3(0.005,0.009,0.035);
uniform vec3 horizon : source_color = vec3(0.08,0.15,0.23);
void sky() {
    float altitude = clamp(EYEDIR.y,0.0,1.0);
    COLOR = mix(horizon,zenith,pow(altitude,0.4));
    float band = exp(-pow((EYEDIR.y-0.3)*18.0,2.0));
    COLOR += vec3(0.02,0.035,0.06)*band;
}
