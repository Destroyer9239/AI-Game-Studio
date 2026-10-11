# Signal Lost setup - 2026-10-10

Dedicated UE 5.7.1 project created from the tested Cinder configuration, with a new
project identifier, separate /Game/SignalLost content namespace and isolated exports,
import manifest, preview and package output. Existing projects were not moved.
New games now have a shared games/ home and a game.json descriptor.

Entry: Open-Signal-Lost.cmd. Agent command from repository root:
`pwsh -NoProfile -File tools/unreal.ps1 accept -Game signal-lost`.
This runs Blender export, Unreal build/validation, PIE, 4K preview, package and
packaged startup. These tests exercise a temporary first-person import fixture,
not spacecraft controls. Fixture buildings are not planned space-game content.

Next: user copies design/CLAUDE_TASK_01.md to Claude Code in this repository.
Claude implements only the first flight milestone. User then playtests, returns its
report and leaves the changes here for Codex review. No simultaneous agent edits.
No new dependencies, downloads, paid generation, or Claude sessions were invoked
for this setup. Existing local Epic template resources and original Blender assets
were reused. A 4K preview establishes output size, not 4K/60 performance or AAA art.

Authored Unreal assets belong under Content/SignalLost/Authored. Source generators
must remain versioned. Generated content is ignored and rebuilt; authored content
and its external actor packages must not be ignored. Check LFS capacity before
pushing new authored binaries.

## Executed acceptance

- Blender exported all four original static fixtures without modifying source blends.
- Signal Lost build/import: PASS, 91 checks (fresh materials/map).
- Signal Lost first-person PIE foundation: PASS, 72 checks.
- GPU preview: PASS, 69 checks; actual 3840x2160 PNG viewed and inspected.
- Windows Development package: PASS, exit 0; cook reported 0 errors, 0 warnings.
- Packaged SignalLost.exe startup: PASS, loaded Signal Lost's own generated map,
  clean exit with configured eight-second engine runtime limit.
- Original Cinder validate without -Game: PASS; shared defaults remain functional.
- Unknown game identifier: correctly rejected, not silently routed to Cinder.
- No remaining failure in this setup gate. Counts repeat common fixture checks;
  they are not distinct unit-test totals. No flight or FPS benchmark claimed.

Receipts are adjacent JSON files. Full logs remain in generated/reports/unreal-*.
Preview: generated/previews/signal-lost-pipeline.png.
Package: generated/unreal/signal-lost/package/Windows/SignalLost.exe.
No new binaries or template packs are pushed to Git; reproducible setup/configuration
and scripts are versioned. This fixture is visibly a prototype, not final space art.
