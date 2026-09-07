# Environment production contracts

This stage creates specifications and a small rendering lab, not a city generator.
`tools/templates/environment_world.json` defines world → districts → blocks → lots
→ modular buildings and associated props, decals, materials, lighting, navigation,
and gameplay hooks. Start each kit on a 0.5 m grid, 3 m floor height and 2 m texture
repeat. Match corner/door/window sockets and pivots before producing variants.
Reuse facade bays, foundations, corners, roofs and service components; unique
hero landmarks are exceptions. Roads need intersection sockets, curb continuity,
drain placement and navigable sidewalk widths. Original fictional signs only.

Suggested output locations: design recipes in `docs/environments`, asset manifests
in `tools/assets`, generated wrappers in `game/scenes/assets`, hand-authored chunk
parents in `game/scenes/environments`, materials in the category catalog, source
art in `generated/textures`. A future composer must validate IDs, bounds, sockets,
overlaps, navigation connections and asset budgets before writing any chunk scene.

## Performance

The five environment asset classes in `tools/templates/environment_quality.json`
are initial upper bounds. Screen size determines useful texture resolution; do not
apply 4K universally. Reuse texture/material resources; use trim sheets or padded
atlases for compatible surfaces. Do not atlas unrelated transparency or huge UV
repeat ranges. Keep moving bodies on primitive/convex collision and static shells
on simplified collision; never use render triangles indiscriminately for physics.

Godot frustum culling is automatic for bounded geometry. MultiMesh batches repeated
props, but culls at the whole MultiMesh bounds: split by chunk and spatial cluster.
Use visibility ranges/HLOD for assemblies, mesh LOD for silhouette, and distant
skyline meshes or reviewed impostors. OccluderInstance3D proxies should cover solid
building masses, excluding doors; benchmark occlusion gains before enabling globally.

Proposed 128 m chunks use staged threaded resource loading and main-thread scene
instantiation with a per-frame time budget. Maintain hysteresis around load/unload
radii. Retain gameplay/save state by stable IDs, independently of loaded visuals.
NavigationRegion3D belongs to loaded chunks; bake reviewed walkable surfaces, connect
region edges and disable unload only after agents leave or transfer. Streaming,
HLOD assembly and city navigation are design contracts here, not implemented systems.

## Characters

`tools/templates/character.json` and `docs/characters` reserve the future route:
concept → conditioned views → model → Blender preservation → PBR → rig → animations
→ LOD → CharacterBody3D. Existing provider rig adapters remain intact. Validate bind
pose, skin weights, bone mapping, clips/root motion and deformation before integration.
Do not use the static mesh cleanup path for rigged content. Environment work comes first.

## Next milestone

Build one original modular street corner using a small shared facade kit, one road
intersection and two navigable chunks. Establish frame-time and memory targets before
expanding to a district. This tests reuse, sockets, loading and navigation with gameplay.

## Current implementation supersedes the original planning-only status

The initial lab contract above is retained as architectural context. The implemented
world now uses 64 m cells, a four-building block, bounded serialized streaming,
NavigationAgent3D worker movement, a skinned fixture and playable persistence flow.
See CITY_AND_STREAMING.md, PLAYABLE_BLOCK.md and characters/WORKER_PIPELINE.md.
Arbitrary 2D worlds, streaming memory admission, HLOD assembly and organic character
production remain future work; the three-cell proof must not be described as those systems.
