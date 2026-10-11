# AI Game Studio

Agent-driven 3D game development workspace.

**Active game: [Signal Lost](games/signal-lost/design/BRIEF.md)**, a third-person
space game in UE 5.7.1. Open `Open-Signal-Lost.cmd`. See [studio games](games/README.md)
and [Claude's first task](games/signal-lost/design/CLAUDE_TASK_01.md).
Project foundation is separate from flight gameplay, which is the next milestone.
Shared Unreal commands select it with `-Game signal-lost`.

**Preserved Unreal reference:** Open `Open-Cinder-Unreal.cmd` for the
new editor project, or `Play-Cinder-Unreal.cmd` for the packaged migration fixture.
Read [Unreal setup and migration](docs/UNREAL_PIPELINE.md) for commands,
verified capabilities, asset decisions and remaining toolchain work. The Godot
release below is preserved as a working reference, not silently replaced or deleted.

Current playable release: **Cinder / Last Light**, a short first-person repair
mission across the existing two-block district. Open `Play-Last-Light.cmd` to play.
The mission has a start/settings menu, three objectives, checkpoint saving and an
ending. It supports 4K output; this remains an improved prototype, not AAA-quality
art or a full campaign. See [current acceptance](docs/LAST_LIGHT_RESULTS.md).

Agent entry point: `tools/last-light.ps1 validate`, `launch`, or
`benchmark -Quality 2 -FourK`. The original fighter scene and regressions remain.

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
No new software is required for the current pipeline. ComfyUI, SDXL and Real-ESRGAN
are already installed locally; their lifecycle and inference acceptance are recorded
in the project documentation. Last Light additionally uses six verified CC0 Poly
Haven texture maps; gameplay has no network dependency.

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
