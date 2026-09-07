# Asset providers and autonomous workflow

Implemented over checkpoint `4372fb9`; checkpoint tag `providers-before-setup` preserves that baseline. The agent runs the commands, authors original designs and checks the results. No software/models were installed and no paid jobs were submitted during setup.

## Entry points

Run from the repository root with `pwsh -NoProfile -File tools/pipeline.ps1 <operation>`. Python 3.11, Blender, Godot and PowerShell 7 already exist locally. Godot resolution still prefers PATH, then `C:\Tools\Godot\godot.exe`.

| Operation | Behavior |
| --- | --- |
| `providers` | Offline capability registry and configuration presence; no account requests. |
| `provider-status` | Registry plus a bounded local ComfyUI health probe. Authentication remains unverified. |
| `asset-plan -RequestFile tools/providers/requests/meshy_interceptor.json -Quality hero` | Offline exact request plan, selection reason, availability, quality and cost estimate. |
| `asset-create -RequestFile tools/providers/requests/blender_fighter.json` | Plan and execute local Blender pipeline. Paid providers return an awaiting-approval plan only. |
| `provider-execute -Job generated/provider-jobs/<id> -Approval generated/approvals/<receipt>.json` | Execute exactly one approved paid job, or a local plan without a receipt. |
| `provider-poll -Job <job>` | Read the recorded task; never submit again. |
| `provider-fetch -Job <job>` | Retrieve completed media; static GLBs go through Blender cleanup and Godot. |
| `provider-quote -Job <job>` | Official Higgsfield CLI cost query, or Meshy estimate. Not a generation request. |
| `provider-balance -Provider meshy` / `provider-usage -Provider meshy` | Read-only account queries, credentials required. Usage is team-plan dependent. |
| `asset-process -Job <job> -SourceFile generated/raw/<job>/0.glb` | Process an explicitly selected staged model. Never submits to a provider. |
| `asset-process -Job <job> -Repair` | Explicit rebuild of the recorded provider/source path, with previous blend/GLB/manifest archived in staging history. |
| `test-asset -Asset <id>` / `preview -Asset <id>` | Godot import, material/UV/geometry/collision validation; preview additionally captures GPU output. |
| `validate` / `launch` | Validate or launch the existing game. |
| `multiview -RequestFile tools/providers/requests/hero_multiview.json` | Prepare dependent concept and reference jobs; does not generate images or spend credits. |

Machine interface: `py -3.11 tools/providers/cli.py <action>`. Actions include `providers`, `status`, `plan`, `create`, `process`, `execute`, `poll`, `fetch`, `quote`, `validate`, `preview`, `launch`, and `multiview`. `validate --asset <id>` checks one asset; `validate` checks the game. CLI output is JSON with nonzero exit on failure. The PowerShell wrapper additionally saves stage logs/reports.

## Choosing a route

Requests under `tools/providers/requests/` use `name`, `asset_type`, `operation`, `provider`, `quality`, `complexity`, `cost_policy`, `prompt`, `source_images`, optional named `reference_views`, `options`, `cleanup` and `provenance`.

The default favors controlled local procedural work for mechanical assets. A source model chooses Blender cleanup. A hero/high-complexity request or supplied references with `cost_policy: consider_paid` considers Meshy or an installed Higgsfield CLI. Organic/reference-driven shapes can produce a paid Meshy plan. An explicitly chosen provider overrides automatic routing, but never bypasses capability validation or approval. Availability signals are configuration hints, not proof of authenticated access or measured quality. The plan exposes unmet prerequisites rather than silently installing tools or spending money.

The agent completes a new Blender generator before executing its plan. Prompt-to-procedural geometry is an agent authoring responsibility, not a hidden text-to-mesh model. Hero source settings use detailed geometry/textures on the reviewed Higgsfield text route; Meshy polygon targets are explicit, bounded request options. Human/agent preview review remains necessary for design quality.

| Profile | Default maximum triangles | Materials | Cleanup LOD ratio |
| --- | ---: | ---: | ---: |
| prototype | 3,000 | 4 | none |
| background | 6,000 | 4 | 0.4 |
| standard | 20,000 | 12 | 0.5 |
| hero | 40,000 | 16 | 0.5 |

These are project defaults, not targets to fill. Explicit cleanup budgets may be lower. Decimation of the main mesh requires `allow_decimate: true`; otherwise over-budget output fails. Hero cleanup cannot disable LOD preparation. Tiny meshes below 101 triangles do not need another decimated copy. Separate LOD GLBs are exported/imported; Godot's automatic mesh LOD import is also enabled by the existing importer. Separate files do not automatically configure gameplay distance switching. Procedural generators must author appropriate LODs or use Godot's importer and inspect them.

