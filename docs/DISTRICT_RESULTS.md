# Bounded district continuation — 2026-09-09

**Status: PROTOTYPE. Third block withheld at the visual repeatability gate.**
Block 1: IMPROVED_PROTOTYPE. Block 2: PROTOTYPE (weaker). Block 3: NOT GENERATED.
This is a tested foundation checkpoint, not completion of the requested district milestone.

## Recovered and completed

Recovered compressed texture imports in b18183d after full regression and a fresh GPU
launch. See DISTRICT_RECOVERY.md. The original fighter main scene and single-block
fixtures remain intact. Three building sources were regenerated with window-local UVs,
exported from Blender and imported/tested/rendered in Godot. New opaque window-room
shading uses view-dependent box projection to suggest interior depth; no modeled rooms,
transmission, calibrated interior lighting or reflection probe is claimed. Shell UVs
still repeat every two meters. Window UV bounds and material preservation have two new
Blender assertions. All existing 1K surface/512px decal resolutions remain unchanged.

tools/world/generate_district.py consumes district_spec.json and writes a separate
district.json and generated chunk scenes. The accepted city_block.json is untouched.
Seed 4821, west seed 4822, center seed 2914. Eight Python tests cover determinism,
seed variation, original block preservation, all four template plans, matching road
sockets and invalid budgets/IDs/road widths. Current supported road is explicitly a
64 m straight corridor cell with an 8 m road; unsupported dimensions reject.

Templates: main_street, industrial_service, alley_backside, plaza_open. Only the first
two are instantiated and visually reviewed. The latter two are data-level templates,
not finished scenes. Lots contain bounds, setback, frontage, height limit, service and
entrance classification. Validation rejects overlapping/out-of-cell lots and corridor
overlap. Asset families currently reuse the existing foundry/market/office models;
the generator does not yet produce different-height sibling models per family.

Two real blocks use six buildings, reusing the same three assets. Eight contextual
loading/utility meshes and two warning/repair decals dress the west service space.
The serialized streamer now accepts an optional world specification/scene directory;
its original loading, cleanup, hysteresis and resource ownership remain intact.
Road and sidewalk edges align at x=-32. Runtime navigation tests traverse that edge.
Ten unload/reload cycles per district test preserve a block event and enforce load
bounds. Central terminal, worker, objective and original gameplay continue through the
shared playable parent. Default district saves use studio_district_save.json, avoiding
the original studio_block_save.json. Explicit regression save paths are preserved.

## Visual acceptance

Actual eleven-view first-block GPU set: generated/previews/district_gate.
Actual six-view two-block set: generated/previews/district_two (both blocks and overview,
clear/rain). The market close-up shows room depth. The overview exposes the weak point:
the industrial block is two identical foundries with excessive empty land and overly
simple machinery. Adding a composed loading group improved context but did not close
the quality gap. Block 1 is strongest; Block 2 is weakest. No third block is warranted.
Rain and shared palette remain coherent, but no new skyline/night art standard exists.

## Honest scope limits

- No accessible entrance approaches yet: generated doors are explicitly DECORATIVE_ENTRANCE.
  Sidewalk/cross-block road routing works; doorway, alley and activity routing remain.
- No additional active NPCs: spawn/activity/gameplay coordinates are hooks, not new AI.
  The existing central worker retains time/weather behavior and persistence.
- World weather remains shared. Existing road wetness and lighting work across both
  cells; per-material roof/glass wetness responses are not newly implemented.
- Existing global ambience and central local audio are retained. New block-specific
  machinery layers, location crossfades and listening acceptance remain undone.
- max_loaded and generation building budget are enforced. NPC/shadow budget entries
  are design limits, not a new runtime admission controller. No general 2D road network,
  intersections, landmark, skyline or debug bounds overlay has been implemented.
- No three-block benchmark exists. Do not relabel two loaded cells as three blocks.
- No new Comfy inference, paid provider, model download, Meshy/Gemini/Higgsfield or Claude.

## Measured acceptance

Fixed camera/player (-20, .35, 6), looking toward (-65, 2, -1), 1280x800 Forward+,
rain/hour 15, VSync off and no FPS cap only in benchmark mode. Three-second warmup,
nine-second measurement. Both cases load west and center: reference has one built
block plus an empty service cell; district has two built blocks. One NPC and sixteen
city lights in both cases. CPU/GPU times are render-only, not complete engine timings.

| Scene | Quality | FPS | Mean ms | CPU render ms | GPU render ms | Draws | Objects | Primitives | VRAM MB |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| One block | HIGH | 1071 | .934 | .184 | .648 | 113 | 283 | 122466 | 309 |
| Two blocks | HIGH | 998 | 1.002 | .218 | .704 | 190 | 372 | 146952 | 304 |
| One block | CINEMATIC | 868 | 1.153 | .216 | .862 | 98 | 267 | 153520 | 468 |
| Two blocks | CINEMATIC | 818 | 1.223 | .239 | .937 | 181 | 363 | 182720 | 463 |

Nodes: 258 reference / 314 district. Resources: 154 in each. Reported video memory
is a Godot counter in decimal MB, not a driver residency measurement. Lower measured
memory does not prove that adding blocks saves memory. Desktop noise and view-dependent
allocations vary. No collapse at two blocks; no three-block conclusion is supported.
Raw metrics retained under docs/benchmarks/district/ with p95/p99 and full counters.

Earlier district benchmark attempts were rejected: the original camera loaded only
one block, and a subsequent unfrozen reference loaded three cells. The final benchmark
disables player physics/input movement, records exact position and loaded IDs, and the
helper requires two loaded cells. Those invalid attempts are excluded from this table.
The original five-preset GPU sweep also passed (world-3c0a77e340194c658f10685fd48d8ccc).

Full existing regression: **1,873 passing checks** (108 building checks now), zero
remaining failures; plus **8 district Python tests and 34 runtime checks = 1,915**.
Repeated benchmark/helper invocations are excluded from that count. Original streaming
stress passed 100 cycles across five processes. Every district runtime invocation
performs ten unload/reload cycles; all four final comparison processes passed them.
Blender export, fighter/main, resource/import and actual GPU gates are additional.
Final artifact audit: 413 candidate files, zero issues.

Reports: world-regression-7aa95d6420d34882a873120d112102d4 and
world-b06bd9f05271451d9311aa896f3cff88. Final comparison reports:
district-c504f7627c754eca94e293e66f223719,
district-bbf582d6f91b4a2080a771f01e1041a2,
district-d53c54e9292e445f9cdb4d5cb4c00783,
district-11c534234d504cffa8ef28236e05dd77.

## Agent commands

Use tools/district.ps1 with generate, validate, preview, benchmark -Quality 2 or 4,
or launch. Dot-source tools/studio-common.ps1 and use Get-StudioShell when pwsh is absent.
All operations validate the generated contract and Godot runtime. Original world tools
retain their existing behavior. tools/test-world.ps1 now includes the district checks.

## Next work

Before any third block: develop a credible industrial service composition with a
different building-family silhouette and richer functional machinery; compare against
Block 1 at the same camera scale. Then implement accessible entrance aprons and routes,
block ambience/NPC activity, third-block acceptance and the requested district benchmark.
Do not spend more space to conceal sparse art. Preserve working systems and checkpoints.
