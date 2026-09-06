# Autonomous asset development

The original commands below remain supported. For provider selection, quality tiers,
paid request plans, external cleanup, image jobs and multi-view preparation, see
[ASSET_PROVIDERS.md](ASSET_PROVIDERS.md). Run `tools/test-providers.ps1` for the combined
no-credit acceptance suite, including the original fighter regression.

The agent runs the tools directly. The user can request an original asset in ordinary language; no manual terminal work is needed for normal generation, import, validation or launch. The scripts execute the repeatable stages; the agent still authors the design and procedural generator and reviews the result.

## Entry point

`tools/pipeline.ps1` runs under PowerShell 7. All paths resolve from the repository, so the agent can call it by absolute path from any working directory. No new Python packages, applications or system PATH changes are required.

Tool resolution: explicit `-GodotPath`/`-BlenderPath` override, then the corresponding command on PATH, then `C:\Tools\Godot\godot.exe` or `C:\Program Files\Blender Foundation\Blender 5.0\blender.exe`. The preferred Godot path was verified as version 4.7.2. Neither short command was available in the inspected agent terminal, so the tested runs used these fallbacks.

| Operation | Agent command suffix | Effect |
| --- | --- | --- |
| Validate project | `validate` | Import, load all scripts/scenes/resources, run fighter regression and main scene for 120 frames. |
| Validate and render | `validate -Capture` | Also validate the selected asset and capture its preview. |
| Launch | `launch` | Import and launch the actual main scene, returning its process ID. |
| Bounded launch | `launch -Frames 120` | Launch the real renderer and close automatically after 120 frames. |
| New asset scaffold | `scaffold -Asset heavy_interceptor` | Create draft spec, manifest and generator. Refuse existing files. |
| Blender generation | `generate -Asset test_fighter` | Execute generator headlessly, save editable `.blend`. |
| Export | `export -Asset test_fighter` | Open saved source with factory settings, check materials/UVs, export GLB. |
| Import | `import` | Headless Godot editor import. |
| Integration | `integrate -Asset test_fighter` | Create reusable model scene, import, check asset requirements. |
| Asset validation | `test-asset -Asset test_fighter` | Import and enforce the manifest's geometry/material/collision requirements. |
| Render preview | `preview -Asset test_fighter` | Import/test, automatically frame the asset, capture actual GPU output. |
| Full pipeline | `test-pipeline -Asset test_fighter` | Generate → export → integrate → validate → asset test → rendered preview. |
| Inventory | `doctor` | Read hardware/software/model-cache information; do not install or start services. |

Every suffix is passed to `pwsh -NoProfile -File tools/pipeline.ps1`. These examples document the agent API; the agent should execute them rather than asking the user to do so.

`tools/validate_pipeline.ps1` remains a compatible wrapper for the original validation command and accepts `-Capture` and `-GodotPath`.

## Request to finished asset

1. Inspect AGENTS.md, the relevant working systems, and Git status; checkpoint relevant current work before major edits.
2. Scaffold an asset ID. Complete `docs/assets/<id>.md` with original silhouette, gameplay role, dimensions, pivot, names, surface treatment and collision requirements.
3. Implement `blender/scripts/generate_<id>.py`. Templates deliberately raise `NotImplementedError` until authored; a prompt alone is not treated as generated geometry.
4. Set `tools/assets/<id>.json` to `ready` once the generator is implemented. Record budgets, required nodes and emissive nodes. Use fixed seeds when procedural randomness is involved.
5. Run `test-pipeline -Asset <id>`. It saves `blender/projects/<id>.blend`, exports `game/assets/models/<id>.glb`, and creates `game/scenes/assets/<id>.tscn`.
6. Inspect the image in `generated/previews/<id>.png` and all stage results. Fix material, geometry, collision or framing problems and rerun affected stages.
7. Integrate the wrapper into the task's intended gameplay parent if the user requested playable behavior. Do not silently replace the main scene as part of generic asset authoring.
8. Record results and checkpoint the finished work. Do not report the asset complete while errors or unmet brief requirements remain.

## Manifest and export contract

The manifest's schema version is 1. IDs contain lowercase letters/digits/underscores. Generator, source, model, spec and wrapper paths follow the asset ID; path traversal and reparse-point traversal are rejected. Manifests are trusted project configuration, not arbitrary downloaded executable instructions.

Generators run with `--background --factory-startup --python-exit-code 1 --python <script> -- --blend-only`. They must save their source and print `PIPELINE_BLENDER_PASS`. The original fighter generator still exports a GLB when invoked directly without `--blend-only`.

The exporter runs in a separate Blender process with factory startup settings. `uv_mode` supports:

- `none`: solid PBR assets, no texture UV requirement.
- `required`: reject missing authored UV layers.
- `smart`: prepare missing UV layers using Blender smart projection and save them back into the editable source. Existing layers are preserved. Inspect seams/distortion; this is preparation, not automatic texture-quality approval.

Godot validates nonempty geometry, triangle/material budgets, required named nodes, emissive material preservation, UV presence when required, and enabled collision resources. Collision mesh suffixes are interpreted by the importer. A static imported collider is appropriate for inspection/static props; moving ships require a designed CharacterBody3D/RigidBody3D setup in the gameplay parent.

Generated wrappers carry a marker and can be regenerated. Hand-authored wrappers are preserved with a clear error. The original fighter main scene stays intact. Geometry checks do not replace visual review, physics tuning, detailed UV inspection, LOD review or gameplay-specific tests.

## Reports and failure behavior

Each invocation writes `generated/reports/<timestamp-id>/report.json`, including status, arguments, resolved executables, durations, exit codes and per-process logs. Failures return exit code 1. Logs are scanned for script/import errors even when Godot returns zero. Expected completion markers prevent stale files from masquerading as a successful preview.

Child processes have timeouts. On timeout only the process tree started by that invocation is stopped. Generation/export may replace that asset's source/output, so keep checkpoints. The tools do not delete project files, reset Git, close unrelated sessions or install dependencies. Concurrent pipeline runs against the same Godot import cache or asset are not supported; run them sequentially.

Reports/previews/raw image jobs and Godot caches are ignored by Git. Editable source, GLBs, import settings, script UID files, specs, manifests and selected art belong in version control. Do not add multi-gigabyte AI checkpoints to the game repository.

## Verified setup

- Working original pipeline committed first as `531e5fa` (`Prove procedural Blender to Godot fighter pipeline`).
- Full new pipeline passed on 2026-09-05. Fighter: 22 meshes, 3,520 triangles, 6 materials, 156,500-byte GLB, imported collision and two emissive engines.
- GPU preview captured and inspected; bounded game launch passed.
- Hardware inventory ran successfully through `doctor`.
- `tools/test-automation.ps1` passed 9 checks covering path/ID rejection, missing executables, zero-exit error logs, nonzero exits, missing success markers, scaffold creation, overwrite refusal and draft rejection.
- `tools/imagegen/test_workflow.py` passed offline tests for parameter types/links and malformed/unsupported requests. The image adapter's dry-run produced a saved request/workflow/result bundle. Live image inference is pending installation, not claimed as tested.
- An initial exporter run timed out while using the user's startup configuration. Factory startup isolated the process and the next complete run passed. Existing Blender sessions were preserved.

Read `LOCAL_IMAGE_GENERATION.md` for the measured machine inventory and proposed image backend installation. Read `PIPELINE_TEST.md` for the original proof scene.
