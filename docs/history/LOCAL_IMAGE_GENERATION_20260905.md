# Local image generation: inventory and recommendation

Inspected 2026-09-05. No software, Python packages or AI image models were installed during this stage. The current Blender/Godot automation already works with existing tools.

## Measured machine inventory

| Item | Finding |
| --- | --- |
| GPU | NVIDIA GeForce RTX 5070 Ti, 16,303 MiB total VRAM; latest sample had 10,036 MiB free. Other applications already use part of VRAM. |
| NVIDIA driver | 591.86. `nvidia-smi` reports CUDA 13.1 driver support. |
| CUDA Toolkit | `nvcc` was absent on PATH; standard NVIDIA GPU Computing Toolkit directory was not found. Driver support does not prove Toolkit/PyTorch availability. |
| CPU | Intel Core Ultra 9 285K. |
| RAM | 34,049,167,360 bytes reported by Windows (about 31.7 GiB, nominal 32 GB). |
| Storage | Latest normal-access C: query reported 2,061,088,190,464 bytes free (about 1.87 TiB). Earlier sandbox query reported a lower figure (~1.04 TB); both show ample headroom, but use a fresh normal-access query before installing. |
| Python | Python launcher available. Installed interpreters: 3.11.9, 3.14.5 and uv-managed 3.12.13. `python`/`python3` resolve to WindowsApps aliases, so the tested adapter uses `py -3.11`. |
| Python image/ML libraries | Checked interpreters did not expose torch, diffusers, transformers, Pillow or NumPy. Other application-private environments were not exhaustively scanned. Blender provides its own Python. |
| Ollama | Client 0.15.2 installed; local model manifest directory contains `llama3`. No responding API at 127.0.0.1:11434 during final inventory. |
| Cached models | Hugging Face cache contains text/embedding models: DistilBERT, multilingual E5, Qwen3-8B-GGUF and MiniLM. No diffusion model was found in that cache. |
| Other relevant software | Blender 5.0.1, Godot 4.7.2, Maya 2026 and Adobe Substance 3D for Maya directories exist. Presence of Maya/Substance files does not establish license availability or a diffusion service. |
| Existing image services | No responding ComfyUI API on 127.0.0.1:8188. No ComfyUI, AUTOMATIC1111, Fooocus, InvokeAI or SwarmUI directory found in the bounded common-location search. |

Inspection covered C:\Tools, common program directories, selected user project/Documents/Downloads folders, Start Menu entries and model-cache directory names. This is not a claim that every private virtual environment or arbitrary disk folder was searched. An initial `ollama list` tried and failed to auto-start its existing service under sandbox restrictions; the reusable doctor instead uses read-only HTTP probes and never starts services.

Refresh evidence with the agent-run `pipeline.ps1 doctor`. The latest successful raw inventory from setup is `generated/reports/20260905-143556-321-8dcdae/local-inventory.json`.

## Recommended installation, pending approval

**ComfyUI Portable for Windows, NVIDIA CUDA 13.0 build, plus the official SDXL 1.0 base checkpoint.** This is my engineering recommendation for this machine and workflow, not a measured image-generation benchmark.

