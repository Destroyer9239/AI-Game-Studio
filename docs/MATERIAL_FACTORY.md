# Local 4K material workflow

Run `pwsh -NoProfile -File tools/pipeline.ps1 image-4k -RequestFile
tools/providers/requests/industrial_concrete_source.json` (one command line).
The explicit ComfyUI provider is required. It generates a 1024-square SDXL source,
then uses core UpscaleModelLoader / ImageUpscaleWithModel and RealESRGAN_x4plus to
produce 4096 × 4096. Core upscaling uses 512-pixel tiles with 32-pixel overlap and
reduces tile size on VRAM pressure. This is learned detail reconstruction, not
native 4K diffusion or proof of additional physical detail. No paid fallback exists.

The square route rejects non-square references: explicitly compose/pad those before
upscaling rather than distort the subject. The low-level API graph can request other
dimensions, but the reusable 4K command enforces the tested square composition.
Concept, environment, decal and UI requests use the same source/upscale route;
alpha extraction and perspective/orthographic correctness remain separate reviews.

`pwsh -NoProfile -File tools/environment.ps1 material` processes the last concrete
4K manifest. `build` continues through Blender, GLB, Godot checks and Forward+ preview.
`validate` checks texture hashes, dimensions, exact opposite edges and Godot resources.

## What the concrete package means

Basecolor is SDXL appearance processed with smooth 256-pixel opposite-edge blending.
The repeated preview has been inspected: no hard outer boundary, but recurring panel
joints remain visible. This is appropriate for a panelled wall/floor demonstration,
not a natural nonrepeating terrain texture. Some joints are baked into color only.
Edge equality is necessary but not sufficient for artistic seamlessness.

Normal and optional height describe an authored periodic 0.15 mm microrelief signal.
They are not AI-recovered geometry. Normal uses OpenGL tangent convention; roughness
is artist-selected .82; metallic is dielectric constant zero. AO is omitted because
there is no geometry bake. Emission is absent on concrete. Authored cyan strip geometry
uses a separate emissive material; graphite beams use metallic .85 / roughness .32.

Basecolor is sRGB. Normal/roughness are linear data. Blender packs images, uses a
Normal Map node and explicit two-meter UV repeats, then GLB embeds basecolor, normal
and packed metallic/roughness. Automated tests inspect embedded 4096 PNG dimensions
and material links, followed by actual Godot rendering. Height is a source map only;
no displacement is enabled. No calibrated map-extraction model has been installed.

The catalog `tools/materials/catalog.json` reserves metal, concrete, urban, sci-fi and
environment recipes. Only the concrete recipe and authored steel/emission example
are implemented. Add a reviewed map recipe for each new material: metallic masks
must reflect exposed conductive material, roughness values need lighting review,
AO needs a meaningful bake, and emission needs a defined luminous surface.

## Provenance and cost

`generated/manifests/industrial_concrete_source.json` and `_4k.json` preserve prompts,
seeds, model/source, workflow hashes, output hashes, timings, GPU samples and zero-credit
cost. `game/assets/textures/industrial_concrete/material.json` records processing/maps.
Ignored raw jobs preserve full requests and job IDs locally; curated runtime files and
manifests are versioned. Regeneration is available through the full command above.

Initial measured base: 11.14 seconds, 1024², 30 steps, sampled GPU peak 13,195 MiB.
Initial upscale: 7.281 seconds, 4096², sampled GPU peak 9,392 MiB. Samples include other
applications and are not allocator peaks. Cached reruns and warm-up differ.
