# Small block and bounded world streaming

`game/world/city_block.json` defines one original Cinder Exchange block with four
buildings (industrial, commercial and office) and two neighboring service cells.
It records district defaults, IDs, placement, entrance orientation and loading budgets.
The center contains the actual detailed architecture; neighbors only extend the road.
Roads, sidewalks, curbs, drains, lane markings, lights and original authored signs are
generated per cell. All building entrances face the central street. Additional district
rules are prepared data; the current generator proves the industrial district only.

`world_streamer.gd` uses Godot ResourceLoader threaded requests for cell PackedScenes
and their declared building dependencies. Duplicate pending/loaded IDs are suppressed.
It loads within 82 m, unloads beyond 110 m and limits live cells to three. At most one
completed scene is instantiated each frame. Instantiation and procedural prop creation
still happen on the main thread: this is a bounded foundation, not zero-hitch streaming.
Future large cells need time-sliced instantiation and measured memory-cost admission.

State hooks capture/restore per-cell dictionaries. Unloading removes physics and
NavigationRegion3D children together. Reviewed navigation strips cover the street and
sidewalk band, excluding building footprints. Regions align at cell edges. Navigation
exists; an NPC movement test is part of the next integrated gameplay stage.

Eleven real headless checks verify duplicate suppression, neighbor preload, one instance
per ID, load success, four buildings, collision, navigation region presence, unloading,
state capture/restore and the loaded-cell budget. GPU overview and all three building
variants were inspected. This is a coherent prototype block, not final environment art.

Run `pwsh -NoProfile -File tools/world.ps1 validate` or `preview`. Reports are saved
under generated/reports/world-*; the actual GPU overview is generated/previews/city_block.png.
`launch` opens the current overview; player control is implemented in the next checkpoint.

Frustum culling and imported mesh LOD remain engine-supported. Shared materials avoid
per-building texture duplication; sidewalks reference one shared material-factory texture.
Assembled HLOD/skyline proxies, occlusion proxies, arbitrary 2D region grids and byte-based
memory admission remain extension work. Current streaming distance is a one-dimensional
road corridor, deliberately limited to three cells for this test.
