# Hero block engineering measurement

Engineering record for the hero-block pass. Architecture and art direction stay
in `HERO_BLOCK_REVIEW.md`, `CITY_AND_STREAMING.md` and `ENVIRONMENT_*`; this file
only records how the block was measured, what the numbers were and which
engineering defects were found or fixed.

## Benchmark method

`pwsh|powershell -NoProfile -File tools/world.ps1 -Action benchmark -Weather rain -Hour 15`
runs the five quality presets in sequence against `res://scenes/playable_block.tscn`
with `--rendering-method forward_plus`. Each preset process receives
`--weather --hour --quality --inspection --benchmark --capture --report`.

- `--benchmark` sets `DisplayServer.VSYNC_DISABLED` and `Engine.max_fps = 0`, and
  enables `RenderingServer.viewport_set_measure_render_time`. It affects only the
  benchmark process; the shipped project settings and the `1`–`5` in-game quality
  keys are untouched.
- `--inspection` places the player at `(22, .35, 6)` looking at `(-14, 2, -1)`:
  one fixed street view with no input, so the camera is identical every run.
- `--hour` fixes the time of day, so sun angle, sun energy and the city-light
  ramp are the same across presets and across runs.
- Sampling starts after a 3 s warm-up and the capture/report is written at 12 s,
  giving a ~9 s window (6.7k–10k frame samples per preset).
- Runs are windowed, not headless, on the real Vulkan device. Headless
  (`--headless`) uses the dummy renderer: it reports no GPU timings and no
  meaningful draw-call counts, so it is used for logic tests only.

Reported metrics come from `Performance` monitors and `RenderingServer` viewport
measurement. Nothing is modelled or extrapolated. `frame_ms_*` are wall-clock
main-thread intervals; `cpu_render_ms` / `gpu_render_ms` are render-only times and
are zero unless `--benchmark` enabled measurement. Counters are sampled at the
capture frame for the fixed view, so they describe this street view, not a city.

## Measured results

Machine: NVIDIA GeForce RTX 5070 Ti, Vulkan 1.4.325, Forward+, 1280x800 window.
Scene: rain, hour 15, 2 loaded cells, 1 NPC, 16 city omni lights, 6 audio players.
Run `generated/reports/world-1d4f96749eaf4154abd9ad0ade43615c`.

| preset | FPS | frame ms mean | median | p95 | p99 | max | CPU render ms (mean/p95) | GPU render ms (mean/p95) | draw calls | render objects | primitives | VRAM |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| LOW (0) | 2010 | 0.498 | 0.481 | 0.665 | 0.813 | 1.646 | 0.124 / 0.171 | 0.215 / 0.243 | 93 | 274 | 19,558 | 129 MB |
| MEDIUM (1) | 1239 | 0.807 | 0.784 | 1.017 | 1.200 | 2.154 | 0.216 / 0.270 | 0.513 / 0.667 | 280 | 461 | 89,970 | 200 MB |
| HIGH (2) | 920 | 1.087 | 1.060 | 1.318 | 1.501 | 3.679 | 0.255 / 0.318 | 0.787 / 0.943 | 299 | 479 | 161,448 | 295 MB |
| ULTRA (3) | 790 | 1.266 | 1.235 | 1.511 | 1.671 | 3.709 | 0.294 / 0.368 | 0.962 / 1.117 | 305 | 485 | 169,028 | 362 MB |
| CINEMATIC (4) | 750 | 1.333 | 1.301 | 1.583 | 1.777 | 2.502 | 0.294 / 0.372 | 1.029 / 1.190 | 302 | 482 | 192,296 | 447 MB |

Preset contents are recorded in each report's `preset` block (MSAA, TAA, 3D scale,
SSAO/SSR/SSIL/glow/volumetric fog, sun shadows, shadow distance, rain particles),
so a cheap number cannot be mistaken for a disabled feature. Node count (252),
resource count (149), shadow-casting lights (1 sun; 0 at LOW) and the audio census
(6 players, 5 playing) are identical across presets.

