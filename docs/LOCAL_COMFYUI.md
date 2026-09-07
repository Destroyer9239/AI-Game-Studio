# Installed local image backend — 2026-09-06

ComfyUI Portable **v0.34.0** is installed at
`C:\AI\ComfyUI\ComfyUI_windows_portable`, outside Git. Embedded Python 3.13.14,
Torch 2.13.0+cu130 and CUDA 13.0 successfully executed GPU tensors and real image
inference on RTX 5070 Ti (16,303 MiB), driver 591.86. No system CUDA Toolkit,
system Python packages, drivers, custom nodes or security settings were changed.
The machine has nominal 32 GB RAM; keep other applications' memory use in mind.

## Verified downloads

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| Official NVIDIA portable v0.34.0 archive | 2,146,721,943 | `ed57cc6b19ae3d83add1ecebfdd56b25e04e0008cf0fe9af43a4ad8797e2a24c` |
| SDXL base 1.0 checkpoint | 6,938,078,334 | `31e35c80fc4829d14f90153f4c74cd59c90b779f6afe05a74cd6120b893f7e5b` |
| RealESRGAN_x4plus.pth | 67,040,989 | `4fa0d38905f75ac06eb49a7951b426670021be3018265fd191d2125df9d682f1` |

Archive checksum matched official GitHub asset metadata; SDXL matched official
Hugging Face LFS metadata. Real-ESRGAN was downloaded from its official release;
its digest is a locally recorded checksum, not an independently published signature.
The already-approved portable/SDXL installation was completed; the added upscaler
is only 67 MB, below the user's 2 GB approval threshold. No further installation
is required for this stage.

Sources: [Comfy portable guide](https://docs.comfy.org/installation/comfyui_portable_windows),
[official v0.34.0 release](https://github.com/Comfy-Org/ComfyUI/releases/tag/v0.34.0),
[SDXL official model](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0),
[Real-ESRGAN release](https://github.com/xinntao/Real-ESRGAN/releases/tag/v0.1.0).
SDXL uses CreativeML Open RAIL++-M; Real-ESRGAN code/model release is under BSD-3-Clause.
Retain these provenance notes; image originality and suitability still need review.

## Agent commands

Run PowerShell entry points with `pwsh -NoProfile -File`:

- `tools/pipeline.ps1 comfy-start` / `comfy-stop` / `comfy-restart` / `comfy-status`
- `tools/pipeline.ps1 asset-create -RequestFile tools/providers/requests/industrial_concrete_source.json`
- `tools/pipeline.ps1 image-4k -RequestFile tools/providers/requests/industrial_concrete_source.json`
- `tools/environment.ps1 build` for current 4K material → Blender → Godot render.
- `py -3.11 tools/imagegen/test_local_backend.py` for explicit local live acceptance.

The unified provider automatically starts an unavailable local backend. The low-level
`submit_image.py` remains dry-run by default and only submits with `--execute`.
Management owns one UUID-tagged wrapper; cooperative stop refuses a busy queue and
never kills unrelated processes. Verified dead-PID recovery handles interrupted
sessions conservatively. An unrecognized live process or stale start lock requires
inspection, not indiscriminate termination. The API binds **127.0.0.1:8188 only**;
custom nodes, paid API nodes and browser auto-launch are disabled. No firewall changes.

Jobs retain workflow/request hashes, seed, prompt ID, history status, PNG hashes,
elapsed time and sampled whole-device VRAM under ignored `generated/image-jobs`.
Provider manifests retain useful evidence under `generated/manifests`. Missing models
fail before submission. Deadlines retain prompt IDs; no global queue interrupt is sent.
Timeouts may leave a local job running, so inspect queue/history before retrying.
Both legacy and V3 Comfy core combo schemas are supported and regression-tested.

## Workflows and reviewed limitations

Versioned core graphs cover concept, environment concept, multiview reference,
texture source, decal/signage source, UI art, emission artwork and sky reference.
They are semantic starting recipes, not eight specialized trained models. SDXL
produces opaque appearance artwork. Alpha, exact typography, projection, seamlessness,
PBR calibration and cross-view consistency require explicit downstream work.
See [material factory](MATERIAL_FACTORY.md) and [skies/rendering](RENDERING_AND_SKIES.md).

Real concept and four requested spacecraft views were generated. Selected concept
v2 is useful as a design study, with some edge cropping. The independent view outputs
failed shape/view consistency and include unwanted pseudo-markings; they are explicitly
rejected as production 3D references. Do not send them to a paid generator. Use an
agent-authored Blender blockout and controlled orthographic renders, or a separately
reviewed reference-conditioned model, for a dependable multiview package.

Meshy user-level configuration was detected without exposing the key. A safe read-only
authentication check returned HTTP 401; **configured is not authenticated**. No Meshy,
Higgsfield or other external generation credits were spent. Higgsfield stays optional;
Gemini remains unimplemented. Paid gates require exact explicit one-use approval.

No new large model is recommended until the local material/street-corner workflow
has been evaluated. A future reference-conditioned model would require a concrete
source, size, license, quality justification and approval if over approximately 2 GB.
