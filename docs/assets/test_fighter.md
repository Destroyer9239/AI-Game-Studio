# test_fighter — Kestrel / 01

Original faceted sci-fi fighter used as the studio regression fixture. Broad swept wings, tapered nose, framed teal cockpit, paired dorsal fins and rear cyan ion engines. Blender +Y forward/+Z up; meters; approximately 8.3 m wide × 6.6 m long. Centered near its fuselage for turntable rotation.

Runtime budgets: 12,000 triangles and 8 unique materials. Preserve named components and both emissive engines listed in `tools/assets/test_fighter.json`. Solid embedded PBR materials need no texture UVs. Simplified collision-only fuselage is suitable for this stationary presentation; a moving gameplay fighter needs an appropriate physics body and collision coverage for its wings/engines.

The original `test_fighter_scene.tscn` remains the main scene. Automation additionally creates a reusable asset wrapper under `game/scenes/assets/` and a framed preview using the shared asset preview scene. Acceptance: import, all resource loads, original turntable regression, main runtime, generic geometry/material/collision budgets and actual GPU preview must pass.
