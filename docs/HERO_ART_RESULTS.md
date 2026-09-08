# Hero art acceptance — 2026-09-07

**IMPROVED PROTOTYPE. The hero gate is not passed. No second block was generated.**
Continuation preserves b31ee50's batching, mipmaps, navigation tests, benchmark and
PowerShell compatibility. Art checkpoint: 82977c3. Same four-building playable block;
fighter main scene unchanged. No provider calls, credits, model downloads or installs.

## Visual review and work completed

Fresh b31ee50 baseline: `generated/previews/b31_baseline` (11 GPU views).
Final acceptance: `generated/previews/hero_acceptance` (11 GPU views), plus
`generated/previews/playable_rain_q0.png` through `q4.png` for all five presets.
Views cover wide/day, foundry, market, office, night, rain, shelter, service,
robot, dusk/CINEMATIC and LOW. These are actual Godot Forward+ captures, not concept art.

Baseline priorities were repetitive facades, sparse service areas, oversized bright
signs, flat materials, weak entrances and a weak horizon. The existing generator now
adds grouped panes, mullions, sills/transoms, industrial shutters and a service core,
market arcade/awning structure and sign tower, office lobby framing and stepped core.
Trim is quieter; three archetypes remain distinct but still visibly procedural.
All three editable Blender sources and GLBs were actually regenerated and validated.
Material batching and repeated-prop MultiMeshes remain intact.

Original projected Decals provide SERVICE 04, warning paint, drainage stains and repair
patches. Placement follows service/loading/drain locations. A pavement tile replaces
mesh joint strips. Existing benches, barriers, cabinets and service equipment remain;
this is not random scattering or a complete street dressing library.

Surface maps remain 1024 square at a two-meter repeat. Authored relief amplitude is
now 0.6 mm instead of 0.12 mm; normals derive from that analytic height field, not
inferred AI color. Decal color/alpha is 512 square, pavement color 1024. No 4K expansion,
new Comfy inference or fabricated PBR maps. Close views show subtle grain but still
large plain areas; exact periodic edges do not establish natural nonrepetition.

Day lighting is less orange and fog is cooler. CINEMATIC uses longer SSR tracing.
Day forms read better; rain remains uniform streaks over a dark, rather uniform road.
Night/dusk silhouettes read, but pools of light and storefront focal points are weak.
No physical HDR panorama, ray tracing, general rain collision or puddle simulation.
Cloud lighting and wetness ease over time; not every weather parameter has a smooth
transition. Final reflection probe was removed after measurement (below).

Robot turn orientation now interpolates; existing idle/walk blending, rig, animation
and weather hooks are retained. A walking-pose capture shows it in the street.
This is still a technical fixture; still images are not a full motion/foot-slide review.
The 70 m capsule LOD is unchanged and remains an obvious presentation limitation.

Navigation decision: **STREET-ONLY**. Prop clearance, routing/stall and lifecycle tests
pass. The measured 4.22 m entrance approach gap is intentional scope, not solved doorway
navigation. NPC entry routes/interiors are not claimed. Audio layers, shelter zones and
crossfades retain their tested behavior; no new sound sources or subjective listening
acceptance occurred in this art pass.

## Actual performance

RTX 5070 Ti, Forward+, 1280x800, fixed inspection street view, rain at hour 15,
3 s warmup / 9 s collection per process. Benchmark alone disables VSync/frame cap.
Two loaded chunks, one NPC, sixteen city lights. CPU/GPU columns are viewport
render-only timings, not total CPU cost. Frame intervals are wall-clock samples.
VRAM is Godot's reported video-memory estimate in decimal MB, not an external profiler.
No material-change counter is claimed. Short desktop runs are variable and do not
predict a larger world or production frame rates.

| Preset | FPS | Mean ms | p95 | p99 | CPU render ms | GPU render ms | Draws | Objects | Primitives | VRAM MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LOW | 1233 | .811 | 1.727 | 2.491 | .157 | .255 | 93 | 276 | 25398 | 162 |
| MEDIUM | 807 | 1.239 | 2.386 | 2.931 | .265 | .631 | 282 | 464 | 106868 | 236 |
| HIGH | 614 | 1.628 | 2.709 | 3.340 | .317 | .940 | 297 | 479 | 177692 | 336 |
| ULTRA | 520 | 1.924 | 3.011 | 3.683 | .390 | 1.141 | 292 | 474 | 185768 | 406 |
| CINEMATIC | 510 | 1.961 | 3.229 | 3.843 | .369 | 1.246 | 288 | 470 | 205628 | 496 |

