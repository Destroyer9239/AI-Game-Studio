# Playable Cinder Exchange

Launch: `pwsh -NoProfile -File tools/pipeline.ps1 world-launch`.
The original fighter remains the project main scene; this command opens the block explicitly.

WASD moves, mouse click captures the pointer, mouse looks, Space jumps, E interacts.
Esc releases the pointer. R toggles rain, T day/night, F5 saves, F9 loads, 1–5 changes
quality. `game/world/controls.json` provides InputMap defaults; existing configured
InputMap actions are preserved. Rebinding UI and controller support are future work.

Walk to the illuminated service terminal, look at it and press E. Its event completes
the service-link objective and triggers ambience. Save, leave the central cell's
streaming range, return: terminal activation, robot health/location/goal and objective
state persist. The regression performs this flow automatically, including disk restore.

`studio_interactable.gd` provides terminal/switch/door/pickup hooks, stable ID, snapshot
and damage. The door fixture toggles visibility/collision; it is not a polished animated
door. Terminal uses this base. `studio_objective.gd` handles activation, matching events,
progress, completion and failure. `studio_events.gd` broadcasts gameplay/world/weather
and objective events with bounded history. Vehicles reserve enter/active-ID hooks only.

The worker follows navigation, patrols by day, rests at night and seeks shelter in rain.
It switches Walk/Idle clips. Perception is a signal extension point, not a complete
sensory AI. Unload owns the worker, collision, navigation and local audio; no detached
NPC reference is retained. Current simulation pauses unloaded NPCs rather than advancing
a global schedule. Skinned technical robot validation is documented in characters/.

Versioned saves are written under Godot user:// through a temporary file then rename.
Player transform, cells/entities, objective, environment and quality are saved. Invalid
shapes/types/weather and nonfinite positions are rejected before changing the world.
This is a bounded single-player schema, not arbitrary future game migration support.

Commands agents should execute:
- `pwsh -NoProfile -File tools/pipeline.ps1 world-test`
- `pwsh -NoProfile -File tools/pipeline.ps1 world-stress`
- `pwsh -NoProfile -File tools/pipeline.ps1 world-benchmark`
- `pwsh -NoProfile -File tools/test-world.ps1` (full existing-asset regression + GPU)

`world.ps1 stress -Runs 5` runs five separate 20-cycle processes. `benchmark -Weather rain`
saves one PNG and metrics JSON per preset. Logs are checked for errors, including zero-exit
Godot failures. `test-world.ps1 -SkipGpu` is appropriate when the same final GPU sweep was
just run separately. This suite never submits a provider job or regenerates accepted
fighter/building sources. The building determinism test uses an isolated unit asset ID.
