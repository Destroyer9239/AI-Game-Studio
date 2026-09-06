# AI Game Studio

Agent-driven 3D game development workspace.

The Blender → GLB → Godot pipeline is automated and verified. Ask the agent to
create an original asset, validate the project, render a preview or launch the
game; the agent runs the tools for you.

Main automation entry: `tools/pipeline.ps1` (PowerShell 7).

- `validate` — import and check the project.
- `launch` — start the game.
- `test-pipeline -Asset test_fighter` — regenerate, export, integrate, test and render.
- `scaffold -Asset asset_id` — prepare the next asset's spec, manifest and generator.

See [Automated workflow](docs/AUTOMATED_WORKFLOW.md),
[multiple asset providers](docs/ASSET_PROVIDERS.md),
[local image-generation proposal](docs/LOCAL_IMAGE_GENERATION.md), and
[original pipeline test](docs/PIPELINE_TEST.md).

Godot resolution prefers `godot` on PATH, then `C:\Tools\Godot\godot.exe`.
No new software is required for the current 3D pipeline. Local AI image generation
is prepared but awaits the proposed ComfyUI/model installation.

The provider layer supports offline generation plans, one-use paid approvals,
Meshy REST and Higgsfield official CLI adapters, and local ComfyUI jobs.
Use `asset-plan -RequestFile <json> -Quality hero` to inspect a route.
`asset-create` runs local routes; paid routes remain plans until explicitly approved.
The no-credit acceptance entry point is `tools/test-providers.ps1`.

Main tools:

- Codex
- Godot
- Blender
- Git

Game project:
game/

Blender automation:
blender/scripts/

Generated assets:
generated/
