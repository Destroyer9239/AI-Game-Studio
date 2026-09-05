# AI GAME STUDIO

You are the primary development agent for this 3D game project.

## Core Tools

Godot:
godot

Blender:
blender

Git:
git

Resolve tools through `tools/studio-common.ps1`: prefer `godot` on PATH, then
`C:\Tools\Godot\godot.exe`. Never use a Godot executable from Downloads.
Prefer `blender` on PATH, then `C:\Program Files\Blender Foundation\Blender 5.0\blender.exe`.
Run PowerShell entry points with `pwsh -NoProfile -File`; no package installation is required.

## Project Structure

/game
The actual Godot game.

/blender
Blender projects and Python generation scripts.

/generated
Generated models, textures, and concept art.

/tools
Automation and validation scripts.

/docs
Game design and technical documentation.

## Development Rules

1. Use Godot for the playable game.
2. Use Blender for 3D asset creation.
3. Blender may be automated using Python scripts.
4. Prefer GLB/GLTF for moving Blender assets into Godot.
5. Put reusable Blender automation in /blender/scripts.
6. Put Godot gameplay scripts in /game/scripts.
7. Put Godot scenes in /game/scenes.
8. Put imported game models in /game/assets/models.
9. Test changes whenever practical.
10. Fix errors rather than ignoring them.
11. Keep files organized.
12. Do not delete working systems unnecessarily.
13. Use Git checkpoints before major changes.

## Autonomous Execution Contract

- Astra/Codex agents are expected to perform authorized work, not hand terminal commands back to the user.
- Read this file, inspect the relevant project files and Git status, and preserve working systems before changing them.
- Actually run Blender generators, export their GLBs, run Godot import/validation and inspect a rendered preview. Writing code alone is not completion.
- Diagnose command failures, fix the cause and rerun affected checks. Read logs as well as exit codes: Godot can return zero after a parse error.
- Use Blender background mode with `--factory-startup --python-exit-code 1` to avoid user startup/add-on interference. Keep reusable automation in `blender/scripts/`.
- Before major changes, create a Git checkpoint for relevant existing work. Do not commit unrelated user changes or credentials. Keep changes reviewable; never reset/clean working files just to obtain a clean tree.
- Do not kill unrelated Blender/Godot sessions, remove working systems, overwrite hand-authored scenes, install large dependencies, or change system settings without task authorization.
- Create original assets from the gameplay brief. Do not copy copyrighted franchise geometry, logos or recognizable designs.
- Optimize for real-time use: set triangle/material/texture budgets, apply sensible scales, use compact collision shapes, reuse materials, and add LODs when the expected screen size calls for them.
- Main scene changes must serve the requested gameplay task. Asset automation generates reusable wrappers; it preserves the existing main scene.
- Ask the user for genuinely missing decisions or required human actions. Routine implementation choices and reversible fixes belong to the agent.

## Standard Commands for Agents

Call `tools/pipeline.ps1` with one operation:

- `validate`: headless import, resource loading, regression and main runtime checks.
- `launch`: import and launch the game; `-Frames 120` gives a bounded launch smoke test.
- `scaffold -Asset asset_id`: create a draft design specification, manifest and generator without overwriting files.
- `generate -Asset asset_id`: execute its procedural Blender script and save the editable source.
- `export -Asset asset_id`: export its saved Blender source with UV checks/preparation selected by the manifest.
- `integrate -Asset asset_id`: create the asset wrapper, import and validate it.
- `test-asset -Asset asset_id`: import and enforce that asset's geometry/material/collision requirements.
- `preview -Asset asset_id`: validate and capture an actual Godot GPU render.
- `test-pipeline -Asset asset_id`: run generation through rendered preview in one command.
- `doctor`: refresh the read-only local hardware/software inventory.

Example: `pwsh -NoProfile -File tools/pipeline.ps1 test-pipeline -Asset test_fighter`.
The agent runs these commands. Read `generated/reports/<run>/report.json` and logs;
inspect `generated/previews/<asset>.png`. Never report image inference as tested when only a dry-run ran.

## 3D Asset Pipeline

When a new 3D asset is required:

1. Determine its gameplay requirements.
2. Create or update a Blender Python generation script.
3. Run Blender from the command line when appropriate.
4. Generate the model.
5. Create appropriate materials.
6. UV unwrap when textures require it.
7. Create reasonable collision geometry.
8. Export as GLB.
9. Place the runtime asset in /game/assets/models.
10. Integrate it into the correct Godot scene.
11. Test the asset inside Godot.

Asset records live in `tools/assets/<id>.json`; design specs in `docs/assets/<id>.md`.
Start from the templates in `tools/templates/` and `blender/scripts/templates/`.
Draft templates deliberately refuse generation until the agent implements the design and marks the manifest ready.
Record dimensions, pivot/orientation, required components, materials, UV mode and runtime budgets.
Use Blender +Y forward/+Z up and meters, which export to Godot -Z forward/+Y up.
Use `-colonly` or `-convcolonly` import geometry where appropriate. Imported static collision is not a substitute for designing a moving gameplay body's physics/collision hierarchy.
Put hand-authored gameplay in a parent of generated `game/scenes/assets/<id>.tscn` wrappers.

## Images and Texture Preparation

- Read `docs/LOCAL_IMAGE_GENERATION.md` before choosing or installing a local image backend.
- No local diffusion backend/model is installed by this setup. ComfyUI Portable + SDXL is the proposed next installation, subject to approval for its large downloads.
- Prepared requests/workflows live in `tools/imagegen/`; the standard-library adapter defaults to dry-run and only talks to loopback when explicitly executed.
- Retain prompts, seeds, model source/license, workflow versions and output hashes. Review generated concepts before interpreting them as 3D geometry.
- Curate concept art in `generated/concept-art/`, source maps in `generated/textures/`, and runtime textures in `game/assets/textures/<id>/`.
- Verify actual seamlessness, alpha edges and material-map behavior. Text-to-image output is not automatically a seamless texture or calibrated roughness/metallic/normal map.

## Goal

Build complete playable systems rather than disconnected demonstrations.

When implementing a feature, consider:

- gameplay
- visuals
- UI
- sound hooks
- performance
- AI behavior
- physics
- collisions
- saving/loading when relevant
- debugging
