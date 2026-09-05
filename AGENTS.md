# AI GAME STUDIO

You are the primary development agent for this 3D game project.

## Core Tools

Godot:
godot

Blender:
blender

Git:
git

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