Portable ComfyUI bundles an independent Python runtime and has a current NVIDIA CUDA 13.0 package. It avoids changing the existing Python installations. Use the official package for modern RTX cards, not the older CUDA 12.6 package. [Official portable guide](https://docs.comfy.org/installation/comfyui_portable_windows).

The installed driver is newer than the documented Windows driver minimum for current CUDA 13.0 PyTorch wheels. Confirm CUDA execution in the portable environment before accepting installation; do not substitute an old PyTorch build for this Blackwell GPU. [PyTorch release guidance](https://pytorch.org/blog/pytorch-2-12-release-blog/).

Initial model: `sd_xl_base_1.0.safetensors`, **6.94 GB**, from the official repository. Download that single checkpoint, not the entire 76.9 GB repository or both duplicate VAE variants. The base model can run independently of the refiner. Its license is CreativeML Open RAIL++-M; retain that model provenance with jobs. [Official model card](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0), [checkpoint listing](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/tree/main).

Proposed location: `C:\Tools\ComfyUI\` with its embedded runtime and model folder, outside the game repository. The runtime/archive adds several GB beyond the model; reserve **30 GB** for the initial bundle, download archive, extraction and first outputs. This is a planning allowance, not a verified exact package size. The agent should confirm the selected release's actual size before downloading. Do not install optional custom nodes, paid/cloud nodes, extra models, system CUDA Toolkit or new drivers as part of this first setup.

Run the local service on `127.0.0.1:8188`. ComfyUI exposes workflow submission, history, node/model inspection and image retrieval APIs suitable for unattended jobs. The repository already has a standard-library adapter for that interface. [Official local server routes](https://docs.comfy.org/development/comfyui-server/comms_routes).

Start at 1024×1024, batch size 1, with the base model alone. The available VRAM suggests this is a sensible starting point; benchmark on this machine after installation. Do not close the user's GPU applications automatically. The local workflow has no metered API bill or required paid service; ordinary hardware/electricity costs still apply.

## Fit for the requested artwork

| Output | Proposed workflow and acceptance |
| --- | --- |
| Concept art | SDXL seeded prompts and multiple views; agent selects original silhouettes and translates them into actual Blender geometry. |
| Reference images | Same local generation plus controlled Blender renders for consistent scale and camera views. Generated multi-view art must be checked for inconsistency. |
| Seamless textures | Generate material appearance, then use an authored wrap/offset/inpaint or procedural Blender workflow. Check a repeated 3×3 grid and edges; a “seamless” prompt alone cannot guarantee tiling. |
| Decals | Generate motifs on a plain background, then explicitly author/clean alpha and edge padding. Use vector/text tools for exact markings and readable lettering. |
| UI artwork | Generate illustration/background layers locally. Keep functional typography and crisp interface symbols in authored/vector form. |
| Roughness/metallic source maps | Use generated art as source masks, then derive and tune non-color scalar maps. Author binary metallic regions deliberately; bake physical normals from geometry when possible. Do not claim a color image is a calibrated PBR material. |

These are planned task-specific workflows, not six already-tested image generators. The prepared basic workflow only generates opaque, non-guaranteed-tileable images. The adapter explicitly refuses alpha/seamlessness guarantees until those workflows are implemented and verified.

ComfyUI is preferred over assembling a new Diffusers environment because its portable runtime and saved workflow graphs reduce initial environment work while retaining API automation. The existing Ollama/llama3 setup can optionally help text briefs later, but it is not an installed replacement for the proposed image workflow. A later concept-art experiment could evaluate FLUX.1-schnell, whose official model is 12B parameters and Apache-2.0 licensed; its larger footprint makes it an optional second model, not the initial download. [Official FLUX.1-schnell model card](https://huggingface.co/black-forest-labs/FLUX.1-schnell).

## Architecture already prepared

The multi-provider stage now includes a ComfyUI configuration/health adapter and
unified manifest integration; its real loopback HTTP protocol test passes against
a mock backend. This does not change the installation or inference status.
See [ASSET_PROVIDERS.md](ASSET_PROVIDERS.md) for routing and image-purpose guidance.

- `tools/imagegen/requests/`: semantic job records (asset, purpose, prompt, negative prompt, seed, size, model source/license and constraints).
- `tools/imagegen/workflows/`: checked-in API-format graphs using core local nodes.
- `tools/imagegen/submit_image.py`: dry-run by default; explicit `--execute` submits to an existing loopback service, polls with a deadline, detects failures and saves PNG output hashes and metadata. It does not install or start anything. A timeout records the prompt ID without interrupting unrelated jobs.
- `generated/image-jobs/`: ignored raw job bundles, including request, workflow and result JSON. No generated image is claimed for a dry-run.
- `generated/concept-art/` and `generated/textures/`: curated source artifacts and sidecars.
- `game/assets/textures/<asset>/`: reviewed runtime maps, with Blender material bindings and correct color spaces.

The dry-run and offline request checks were actually executed successfully. No live ComfyUI dispatch or image inference was possible because the backend/checkpoint is not installed. Future installation acceptance must include a CUDA tensor check, a real API image job, visual inspection, recorded timings/VRAM and a texture seam check before calling the image pipeline complete.

**Next recommended action:** approve the portable ComfyUI + single SDXL checkpoint installation above. The agent can download, configure, start and test it; no manual PowerShell session should be required. The large download is the reason this setup stage stops at a concrete installation proposal.
