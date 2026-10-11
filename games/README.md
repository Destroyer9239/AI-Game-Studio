# Studio games

Each new game lives in games/<id> with game.json, unreal/, design/, assets/ and reports/.
Shared automation stays in tools/. Source asset tools remain in blender/. Outputs
go to generated/unreal/<id>; generated data and template packs are rebuildable.

Active game: [Signal Lost](signal-lost/design/BRIEF.md), UE 5.7.1.
Existing unreal/Cinder and game/ are preserved reference projects, not relocated.

From the repository root: pwsh -NoProfile -File tools/unreal.ps1 accept -Game signal-lost.
Supported actions: setup, export, build, validate, test, preview, launch, play,
package, smoke, accept, doctor. Omitting -Game preserves Cinder behavior.
The current acceptance tests check the shared import/first-person foundation;
flight acceptance is a separate upcoming milestone. Build never edits Authored.
Do not run two agents/editors against one project concurrently.