| Comparison to b31ee50 | HIGH before / after | CINEMATIC before / after |
|---|---:|---:|
| Mean wall frame ms | 1.087 / 1.628 | 1.333 / 1.961 |
| CPU render ms | .255 / .317 | .294 / .369 |
| GPU render ms | .787 / .940 | 1.029 / 1.246 |
| Draw calls | 299 / 297 | 302 / 288 |
| VRAM MB | 295 / 336 | 447 / 496 |

Added geometry/effects are not free: GPU render time and memory increased. Wall timing
also varied substantially between runs, so this is not an isolated attribution of all
slowdown to art. The largest measured cheap fix removed a low-value ReflectionProbe:
HIGH memory fell 877 to 336 MB; CINEMATIC 1037 to 496 MB. Both captures used the same
art. Do not claim a speedup from this experiment: final wall times were slower.
SSR/sky response remains; glass still needs art work. No dynamic local probe claimed.
LOW visibly loses rain/effects; higher tiers add particles, shadows and screen-space
effects. ULTRA/CINEMATIC remain visually close; CINEMATIC is not a distinct hero look.

Raw final metrics: `generated/reports/world-37853916387542ceba66301e68a60ed8/quality_*.json`.
Probe experiment: `generated/reports/world-0662721976bc4fde9b623e511283c8cb`.
Baseline metrics and method: [HERO_BLOCK_PERFORMANCE.md](HERO_BLOCK_PERFORMANCE.md).
Curated raw copies: `docs/benchmarks/hero_art/`.

## Validation and reproducibility

The complete `tools/test-world.ps1 -SkipGpu` suite passed. Exact auditable count:
23 provider + 3 workflow + 5 multiview + 5 city + 106 building + 21 surface +
43 navigation + 9 material + 9 automation + 121 streaming + 66 environment/audio +
30 gameplay + (286 x 5 stress) = **1,871 passing checks**, zero failures.
Both GPU benchmark invocations repeat 121 + 66 + 30 headless checks: another 434.
**2,305 counted passing checks across these runs; zero remaining failures.**
Repeated checks are not unique tests. The earlier 2,206 summary uses a different
aggregation; no test was removed to obtain this count. Additional uncounted gates:
canonical fighter/worker, character source, fighter/main regression, resource/import,
three Blender pipelines, five GPU presets per sweep, visual capture and artifact audit.
Stress: 100 cycles across five processes; maximum 290 nodes; zero failures/pending at end.

Evidence: `generated/reports/world-regression-fee87f7e2819472db3f8ecc8d4ce93d1`,
`generated/reports/world-e83cb3c5b00e4168bbbe042cc1701e9e`, fighter report
`generated/reports/20260907-172143-308-f3dc61`. Expected rejection tests are successful
when they reject invalid input. Generated logs/screenshots are local ignored evidence.

Resolve PowerShell via `Get-StudioShell` after dot-sourcing `tools/studio-common.ps1`.
Run `tools/world.ps1 benchmark -Weather rain -Hour 15` for the benchmark,
`tools/test-world.ps1 -SkipGpu` for full non-GPU regression, and
`godot --path game --script res://scripts/visual_review.gd -- --review-dir=<absolute-directory>`
for the eleven-view review. Launch the playable block with
`C:\Tools\Godot\godot.exe --path C:\Users\ronan\AI-Game-Studio\game res://scenes/playable_block.tscn`.

## Remaining work and acceptance decision

CRITICAL for hero acceptance: glass has little convincing depth/reflection; facades
and blank horizon still read as simple procedural boxes. Do not increase map size.
MAJOR: richer selective service/storefront dressing; grounded material aging and wet
patch variation; readable night pools; less uniform rain; more distinct cinematic look.
MINOR: sign/detail placement polish, coarse robot proxy and obvious regular repetition.

Visual/architecture work for Astra: redesign one close-view storefront/material module
as the quality reference, then apply its logic to the same three recipes. Review close
day/rain/night images before adding more assets. No second block until this gate passes.

Engineering/debugging work: motion and LOD traversal capture, subjective audio review,
repeat benchmark variance investigation, and targeted decal receiver/bounds tests.
Doorway routing is a separate future feature, not a current street-only bug fix.
Preserve batching, collision/navigation clearance, original fighter and working saves.
