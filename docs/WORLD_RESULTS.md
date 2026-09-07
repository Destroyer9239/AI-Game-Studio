# Verified world milestone — 2026-09-07

The block is technically playable. Existing accepted content was preserved. Character
art, city art and synthesized audio remain prototype quality; this is not a finished game.

## Evidence

Final counted regression: **1,149 passing assertions/tests, zero remaining failures**:
23 provider unit tests, 3 image-workflow tests, 5 multiview tests, 5 city contract tests,
8 Blender building/determinism checks, 9 material/lifecycle tests, 9 automation checks,
11 streaming checks, 16 environment/audio checks, 30 gameplay checks, and 206 streaming
stress assertions repeated in five separate processes (1,030 assertions / 100 cycles).
These are 325 distinct cases/check positions with the stress cases repeated, not 1,149
unique test scenarios. Expected negative cases print failures internally and pass when
the rejection is correct. Earlier failed development runs are retained in ignored logs.

Additional acceptance gates, not included in that count: both canonical reference sets,
read-only Blender character source validation (10 categories), Godot import/resource/
original fighter/main runtime checks, five actual Forward+ GPU presets, street/worker
GPU inspection and Git artifact/credential-pattern audit. No live external service test
is inferred from mocks. Local image inference was not repeated; earlier acceptance is
preserved and nine material/lifecycle tests reran.

Evidence directories:
- `generated/reports/world-regression-555ab3ff14454f87a8c7b1b7222d87fe`
- `generated/reports/world-0b437bb5eb6f4686bbe568a28e56ca2c` (final stress/gameplay)
- `generated/reports/world-1e6c0355c4da4b6db46642d4060b1e42` (final rainy GPU sweep)
- `generated/reports/20260907-090300-841-a7af8a` (fighter/main regression)

## Streaming and gameplay

One serialized background request precedes main-thread cell instantiation. Queued stale
loads cancel, active stale loads drain/discard; shutdown drains the active request.
The prior headless RID error was associated with competing resource loads/creation.
Its exact internal engine cause is unproven; repeated stress now passes. A later GPU
shutdown resource leak was fixed by stopping/releasing streamed audio and waiting before
exit. Navigation assertions wait for physics-server synchronization.

Final stress: 20 cycles/process, five processes, max 719 nodes, three cells/zero pending/
zero failures at completion. Each run performs 63 loads, 60 unloads and 20 discarded
obsolete loads. It tests weak-reference destruction, entity/terminal persistence, current
weather on reload, objective persistence, navigation count, duplicate prevention, disk
restore, full scene release and shutdown with an active request.

Player movement/collision/camera, E-ray terminal interaction, event-driven objective,
versioned save/restore and worker navigation work together. Robot health/position/goal
and terminal activation survive streamed unload/reload. Weather determines shelter
behavior, time determines day patrol/night rest. Idle/Walk playback advances. Door,
switch, pickup, health, perception and vehicle interfaces are intentionally small hooks;
only terminal/worker are placed in the playable block.

## Visual and performance result

Inspected all eight worker references, the Godot robot preview, animated worker in the
street, first-person terminal, street framing and all five rainy preset images. Geometry,
orientation and authored signage are intact. Shelter rain now uses a bounded roof mask.
The block is coherent but sparse: facade repetition, simple road material, dark shelter
undersides and basic robot animation remain visible prototype limitations. No polished
humanoid, professional audio mix or general building rain collision is claimed.

At 1280 x 800 on RTX 5070 Ti, the bounded first-person rainy view measured:

| Preset | Mean ms | p95 ms | Reported video memory MiB |
|---|---:|---:|---:|
| LOW | 6.945 | 8.104 | 254.0 |
| MEDIUM | 6.944 | 7.959 | 279.6 |
| HIGH | 6.945 | 8.287 | 375.7 |
| ULTRA | 6.945 | 8.437 | 441.5 |
| CINEMATIC | 6.944 | 8.362 | 526.8 |

Each capture has 577 measured frames after warmup, 284 reported draw calls, three cells,
one NPC and 24 lights. Reported primitives: 29,948 LOW/MEDIUM and 73,148 HIGH+ including
render effects. Six shared procedural city materials excludes imported building materials.
Frame intervals are CPU observed and refresh-limited near 144 FPS, not isolated GPU time
or an uncapped performance limit. This view is not a full-city or lower-end-PC benchmark.

## Scope and providers

Original fighter main scene and accepted assets remain. Three building archetypes compose
four buildings. Other archetypes/district parameters are templates/contracts, not proven
district production. Arbitrary 2D worlds, HLOD, byte-based admission, general occlusion,
streamed navigation transfers and offscreen NPC simulation remain future work.

Central time/sky/weather/fog/lighting/wetness connects to layered ambience and worker AI.
Procedural/physical/custom/panorama sky hooks preserve SDR versus declared HDR distinction.
Audio has base/district/weather/interior layers, positional machinery, seeded one-shots,
world events and unload-aware shelter filtering. Sounds are original synthesized fixtures.

ComfyUI/SDXL/Real-ESRGAN remain installed. Current loopback health reports UNAVAILABLE
because the managed backend is stopped; prior CUDA/inference acceptance remains recorded.
Meshy: previous environment-key detection and HTTP 401 are deferred. Gemini and Higgsfield
NOT CONNECTED. External credits spent: NO. New models/downloads/installations: NONE.

## Next milestone and handoff

Recommended next action: review/play this exact block, then improve one street's art and
navigation obstacle coverage before increasing world size.

Engineering/debugging candidates: save schema migrations, finer instantiation budgets,
2D streaming/byte admission, adversarial persistence tests, tighter navigation around props,
NPC perception implementation and refactoring compact GDScript into reviewed components.
No other agent or Claude was invoked.

Keep for Astra visual/architecture work: facade/material variation, street composition,
lighting and rain review, character animation/LOD visual review, Blender kits, canonical
multiview judgment and optional local ComfyUI texture work. Robot art polish is deferred
as requested. Do not add cloud providers or scale the city as a substitute for this review.
