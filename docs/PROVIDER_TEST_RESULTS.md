# Provider acceptance results

Tested 2026-09-05 America/Phoenix (2026-09-06 UTC) using existing Blender 5.0.1,
Godot 4.7.2, Python 3.11.9 and PowerShell 7. No paid job or model installation ran.

| Check | Result and evidence |
| --- | --- |
| Complete suite | PASS: `pwsh -NoProfile -File tools/test-providers.ps1`; terminal marker `PROVIDER_SUITE_PASS`. Full local log: `generated/reports/provider-suite-final.log`. |
| Provider tests | PASS: 22 tests covering capability selection, unavailable auth, request models, changed inputs, one-use approvals, ambiguous submit protection, provenance, cleanup, downloads, CLI dispatch and local HTTP. The complete suite first passed with 20; the expanded 22-test set was then run successfully. Paid transport is mocked. |
| Existing image tests | PASS: 3 tests covering graph parameter types/links and rejected requests. |
| Existing PowerShell tests | PASS: 9 checks including expected negative tests for draft/overwrite/exit-code/log errors. Expected `PIPELINE_FAIL` messages in this test's log are deliberate assertions. |
| Actual Blender fixture | PASS: generated transformed textured sphere through `create_fixture.py`; GLB source actually written. |
| PBR preservation | PASS: base-color, normal, packed metallic/roughness and emission slots survive; embedded PNG payload hashes match the source exactly. Images remain packed in editable Blender source. |
| Geometry cleanup | PASS: 528 visible triangles, identity hull transform, 3 m longest dimension, bottom origin, finite normalized normals, usable material references and UVs, box collision proxy. |
| LOD | PASS: separately exported/imported LOD has fewer triangles than the source. Runtime distance switching remains gameplay work. |
| Godot | PASS: real GLB import, material texture checks, geometry/UV/collision validation, resource loading, original scene regression and main runtime smoke test. |
| GPU previews | PASS: actual renders of `provider_cleanup_probe` and `test_fighter` captured and visually inspected. |
| Original fighter | PASS: new provider `asset-create` route regenerated Blender source/GLB and completed the original Godot test/preview pipeline; 22 meshes, 3,520 triangles, 6 materials. Main scene preserved. |
| CLI plans | PASS: Meshy hero, Higgsfield hero, ComfyUI concept and multi-view preparation executed without generation requests. Paid `create` returns awaiting approval; execute without receipt exits nonzero. |
| ComfyUI protocol | PASS against a loopback test HTTP server: health, graph POST, task history, PNG retrieval, hash and manifest integration. This does NOT test AI inference. |
| Live service configuration | Meshy key absent, Higgsfield CLI/login absent, ComfyUI health unavailable on 127.0.0.1:8188. Absence failures are handled. |

Fixes discovered by executing tests:

- Blender imports packed images lazily. The texture audit now forces decoding and
  preserves already-packed buffers; repacking them had removed image data from export.
- Godot originally accepted material objects even when their texture images were
  missing. Validation now checks named PBR materials and the required texture slots.
- Rebuilding a generated fixture can change GLB bytes. Explicit repair checks the
  recorded provider/source path, validates the new plan's input hash and archives
  previous outputs before rebuilding.
- Old example requests used `game-ready`; they now use the actual quality profiles.

Reproduce local acceptance with `tools/test-providers.ps1`. It rebuilds only its
named fixture and the original fighter. It leaves a normal generated-artifact Git
diff for review; it does not reset/clean files to hide changes. Reports and image
job bundles are ignored; the curated source/runtime fixture and manifests are committed.

Live Meshy/Higgsfield generation, actual ComfyUI CUDA inference, seamless-texture
production, coherent AI multi-view images, animation preservation, visual hero
quality and gameplay-specific LOD/collision behavior remain untested. These are
explicit future acceptance stages, not reported as PASS.
