# Runtime textures

Put only selected and validated runtime maps in per-asset directories here. Authoring sources belong in `generated/textures/`. Bind maps in Blender materials, using sRGB for color/emission and non-color for data maps; export embeds GLB dependencies. Avoid duplicate external runtime copies unless Godot materials need them directly.
