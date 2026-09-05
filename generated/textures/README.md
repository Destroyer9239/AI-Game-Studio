# Texture authoring sources

Use per-asset folders with `basecolor`, `roughness`, `metallic`, `normal`, `emission` and optional `decal` sources. Keep source metadata and raw generated artwork separate from curated runtime maps in `game/assets/textures/<asset>/`.

Base color/emission use sRGB; roughness/metallic/normal data use non-color/linear interpretation in Blender. AI appearance images are not calibrated material maps: derive and inspect masks, bake normals from real geometry where useful, and check tiling with a repeated grid. A text prompt saying “seamless” is not sufficient. Review transparency, edge bleed, UV density and texture dimensions before export.
