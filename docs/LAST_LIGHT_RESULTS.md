# Last Light checkpoint — 2026-10-10

Status: IMPROVED PLAYABLE PROTOTYPE, not AAA or hero-quality art.
Preserved before the user's subsequent Unreal Engine migration request.

The existing two-block district now supports a complete short repair mission:
west relay, central service link, extraction. There is a start/settings menu,
objective markers, autosave, reload and an ending. Separate save slots preserve
the original fixtures. Last Light is the Godot main scene; the fighter is retained.
Play-Last-Light.cmd launches using the existing installed Godot, not a standalone build.

Six original-source CC0 Poly Haven maps (asphalt_02 and brushed_concrete), 2048 square,
76,628,380 bytes total, were acquired and verified against API hashes. Provenance,
source URLs and SHA256 are adjacent to the textures. Compressed GPU imports and
mipmaps are enabled. These are supplied basecolor/normal/roughness maps, not inferred
PBR from a color image. Concrete now also shades mineral facades. A single 64-instance
MultiMesh adds non-playable skyline scenery. No new playable blocks were generated.

Full regression world-regression-2670727e7ada4aa793cd7250ff11adee passed 1,929
counted tests/assertions, including 14 new mission checks and 100 streaming cycles
across five processes. A subsequent cursor-capture regression adds one mission check;
the updated 15-check mission suite passed in the final GPU review helpers.
Blender source/export checks, fighter, Godot import/resources and main runtime also
passed. Live Comfy inference was not repeated. A navigation readiness test was fixed
to await bounded asynchronous map publication rather than assume five frames suffice.
Main runtime validation now frees the streamed scene before shutdown.

All five quality screenshots were actually inspected. Native 3840x2160 output was
verified after fixing a 16:10 viewport mismatch. LOW internally renders at 75% linear
resolution; other presets use 100%. Benchmark: RTX 5070 Ti, Godot 4.7.2 Forward+,
fixed street camera, two loaded cells, one NPC, rain at 17.5h, 3-second warmup and
9-second sample; VSync/cap disabled only for measurement. CPU/GPU are render-only.
Raw results: docs/benchmarks/last_light/quality_*.json.

| Quality | FPS | Mean ms | p95 ms | p99 ms | CPU render ms | GPU render ms | Draws | Video MB |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| LOW (upscaled) | 763.3 | 1.310 | 2.389 | 3.024 | .141 | .724 | 63 | 317.2 |
| MEDIUM | 282.8 | 3.537 | 4.816 | 5.442 | .296 | 2.898 | 216 | 632.9 |
| HIGH | 194.3 | 5.147 | 6.581 | 7.291 | .386 | 4.382 | 232 | 1337.4 |
| ULTRA | 149.9 | 6.670 | 7.977 | 9.221 | .452 | 5.949 | 227 | 1854.8 |
| CINEMATIC | 137.1 | 7.293 | 8.842 | 9.755 | .463 | 6.479 | 223 | 2556.9 |

These short desktop measurements do not predict full-game performance. Render target
and effect costs dominate higher presets; no broad engine bottleneck claim is made.
The largest practical win was compressed/mipmapped textures, without discarding detail.

Remaining art blockers: repeated facades, sparse streets, crude skyline silhouettes,
simple rain streaks, decorative doors, basic robot and limited material diversity.
Audio/weather/navigation fixtures remain functional; no new professional audio,
full interiors, campaign, combat, final characters or general city simulation is claimed.
Settings are basic; standalone packaging and long traversal acceptance remain.
No paid credits, new models, Meshy, Gemini, Higgsfield or Claude were used.

Next direction is Unreal Engine 5 at the user's request. Preserve this working
Godot version as the behavior and asset reference, not the migration target engine.
