# Canonical views and modular building foundation

The earlier SDXL view set remains rejected. The new local route derives all views
from one original Blender source. `render_multiview.py` renders front, left, right,
rear, top, bottom and two three-quarter views with one scale, identical geometry,
materials and lighting. `tools/world/multiview_fighter.json` defines dimensions,
required components, palette, markings and orientation. Output camera poses, source
and image hashes live in `generated/references/canonical_fighter/package.json`.

`multiview_gate.py` returns PASS, REJECT or NEEDS_REGENERATION. Missing visual review
means review is required, not an instruction to regenerate blindly. Different geometry,
changed sources/images, incomplete/stale reviews or failed visual criteria reject.
The renderer conservatively rejects FONT objects and image-textured materials, preventing
unreviewed text/pseudo-branding in this controlled route. This is not a general OCR or
image-understanding detector. Arbitrary external images still require visual inspection.

All eight canonical fighter views were inspected and passed. This proves consistent
references for that existing design, not automatic reconstruction of an SDXL concept.
The gate has five passing regression tests including contradictions and marking failure.

```powershell
blender --background --factory-startup --python-exit-code 1 --python blender/scripts/render_multiview.py -- --spec tools/world/multiview_fighter.json
py -3.11 tools/world/multiview_gate.py generated/references/canonical_fighter/package.json --review generated/references/canonical_fighter/visual_review.json
pwsh -NoProfile -File tools/pipeline.ps1 test-pipeline -Asset foundry_building
```

Use the existing executable resolver when short commands are absent. The building
generator consumes a seeded JSON recipe. Footprint/floors/palette/quality/archetype
drive geometry; archetypes control facade bay spacing and rooftop equipment density.
Age/wealth/district/function are recorded design context, not simulated urban economics.
HERO/NEAR/STANDARD retain facade detail; BACKGROUND/DISTANT simplify to shell/cap.
Interiors, balconies, garage variations and damage remain extension points, not finished
content. Each sample has a single logical entrance, collision and navigation anchors.

Foundry: original 12 × 10 m three-story industrial office, shared authored PBR,
centered front canopy, corner columns, floor ledges and two roof HVAC modules. It
passes actual Blender/GLB/Godot/material/collision/render checks. Eight recipe checks
cover same-seed reproduction, changed-seed variation, one centered entrance, cheaper
distant form and invalid-spec rejection. Geometry placements are hashed; Blender file
bytes need not match because serialization contains incidental metadata.

This is a working modular building foundation with a visually reviewed example.
Block composition, streaming, weather/audio and character/gameplay integration are next.
