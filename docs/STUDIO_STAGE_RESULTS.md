# Local environment stage acceptance — 2026-09-06

Continued from `114ec58` (which preserved the interrupted ComfyUI work), keeping
the tested `f0f86af` provider architecture and original fighter intact.

| System | Result |
| --- | --- |
| ComfyUI managed start/reuse/stop/restart and interrupted-PID recovery | PASS |
| CUDA and real RTX 5070 Ti image inference | PASS |
| SDXL source → tiled Real-ESRGAN 4096² | PASS |
| Selective material maps, periodic edges, hashes and visual review | PASS |
| Blender editable source, packed textures and GLB export | PASS |
| Godot import/resources/material/collision/scene and original fighter | PASS |
| Forward+ GPU lab, sky contracts and five quality presets | PASS |
| Paid-provider protection and rejected-reference guard | PASS |
| Obvious credential/model-artifact audit | PASS |

Executed full `pwsh -NoProfile -File tools/test-studio.ps1`, then reran affected
checks after final fixes. **44 automated checks passed**: 23 provider/protocol tests,
3 image-workflow tests, 9 PowerShell safety/scaffold checks and 9 material/lifecycle
regressions. **9 live local backend checks passed**, plus **5 GPU quality presets**.
No unresolved failures. Expected negative tests deliberately log rejected requests;
they are not actual service failures. Mock provider tests do not establish live
Meshy/Higgsfield generation success. Actual local inference is separate evidence.

The small environment has 108 render triangles, three materials, compact static
floor/wall collisions and embedded 4096 basecolor/normal/metallic-roughness textures.
Its GLB is about 20.3 MB. Runtime height/displacement is omitted; optional source
height can be regenerated with `material_factory.py --height`. Full source and
runtime assets are curated; raw image jobs, models, runtime and reports are ignored.

The final HIGH sample (1280 × 800, 100 instanced props) measured about **1.04 ms mean /
2.39 ms p95 CPU-observed frame intervals**, 65 draw calls and 1.23 GB reported video
memory. This tiny lab is not a city-performance claim or isolated GPU timing. See
`generated/manifests/environment_probe.json` for all preset samples and limitations.
The final GPU render and repeated material grid were visually inspected. Concrete
panel repetition and baked-in color joints remain visible; microrelief is authored,
not recovered from that color image. A local SDXL concept is also displayed in Godot.

Environment/road/detail/quality/character templates and material categories are ready
for agents to extend. Streaming, city composition, full character integration and
production navigation remain architecture only. No full city/game was built.

Four independently prompted spacecraft reference images were generated but rejected
for reconstruction: wrong/inconsistent views, unrelated silhouettes and pseudo-markings.
Their offline Meshy plan is explicitly rejected and cannot execute. A controlled
Blender blockout is the next reliable reference step. No external credits were spent.
Meshy key presence was detected at user scope; read-only authentication returned 401.
Higgsfield remains optional. No Gemini adapter or new large model was added.

Portable runtime plus installed models/outputs occupies about 11.57 GB, with the
2.15 GB download archive retained separately. C: had about 2.00 TB free at final
inspection. No further installation is necessary. ComfyUI was cooperatively stopped
after testing to release GPU memory; provider auto-start is verified.

## Reproduce or inspect

From the project root, the agent can invoke:

```powershell
pwsh -NoProfile -File tools/test-studio.ps1
pwsh -NoProfile -File tools/pipeline.ps1 environment-launch
```

The first runs real local inference and complete validation. The second opens the
interactive lab. Raw evidence is under `generated/reports`; durable provenance is
under `generated/manifests`. See LOCAL_IMAGE_GENERATION.md, MATERIAL_FACTORY.md,
RENDERING_AND_SKIES.md and ENVIRONMENT_ARCHITECTURE.md for operating details.

Next milestone: one original modular street corner with a shared facade kit, one
intersection, two loadable chunks and validated pedestrian navigation. Establish
playable performance budgets there before expanding to a district.
