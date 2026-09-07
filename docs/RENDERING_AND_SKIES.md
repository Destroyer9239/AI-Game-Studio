# Rendering and sky lab

The installed engine reports **Godot 4.7.2 stable**, build `ed1daf0bf`, and the actual
GPU lab reports Vulkan / Forward+ on NVIDIA RTX 5070 Ti. `report_render_capabilities.gd`
records installed ClassDB properties and project settings in ignored reports. The
original fighter main scene is preserved. Desktop defaults to Forward+; mobile keeps
the compatibility fallback. CLI `--rendering-method gl_compatibility` remains available
for the original fighter; the environment launcher explicitly selects Forward+.

Run `pwsh -NoProfile -File tools/environment.ps1 benchmark -Quality HIGH -Instances 100`.
Use `launch` for interactive inspection: 1–5 switches quality, arrows orbit, Esc exits.
The lab combines packed PBR concrete, directional and point light shadows, physical
sky/environment reflection, a box-projected ReflectionProbe, SSR, SSAO, optional SSIL,
volumetric fog, glow, MSAA/TAA, an original caution decal and GPU dust. It is a small
measurement scene, not evidence of a full city frame rate. No hardware ray tracing
or Unreal-specific feature is claimed. SDFGI and baked GI are future scene-dependent
choices, not enabled or benchmarked here.

LOW disables screen effects/particles; MEDIUM enables SSAO/glow/particles; HIGH adds
SSR, volumetric fog and 4× MSAA; ULTRA adds SSIL/TAA and 128 SSR steps; CINEMATIC adds
8× MSAA. Project directional shadows use a 4096 atlas and anisotropic filtering is
set to 16× with the lab materials opting in. Texture memory and aliasing must still
be inspected at oblique angles; presets do not justify 4K textures everywhere.

Each bounded benchmark warms up for at least two seconds/120 frames and records at
least two seconds/240 subsequent wall-clock
frame intervals, mean/p95 milliseconds, draw calls, rendered objects, video memory,
adapter and renderer. Logs and JSON live in `generated/reports/environment-*` and GPU
captures in `generated/previews/environment_<QUALITY>.png`. These are CPU-observed
frame intervals; GPU timestamps, long thermal runs and streaming stress are not measured.
Use identical resolution, instance counts and background workload for comparisons.

## Skies

`game/scripts/sky_factory.gd` creates physical, procedural, supplied panorama or custom
sci-fi skies. `set_time` provides a simple day/night sun direction/energy hook; it is
not geographic/astronomical simulation. The lab uses PhysicalSkyMaterial and actual
environment lighting. The custom shader is an original artistic gradient/atmospheric
band. Future profiles can combine sky, sun, fog and exposure as a coherent resource.

PanoramaSkyMaterial accepts a supplied Texture2D. Real `.hdr`/`.exr` environments may
contain high dynamic range radiance; verify source/license/exposure and orientation.
SDXL PNG sky art is LDR reference, not calibrated HDR illumination and not guaranteed
equirectangular or pole/seam-correct. The sky-reference workflow is labeled accordingly.
Do not rename an ordinary PNG to EXR and claim physical HDR. A future panorama route
needs projection-aware stitching, seam/pole review, and separate lighting calibration.

References: [official renderer feature table](https://docs.godotengine.org/en/latest/tutorials/rendering/renderers.html)
and installed ClassDB report. Online latest documentation may include differences;
the installed engine's runtime and successful lab checks are the capability evidence.
