# Blender → Godot pipeline test

Verified on 2026-09-05 with Blender 5.0.1 and Godot 4.7.2.stable.official.ed1daf0bf on Windows.

This records the original proof. The pipeline is now committed as `531e5fa`.
For the current master command and report locations, read `AUTOMATED_WORKFLOW.md`.
Godot command examples below use the current preferred executable path.

## Result

| Stage | Result | Evidence |
| --- | --- | --- |
| Blender background automation | PASS | Process exited 0; editable `.blend` saved (111,312 bytes). |
| GLB export | PASS | Process exited 0; `.glb` saved (156,500 bytes), then imported by Godot. |
| Godot import | PASS | Headless editor import completed; final import log has no errors. |
| Godot scene validation | PASS | 22 visible mesh components; named parts, emissive materials, collision, active camera, main scene, rotation, pause and reset verified. |
| Main scene runtime | PASS | Headless startup ran 120 frames at a fixed 60 FPS with no logged errors. |
| Rendered preview | PASS | Real OpenGL Compatibility rendering on NVIDIA GeForce RTX 5070 Ti; PNG captured and visually inspected. |

AGENTS.md and all existing project directories/files were inspected before edits. The initial project contained README.md, AGENTS.md and an empty Godot configuration, with no existing scenes, scripts or assets. The clean initial commit `da77b3c` was checkpointed with Git tag `pipeline-test-before` before changes. The working proof was subsequently committed as `531e5fa`.

## Generated content

The original **Kestrel / 01** is a small faceted sci-fi fighter built entirely from procedural meshes: tapered central fuselage and nose, framed teal cockpit, swept left/right wings, amber identification markings, paired dorsal fins, twin rear engine housings/intakes/nozzles and cyan emissive engine cores. No reference geometry or external assets were used.

The Blender source has 22 visible mesh objects and one simplified collision-only fuselage mesh. Named metallic PBR materials are embedded in the GLB. Blender +Y points forward and +Z points up; glTF export maps these to Godot -Z forward and +Y up. Units are meters. Geometry is about 8.3 m wide and 6.6 m long.

The test scene instances the GLB directly. It contains a camera, WorldEnvironment with a dark background and sky reflections, directional key/rim lights, a warm fill light, two reference rings and deterministic star markers. The model turns at 12 degrees/second. **Space** pauses/resumes, **R** resets and resumes, and **Escape** exits.

## Files

- `blender/scripts/generate_test_fighter.py` — repeatable Blender generator, with paths resolved from the script location.
- `blender/projects/test_fighter.blend` — editable generated source.
- `game/assets/models/test_fighter.glb` — runtime model with embedded materials.
- `game/assets/models/test_fighter.glb.import` — Godot import settings, including collision name suffix handling.
- `game/scenes/test_fighter_scene.tscn` — main presentation scene.
- `game/scripts/test_fighter_demo.gd` — turntable, controls, depth markers and optional preview capture.
- `game/scripts/validate_pipeline.gd` — executable scene assertions, returning nonzero on failure.
- `game/scripts/*.gd.uid` — Godot script identity sidecars.
- `game/project.godot` — main scene, 1280 × 800 viewport, Compatibility rendering and 4× MSAA.
- `tools/validate_pipeline.ps1` — repeatable import, scene and runtime validation; optional rendered capture. Checks process exit codes and error text because Godot can exit 0 after a script parse error.
- `.gitignore` — excludes Godot caches, Blender backups and local validation output.
- `generated/pipeline-test/` — local logs and `fighter-preview.png` (ignored by Git).

## Commands used

Run from `C:\Users\ronan\AI-Game-Studio` in PowerShell. Although the short commands were expected to be available, this terminal's PATH did not resolve `blender` or `godot`. The installed executables below were located and their versions verified; no software installation was needed.

```powershell
git tag pipeline-test-before da77b3c

& 'C:\Program Files\Blender Foundation\Blender 5.0\blender.exe' --background --factory-startup --python-exit-code 1 --python blender/scripts/generate_test_fighter.py

pwsh -NoProfile -File tools/validate_pipeline.ps1 -Capture
```

The initial Blender execution redirected console output to `generated/pipeline-test/blender.log`. The validator uses the executable on PATH if available, otherwise the preferred C:\Tools\Godot path below. Override it with `-GodotPath` on another machine. Omit `-Capture` for entirely headless validation.

The validator runs these Godot operations, adding an absolute `--log-file` path before the arguments:

```powershell
$godotExe = 'C:\Tools\Godot\godot.exe'
& $godotExe --headless --path game --editor --import
& $godotExe --headless --path game --script res://scripts/validate_pipeline.gd
& $godotExe --headless --path game --quit-after 120 --fixed-fps 60
& $godotExe --path game --fixed-fps 60 --quit-after 300 -- --capture=C:\Users\ronan\AI-Game-Studio\generated\pipeline-test\fighter-preview.png
```

To launch the finished interactive test from any directory:

```powershell
& 'C:\Tools\Godot\godot.exe' --path 'C:\Users\ronan\AI-Game-Studio\game'
```

## Diagnostics and limitations

- Initial Godot attempts encountered sandbox restrictions on user settings/editor cache and Windows certificate access. Validation was rerun with approved normal process access; final logs contain no such errors.
- The first script used an incorrect reflection enum. It was corrected to the installed engine's `Environment.REFLECTION_SOURCE_SKY`; subsequent import and runtime checks pass.
- The initial capture command placed `--log-file` after the user-argument separator. Capture succeeded but the validation wrapper could not find its log. The argument ordering was fixed and the complete validation rerun passed.
- Blender reported a `Material.use_nodes` deprecation warning for Blender 6.0. Generation and export succeed on the requested Blender 5.0.1. A future Blender major-version migration may require updating material setup.
- This is an interactive asset inspection test, without flight, combat, audio, saving or other game systems.
- Materials use solid PBR values, so texture UVs are unnecessary. Compatibility rendering shows bright emissive cores without bloom. The simplified fuselage collider proves collision import; it does not precisely cover the wings or engines and is not intended for dynamic flight physics.
- Headless validation proves resource loading and behavior, while the separate GPU capture verifies appearance. This is a local smoke test, not a performance benchmark or cross-platform export test.

Final verification includes `git diff --check` and `git status --short --untracked-files=all`.
