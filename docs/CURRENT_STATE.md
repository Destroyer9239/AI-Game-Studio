# Current checkpoint

The interrupted local image/material/environment stage is complete in `8c1656d`,
already present on the existing GitHub origin/main. A normal push confirmed it is
up to date. Godot resource/main/fighter validation, 23 provider tests, 9 material
tests and the 220-file credential/artifact audit passed again on continuation.
Earlier live ComfyUI/4K/Blender/GPU evidence is retained; no accepted assets were
regenerated just to repeat that work. See STUDIO_STAGE_RESULTS.md for the full record.

Godot's editor normalized project.godot by omitting default Forward+ and 4096-shadow
settings. The remaining effective configuration still passes validation. Keep this
normalization rather than fight the editor's serializer.

Next work: deterministic canonical Blender multiviews and modular building recipes,
then a small city block, streaming, connected weather/audio and character/gameplay.
No external generation or new provider setup is authorized. Meshy remains user-key
detected / HTTP 401; Gemini and Higgsfield are not connected. No credits spent.

Checkpoint 2: canonical fighter multiviews passed structural and visual review, with
five gate tests. The foundry building passed eight recipe checks and its complete
Blender/GLB/Godot/render pipeline. See MULTIVIEW_AND_BUILDINGS.md. Next: small block
composition and bounded streaming. No paid services used.

Checkpoint 3: four-building Cinder Exchange block and two service cells. Industrial,
commercial and office recipes exported/imported/rendered. Eleven real streaming checks
pass (duplicate prevention, load/unload, state restoration, collision/navigation and
cell budget). Final overview inspected after correcting entrances to face the street.
See CITY_AND_STREAMING.md. Next: connected environment/weather/audio, then playable
character/gameplay integration. Corridor streaming is intentionally bounded, not a
complete arbitrary large-world solution.

Checkpoint 4: EnvironmentDirector connects data-driven weather/time to sky color,
sun/city lighting, fog, particles, gradual road wetness and audio signals. Layered
procedural ambience, local machinery, seeded one-shots and spatial shelter zones work.
Thirteen state/audio-zone checks and five synthesized-waveform checks pass; rainy and
clear GPU views inspected. Explicit audio shutdown fixes resource lifetime during cell
unload/tests. Current art/audio remain prototype quality; no professional sound assets
or physically calibrated HDR are claimed. Next: actual player, rigged fixture, NPC,
interaction/objective/save/event foundations and integrated playable acceptance.

Continuation checkpoint 1 (2026-09-07): recovered all character/gameplay working files.
Serialized shared-resource requests before main-thread cell instantiation; queued
out-of-range requests cancel, active requests drain/discard and shutdown drains owned
work. Prior intermittent dummy-renderer RID failure occurred with overlapping resource
loads/scene creation; concurrency is the suspected trigger, not a proven engine root
cause. Five separate stress processes passed 203 assertions each / 20 cycles each
(100 cycles total), maximum 719 nodes, 3 loaded / 0 pending / 0 failures at completion.
Worker and terminal persistence, navigation region budgets and current weather on
reload passed. Headless gameplay 17 checks, streaming 11 and environment 13 passed.
Robot source validation and eight canonical reference views passed; actual first-person
GPU render inspected. Original fighter main scene remains unchanged. Next: harden save
schema and gameplay interfaces, then all-quality integrated regression and documentation.

Checkpoint 2: gameplay state validation rejects malformed save structures before world
mutation. Shared interactable implements terminal/switch/door/pickup state and damage
hooks; terminal uses it. Event-driven objectives support activation/progress/completion/
failure. Runtime InputMap defaults come from world/controls.json. Gameplay now passes
28 checks including advancing animation playback, invalid saves and interaction hooks.
Two more 20-cycle persistence stress processes passed. Master pipeline exposes world-test,
world-stress, world-benchmark and world-launch; the original fighter main scene is preserved.

Checkpoint 3/4 integration: player-linked shelter zones, owned low-pass ambience bus,
night/day NPC activity and animation switching are implemented. Five rainy GPU quality
presets rendered; a zero-exit audio resource leak was caught and fixed with orderly
cell/audio release before bounded exit. Visual review caught shelter rain clipping;
a bounded roof mask was added, with a fresh GPU sweep required. Existing provider,
workflow, material, canonical view, building, city and fighter regressions pass through
tools/test-world.ps1 -SkipGpu. Final metrics/report and checkpoint follow the fresh sweep.

Final acceptance: see WORLD_RESULTS.md for exact counts, performance and limitations.
1,149 counted passing checks/assertions (325 distinct cases/check positions with stress
repeated), zero remaining failures; additional source/import/GPU/audit gates pass.
All five final rainy presets and actual street/worker images inspected. Current ComfyUI
loopback health is unavailable because the backend is stopped; no new inference or model
install was needed. Meshy remains deferred (prior HTTP 401), no Gemini/Higgsfield, no credits.
Next milestone is visual/navigation refinement of this same small block, not a larger city.

Hero checkpoint A: existing three recipes now differ in window proportion, facade rhythm,
roof silhouette and accent palette. Blender generation/export and Godot validation/render
passed for all three. Eight recipe checks and 11 streaming/16 environment/30 gameplay
checks passed. Authored 1024-square periodic normal/roughness fields use a two-meter repeat;
no inferred physical PBR. Composed benches/bollards/cabinets/service crates added; nav grid
excludes expanded collision footprints. Same street view draw calls fell 1086 to 501 by
batching static building parts by material. Visually IMPROVED PROTOTYPE, not hero quality.
Next: navigation route test, uncapped benchmark and day/rain/night lighting review.

Hero checkpoint B (engineering, 2026-09-07): Astra's hero-block visual work is preserved
unchanged; this pass only measured, tested and hardened it. The uncapped benchmark is
finished: vsync and the FPS cap are disabled for the benchmark process only, the camera
and time of day are fixed, and CPU/GPU render-only timings plus median/p95/p99 come from
RenderingServer and Performance monitors. All five presets measured on the real Vulkan
device; see HERO_BLOCK_PERFORMANCE.md for the method, the full table and the limitations.
Astra's draw-call claim is verified against f6b5667 in a temporary worktree: 1105 to 299
draw calls on the same street view while primitives rose 117,528 to 161,448, so no content
was dropped. Two measured fixes: repeated collision-less street props became MultiMesh
instances (490 to 299 draw calls, CPU render -17%, max stress nodes 719 to 283) and the
hero surface maps now import with the mip chain their material filter already requested.
Godot ArgumentList tooling only ran under PowerShell 7, which is not installed here; the
shared helper now works on Windows PowerShell 5.1 too without changing the pwsh path.
Test coverage grew: hero surfaces 4 to 21 tests including rejection cases, hero navigation
43 checks covering prop clearance, lane continuity, stall/oscillation, unreachable targets
and unload/reload of a routing agent, building recipe 8 to 105 checks including batching
determinism across all three archetypes, streaming 11 to 121, ambience 13 to 66 and the
streaming stress 203 to 286 checks per process. Full tools/test-world.ps1 run: 2,206
counted passing checks, zero failures, 100 streaming cycles across five separate processes,
372 audited files. Remaining engineering issue: the navigation mesh stops 4.22 m short of
the designed building entrances. Remaining art work is Astra's; no provider, credit or
model use in this pass.
