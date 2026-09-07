# Local character technical pipeline

Original maintenance robot: editable Blender source, ten segmented meshes, eight named bones, normalized rigid skin weights, three authored materials and Idle/Walk clips. This is a technical fixture, not a polished humanoid. No image textures are required.

Godot imports skin and animation without flattening. CharacterBody3D owns capsule collision and NavigationAgent3D. A cheap capsule proxy starts at 70 m.

`tools/world/worker_character.json` is the reusable validation contract. Blender validation uses `--background --factory-startup --python-exit-code 1 --python blender/scripts/validate_character.py -- tools/world/worker_character.json`. This read-only check covers topology, budgets, finite vertices, materials, normalized weights, bone references, animations, dimensions, orientation and GLB presence. Generation already succeeded; do not regenerate to validate.

Eight canonical references in `generated/references/canonical_worker` passed actual visual inspection and the hash/invariant gate. Future player/civilian/guard/enemy specs can use this contract; their art and behavior are not implemented merely by naming a class.

Run `pwsh -NoProfile -File tools/world.ps1 test-gameplay`. It tests movement, collision, interaction, objective, events, save/load, NPC navigation, weather reaction, skeleton/clips and proxy availability. The separate streaming stress test checks persistent health/terminal state through 20 cycles. Organic deformation, retargeting and professional animation remain future work.
