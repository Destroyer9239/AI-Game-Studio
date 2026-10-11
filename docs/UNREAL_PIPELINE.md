# Unreal production foundation — 2026-10-10

The user selected Unreal Engine 5. The active target is now **UE 5.7.1**, already
installed at C:\Program Files\Epic Games\UE_5.7. The working Godot reference is
preserved at commit 3aea70d (pushed), including its short Last Light mission.
This is a migration foundation, not a claim that the whole Godot game is ported.

## Engine and tool reassessment

| Option | Decision for this project |
|---|---|
| Unreal 5 | Selected: integrated high-end rendering, editor automation and Blueprint/C++ production path; existing local install avoids a new engine download. |
| Godot Forward+ | Keep the tested behavior/asset reference and automation. No destructive conversion or deletion. Its existing performance results remain Godot results. |
| Unity HDRP | Credible high-end alternative, but another gameplay/material rewrite with no advantage over the user's selected UE direction for this milestone. Not installed or benchmarked here. |
| Custom engine | Reject for this project: adds rendering/editor/platform maintenance instead of completing content. |
| Blender | Keep as editable source of original mechanical and architectural assets. |
| ComfyUI/SDXL/Real-ESRGAN | Keep local art generation; no new model required. |

UE features do not automatically turn the existing prototype meshes into AAA art.
Lumen GI/reflections, virtual shadow maps and TSR are configured. Hardware ray tracing
is not enabled or claimed. Nanite is a per-asset production decision, not a blanket
switch on these small fixture meshes. No custom engine/plugin/source build is needed
for the current editor pipeline.