## Meshy: implemented, live account test pending

`tools/providers/meshy/adapter.py` uses official REST and `MESHY_API_KEY` from the process environment. There is no key in this repository or current session. It supports text preview/refine, image and multi-image generation, remesh, retexture/PBR, humanoid rigging, preset animation, submission, polling, output retrieval and reported `consumed_credits`.

Text generation uses separate geometry preview and texture-refine tasks. Each needs its own approval; a 20-credit preview is not a complete textured generation budget. Reviewed models are pinned rather than silently using a changing `latest`. [Text API](https://docs.meshy.ai/en/api/text-to-3d).

Single-image and up to four-view routes accept public image URLs or local PNG/JPEG files encoded for the official API. PBR is requested for textured outputs. Smart topology is supported for the reviewed text/single-image route; this adapter refuses smart-topology multi-image combinations until their schema/pricing is reviewed. [Image API](https://docs.meshy.ai/en/api/image-to-3d), [multi-image API](https://docs.meshy.ai/en/api/multi-image-to-3d).

Remesh supports bounded triangle targets. Retexture preserves UVs and requests PBR. Rigging is guarded to humanoids; animation requires a recorded rig and an official library action ID. Rigged/animated downloads remain staged for specialized Blender/Godot handling, because static cleanup deliberately rejects armatures/actions/morphs. [Remesh](https://docs.meshy.ai/en/api/remesh), [retexture](https://docs.meshy.ai/en/api/retexture), [rigging](https://docs.meshy.ai/en/api/rigging), [animation](https://docs.meshy.ai/en/api/animation).

Pricing snapshot checked 2026-09-05: standard text preview 20 credits, refine 10, textured image/multi-image 30, remesh 5, retexture 10, rig 5, animation 3. Smart-topology text is 5 and textured single-image 15 for the implemented defaults. Recheck before approval; these are not guaranteed account billing caps. [Official pricing](https://docs.meshy.ai/en/api/pricing).

Balance is read-only. Usage lists recent completed task credits and requires a Studio/Enterprise team key; a 403 means unavailable, not zero usage. Default usage query covers the last 30 days/first page; the adapter does not claim an exhaustive billing export. [Balance](https://docs.meshy.ai/en/api/balance), [usage](https://docs.meshy.ai/en/api/usage).

Optional official MCP: `@meshy-ai/meshy-mcp-server`, with the same environment credential. It can be added to the agent's MCP configuration later using the official package, but is not required by this direct adapter. Any MCP generation must obey the same explicit approval policy. No MCP package was installed. [Official AI/MCP guide](https://docs.meshy.ai/en/api/ai).

## Higgsfield: verified official capabilities, live CLI test pending

The integration uses the official CLI, not website automation. Reviewed models: `tripo_3d` (text), `image_to_3d`, `multi_image_to_3d`, `3d_rigging`, `nano_banana_2` (generation/reference editing) and `seedance_2_0` (text video). Image editing accepts up to 14 local references; the 3D adapter accepts up to four matching views. New model flags require schema review. [Official model catalog](https://raw.githubusercontent.com/higgsfield-ai/cli/main/MODELS.md).

The CLI is not installed or logged in. The agent can install the official Windows binary/npm package when this provider is selected. The human then completes the official `higgsfield auth login` flow. After login, the agent should check `model get`, `generate cost`, and account status before proposing any paid generation. The bridge uses `generate create` once, saves its job ID, then uses `generate get`. Live output schemas/authentication have not been exercised. The Cloud SDK's HF credentials are a separate auth mechanism and are not used by this CLI adapter. [Official CLI installation/authentication/commands](https://github.com/higgsfield-ai/cli).

All Higgsfield generation/editing/video/3D/rigging actions are treated as paid. Cost is unknown until an official quote/account check; the adapter never invents a price. No credits were spent.

## ComfyUI: prepared local API, installation pending

Configuration: `tools/providers/image_generation/comfyui.json`. Workflows: `tools/imagegen/workflows/`. The provider reuses `tools/imagegen/submit_image.py`; it does not create a competing client. It probes health, submits a saved graph, polls history, retrieves PNG outputs, records hashes and stages a result bundle plus the unified asset manifest. Only loopback HTTP and reviewed core local nodes are allowed; redirects/custom/paid nodes are rejected. The local HTTP protocol was exercised with a test server, not a diffusion model. [Official server routes](https://docs.comfy.org/development/comfyui-server/comms_routes).

The standard image request's `kind` maps concept/environment art to `concept`, views to `reference`, decals to `decal`, UI/icons to `ui`, material/planet/skybox appearance to `texture`, and base-color/normal-source/emission masks to `map`. Describe the precise purpose in prompt/notes. The basic workflow produces opaque image sources only. Seamless output, alpha decals, coherent cubemap seams and calibrated PBR maps need dedicated postprocessing/baking and acceptance checks; `tileable_required` or `alpha_required` currently fails instead of making false guarantees. Normal maps should usually be baked from geometry; an image is only a reference/source until converted and checked.

Recommended installation remains ComfyUI Portable NVIDIA CUDA 13 build plus the single official SDXL base checkpoint (6.94 GB); reserve 30 GB for runtime/archive/extraction/model/output. No large download was approved or performed. See [local inventory and exact installation proposal](LOCAL_IMAGE_GENERATION.md). After approval, the agent can download, configure, start and verify CUDA/API inference. No manual PowerShell work is necessary.

## Multi-view and provenance

`multiview` writes a draft sequence and concept/front/side/rear/top image requests under `generated/reference-plans/<id>/`, followed by a 3D request referencing the selected images. Review the concept first. Derive consistent views with reference-image editing or Blender orthographic rendering; independent SDXL text prompts are drafts and cannot guarantee matching geometry. Store the selected PNG/JPEG views at the declared paths, then plan the multi-image 3D task. Planning fails if required local files are absent. Paid image edits and 3D generation remain separate approvals.

Every completed provider route records `generated/manifests/<id>.json`: ID/name/type/quality/provider/model/method/prompt, reference views and preserved reference hashes, original file/hash, processed blend/GLB, texture slots, triangle count, scale, collision, LODs, Godot scene, validation, preview/review state, date, estimated/reported credits and license/provenance notes. Media-only fields stay null where not applicable. Images have their original request/workflow/model/license/seed metadata too. Original downloads stay under `generated/raw/<job>/`; video remains source media and is never injected into the runtime scene automatically.

Cleanup is static and conservative: preserve material graphs/UVs and embedded PBR images, apply transforms, correct negative winding, normalize dimensions/pivot, check geometry/budgets, make a box collision proxy, save an editable blend and export GLB/LOD. Source GLB texture slots are compared before promotion, and Godot checks imported base-color/normal/metallic-roughness/emission connections. Broken references fail. A cleanup fixture caught Blender unpacking an already-packed image on a redundant `pack()` call; the fixed path preserves existing packed buffers.

Logs/previews/staging/approvals are ignored. Curated runtime artifacts, sources, specs, manifests and selected references belong in Git. This checkpoint includes the small cleanup fixture and original fighter; the unrelated VS Code Counter report is ignored without editing it.

## Cost boundary and errors

Planning never submits. Local Blender/Godot/ComfyUI need no credit approval. Before a paid call, present provider/operation/asset/quality/estimate and obtain explicit user approval. The agent then records it through:

```text
py -3.11 tools/providers/cli.py approve --job <job> --approval generated/approvals/<id>.json --user-reference <actual-approved-message-reference> --max-cost <ceiling> --unit credits
```

This is an agent bookkeeping command, not a mechanism to fabricate consent. Receipts expire, bind the exact plan hash and support one submission only. Changed input files invalidate the plan. The exclusive submission latch remains after timeouts or ambiguous failures, preventing an automatic duplicate charge. Follow-up paid operations require new plans/approval. Cost ceilings only guard known estimates; provider APIs do not enforce this local ceiling. Unknown costs must be quoted and reviewed first. Authentication checks happen before consuming approval.

Missing credentials, unsupported methods, unsafe paths, unreviewed nodes and unrecognized responses fail explicitly. A cleanup/validation failure preserves the source and records available logs; repair the affected stage. Never declare a live provider tested because its offline plan or mock transport passed.

## Acceptance

Run `pwsh -NoProfile -File tools/test-providers.ps1`. It creates the textured source in actual Blender, plans/selects the local provider, performs cleanup, imports and tests in Godot, renders the preview, checks PBR image bytes/transforms/origin/normals/LOD, exercises provider/cost/auth/HTTP tests, and regenerates the original fighter through the provider interface. It performs no paid submission.

See [PROVIDER_TEST_RESULTS.md](PROVIDER_TEST_RESULTS.md) for the measured final results and remaining live-service limitations.

## Local image/environment acceptance update (2026-09-06)

ComfyUI now supports managed loopback lifecycle, actual SDXL inference and tiled
Real-ESRGAN 4K processing. See LOCAL_IMAGE_GENERATION.md for verified status. Plans
include local alternatives, output destinations and an explicit external recommendation
field. Price gates remain unchanged; no paid job was submitted in this stage. Meshy
user-level key presence was detected, but its safe authentication check returned 401.
Rejected independent spacecraft views are unsuitable for paid reconstruction.
