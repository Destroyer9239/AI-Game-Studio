# Copy this task into Claude Code at the repository root

Work on Signal Lost milestone 1 only. I authorize Claude to edit this project; this
supersedes historical instructions prohibiting Claude. Do not launch other agents.

Read games/signal-lost/design/BRIEF.md, games/README.md and
games/signal-lost/reports/SETUP.md. Inspect Git status and relevant shared Unreal tools.
Project: games/signal-lost/unreal/SignalLost.uproject, Unreal 5.7.1.
Preserve game/ and unreal/Cinder. Avoid a whole-repository audit or unrelated refactors.

Implement an original third-person flight prototype: spacecraft pawn, chase camera,
acceleration/deceleration, pitch/yaw/roll, mild inertia, collision with course obstacles,
reset and a readable speed display. Document units and controls. Reuse the existing
/Game/SignalLost/Generated/Meshes/SM_test_fighter as a temporary visual only. Verify
its facing and scale; use a suitable moving collision root, not the static import
fixture's collision as an assumed complete vehicle physics implementation.

Author runtime logic in C++/Blueprint, never editor Python. Put authored levels/assets
under /Game/SignalLost/Authored and C++ under this project's Source if needed.
Create a compact space course with scale references and readable lighting. Add a
repeatable setup script for generated course content where practical. Keep the shared
L_Pipeline fixture and its acceptance tests intact. Set the new flight map as this
game's default and cook it alongside the fixture. Update smoke testing to exercise
the flight map separately; do not mislabel first-person tests as flight tests.

Actually compile, run and test. Check spawn/possession, acceleration/braking, turning,
collision, reset, HUD, frame-rate-independent movement and packaged startup. Capture
and inspect a gameplay render. Run relevant shared regression checks. Do not claim
unperformed manual tests or measured 4K performance from a screenshot.

Shared foundation command: pwsh -NoProfile -File tools/unreal.ps1 accept -Game signal-lost
If pwsh is not on PATH, dot-source tools/studio-common.ps1 and use Get-StudioShell.
Close only your own editor processes before packaging; do not kill user sessions.

No combat, multiplayer, planetary generation, new purchases, external generation
credits, new dependencies or large downloads. Keep this task bounded to flight.
Do not launch a second assistant. Do not overwrite user edits or binary assets.
Check Git LFS storage before uploading authored binaries. Prefer reproducible source
for generated assets; never ignore the only copy of authored gameplay.

Finish with tested results, remaining bugs, changed files, controls, launch steps
and a local Git checkpoint of task-owned files. Do not push new LFS payloads without
checking capacity/authorization. Stop and let the user playtest. The user will bring
your report back to Codex for independent review and refinement.