The block is GPU-bound at this resolution. Wall FPS is not the useful figure here;
CPU render time and draw calls are, because they are what scales with block count.

## Draw-call verification

Astra reported the same street view falling from ~1086 to ~501 draw calls. Verified
by checking out `f6b5667` into a temporary worktree, importing it separately and
running the same view at quality 2:

| | f6b5667 baseline | 5b25b70 (Astra) | this pass |
|---|---|---|---|
| draw calls | 1105 | 490 | 299 |
| render objects | 1307 | 670 | 479 |
| primitives | 117,528 | 156,264 | 161,448 |
| VRAM | 393 MB | 293 MB | 295 MB |
| frame ms mean | 6.944 (refresh-limited) | 1.100 | 1.087 |

The reduction is legitimate: primitives went **up** 37% while draw calls fell 73%.
Nothing is hidden or unrendered. Confirmed independently at the asset level by
loading both GLB sets through `GLTFDocument`:

| building | baseline mesh instances | current | baseline triangles | current |
|---|---|---|---|---|
| foundry | 102 | 14 | 2,856 | 3,264 |
| market | 70 | 14 | 2,024 | 2,148 |
| relay | 185 | 14 | 5,292 | 5,548 |

Materials per building went 6 to 7 (the new `Painted_Accent`); each batched
surface still carries its own material. Sun shadows were confirmed rendering by
capturing clear weather at hour 9 — buildings, benches, bollards and lamp posts
all cast. At hour 12 the sun is directly overhead, which is why the noon capture
looks shadowless; that is geometry, not a lost shadow map.

`test_streaming.gd` now guards this permanently: per-building mesh instance count
must stay ≤ 20, every surface must keep a material, and the four buildings
together must still carry ≥ 10,000 triangles.

## Performance fixes made in this pass

1. **Instanced street furniture** (`game/scripts/city_chunk.gd`). Ten families of
   repeated collision-less props — lamp posts, lamp arms, lamp heads, drains, lane
   marks, bollard stripes, bench feet, crate bands, pavement joints (62 of them)
   and crosswalk stripes — were one `MeshInstance3D` each. They are now one
   `MultiMeshInstance3D` per family: 135 nodes to 10, identical geometry,
   transforms and materials. Props with collision are untouched, so the navigation
   footprints are unchanged.
   Measured at quality 2: draw calls 490 to 299, render objects 670 to 479, CPU
   render time 0.306 ms to 0.255 ms (-17%), max scene nodes in the streaming stress
   283 (was 719 at the last recorded checkpoint). GPU time and appearance unchanged.
2. **Mipmaps on the hero surface maps**. `normal/roughness/aggregate.png` imported
   with `mipmaps/generate=false` while `city_chunk.gd` asks for
   `TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC` on the largest surfaces in the
   view (road and sidewalks, world triplanar). Filtering requested a mip chain that
   did not exist. Now generated, matching the building maps exported from Blender.
   Cost: ~2 MB VRAM at quality 2.

## Engineering defects found

- `tools/studio-common.ps1` used `ProcessStartInfo.ArgumentList`, which only exists
  on PowerShell 7. No `pwsh` is installed on this machine, so every entry point
  failed immediately under Windows PowerShell 5.1. Fixed with an argument-quoting
  fallback plus a `Get-StudioShell` resolver for nested `pwsh` calls; the pwsh path
  is unchanged when pwsh is present.
- The navigation mesh spans z ∈ [-8, 8] while the designed building entrances sit
  at |z| ≈ 11.7. The closest reachable navigation point to a door is **4.22 m**
  away, so an agent cannot currently route to a building entrance. Recorded by
  `test_hero_navigation.gd`, which asserts the approach gap stays under 6 m.
- `height_amplitude_m` of 0.00012 quantises to a near-flat 8-bit normal map: R and
  G span only 123–132 of 255 and B is 255 everywhere (max implied slope 0.045).
  The map is technically valid and the tests pass, but it costs 526 KB and a
  texture fetch for a shading effect that is close to invisible. Amplitude is an
  art decision — flagged, not changed.