Sources: [Epic Python automation](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python?application_version=5.7),
[Lumen performance guidance](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-performance-guide-for-unreal-engine?application_version=5.7),
[Unity HDRP overview](https://unity.com/resources/lighting-environments-hdrp-unity-6?isGated=false).
Python runs in the UE editor, not as shipped gameplay logic. 4K output and native 4K
internal rendering must be reported separately; TSR is an upscaler. No UE performance
numbers are borrowed from the previous Godot benchmark.

## Layout and reproducibility

- unreal/Cinder/Cinder.uproject: separate UE project, pinned to 5.7.
- unreal/Cinder/Config: versioned project/render/input defaults.
- Content/Cinder/Generated: disposable import/test output, rebuilt only by this pipeline.
- Content/Cinder/Authored: reserved for future hand-authored levels, Blueprints and assets.
  Never write authored work into Generated; never overwrite Authored from a generator.
- tools/unreal: Blender adapter, Unreal editor build/validation and packaging runner.
- generated/unreal: FBX intermediates and import/source SHA256 manifests, ignored by Git.
- generated/reports/unreal-*: logs, structured acceptance results and timing.
- generated/previews/unreal_pipeline.png: actual renderer output when preview succeeds.

Installed Epic template/character/input/prototyping packs are copied locally only if
missing. They stay out of this Git repository and are reconstructed from the same UE
installation. No marketplace download or account login is needed for these local packs.
Generated .uasset/.umap files are reproducible, not the only source of work. Before
adding large hand-authored binaries, verify remote Git LFS capacity (or choose
Perforce for a larger team). Scoped LFS/locking attributes are prepared for Authored;
git-lfs 3.7.1 is present. No history rewrite or unapproved
remote binary-storage upload is performed by setup.

## Agent commands

Run with pwsh -NoProfile -File tools/unreal.ps1 ACTION. If pwsh is not on PATH,
dot-source tools/studio-common.ps1 and invoke Get-StudioShell as existing tools do.

| Action | Behavior |
|---|---|
| doctor | Inspect pinned engine, memory, free disk and installer discovery. |
| setup | Copy missing installed first-person template dependencies. No downloads. |
| export | Actually run Blender and create four static FBXs plus source hashes. |
| build | Setup, export, import, create the test level, validate and save. |
| validate | Reload and verify the existing generated Unreal assets/map. |
| test | Validate, enter PIE, verify first-person spawning, grounding, movement and clean exit. |
| preview | Validate and request a GPU screenshot of the review camera. |
| launch | Open the Unreal editor on this project. |
| play | Launch the installed editor's game mode. This is not a packaged executable. |
| package | Run UAT BuildCookRun for Windows; missing SDK/toolchain fails visibly, never auto-installs. |

Set UE_ENGINE_ROOT only to another compatible 5.7 install if necessary. Upgrades need
their own branch and acceptance run. Do not silently substitute UE 5.6 or latest online.

## Asset contract and migration boundaries

The static adapter opens original .blend files in a separate factory-startup Blender
process, bakes evaluated meshes, preserves the source files, joins geometry for a
bounded exterior fixture, exports FBX and records triangle/material/dimension data.
Armatures are explicitly rejected. Unreal checks imported mesh sections, material
assignments, simple collision and meter-to-centimeter bounds. Godot-only collision
helper geometry is excluded. Simple UE boxes are suitable for this exterior test,
not navigable interiors or a moving spacecraft physics rig.

Existing GLBs remain unchanged. FBX is used through UE's established static importer;
the experimental FBX Interchange route is disabled for this adapter. Future glTF/USD
scene imports need separate acceptance; compatibility is not assumed.

The current UE palette is a migration fixture and does not reproduce every original
Blender/Godot material. Concrete imports actual basecolor/roughness/normal source maps,
sets data-map color space and flips OpenGL normal green for Unreal. No fabricated PBR.
See tools/unreal/asset_review.json for the disposition of every asset/system family.

## Human/toolchain steps

The local machine has an RTX 5070 Ti, Intel Core Ultra 9 285K, about 32 GB RAM and
about 1.2 TB free on C:. UE 5.6 and 5.7 installations exist; 5.7.1 is selected.
Visual Studio Installer/vswhere and a Windows SDK include installation were not found
in standard locations or registered installed-program inventory. Editor automation can
run without compiling project C++, but a professional C++/packaging workflow needs a
verified toolchain.

Recommended: Visual Studio 2022 17.14, Game development with C++, Desktop development
with C++, MSVC v143 14.44, Windows SDK 10.0.22621 or newer. Import the prepared
tools/unreal/development.vsconfig. Check the IDE edition's license for your organization.
The user explicitly approved this multi-GB toolchain installation on 2026-10-10.
The official Microsoft bootstrapper was downloaded and its Authenticode signature
verified before launch. Installation uses the prepared component config and
--norestart; completion and packaging must still be verified, not inferred from launch.
[Epic's UE 5.7 toolchain requirements](https://dev.epicgames.com/documentation/en-us/unreal-engine/setting-up-visual-studio-development-environment-for-cplusplus-projects-in-unreal-engine?application_version=5.7).

## Next production gates

1. Validate the Windows toolchain and produce/play a packaged build.
2. Port the three-stage mission, interaction/save state and automated gameplay tests to
   Blueprint/C++; the existing Godot behavior is the acceptance reference.
3. Establish one convincing UE hero location: architecture, original signage, material
   masters/instances, practical lighting, Niagara weather and authored ambience.
4. Port the robot through a dedicated skeletal workflow and validate movement/animation.
5. Add World Partition/streaming only when the small scene's gameplay and art justify it.
6. Benchmark packaged native/internal and upscaled 4K separately with Unreal Insights,
   fixed traversal, frame percentiles and GPU timings. Do not grow the city first.

## Acceptance and known limits

Actually executed Blender exports for the fighter, foundry, market and relay building;
imported them into Unreal; checked centimeter bounds, geometry sections, materials,
source/export hashes and collision; saved and reloaded the generated level. A separate
PIE run verified the first-person Blueprint, grounding, movement over one meter and
clean end-play. Captured and inspected a real 3840x2160 GPU screenshot. This is a 4K
output image, not a native-internal-resolution performance benchmark.

Packaging was actually attempted with UAT BuildCookRun and failed with ExitCode 6.
UnrealBuildTool explicitly reports no valid SDK for Win64; the engine's Windows SDK
configuration files do exist. Report: unreal-348385a616c6460da98524283c2bd806.
Do not report a packaged executable or completed C++ setup until this gate passes.

Resolved setup failures: missing editor subsystems in minimal Python commandlet mode,
an engine divide-by-zero during NullRHI level creation, Python API naming differences,
and batch argument quoting. This installed build now uses unattended full-editor GPU
execution with RenderOffscreen. Do not call this NullRHI/headless renderer validation.
The log validator ignores only named optional profiler/tablet DLL startup notices and
the engine's absent-default-concurrency notice; real asset-load errors, Python errors,
fatal errors, missing success markers and nonzero exits still fail the operation.

The Windows-only project disables AndroidFileServer so it does not create a device
connection token in versioned config. No credentials or device tokens are committed.
The local LFS hook is installed; no new LFS binary payload has been uploaded.

This stage does not migrate the mission/save system, weather, audio, robot rig or
streaming. The test scene is intentionally small and uses temporary palette materials.
The existing robot remains untouched. Editor tooling and PIE work without a new
download. The separately approved toolchain installation is being verified.
