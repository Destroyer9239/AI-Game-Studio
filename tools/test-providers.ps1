# Reproducible local acceptance suite. Never submits a paid provider request.
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/studio-common.ps1"
Push-Location $script:StudioRoot
try {
    $blender = Resolve-StudioTool 'blender' ''
    & $blender --background --factory-startup --python-exit-code 1 --python tools/providers/tests/create_fixture.py
    if ($LASTEXITCODE) { throw 'Texture fixture generation failed' }
    $planned = & py -3.11 tools/providers/cli.py plan --request tools/providers/requests/cleanup_probe.json
    if ($LASTEXITCODE) { throw 'Provider plan failed' }
    $job = ($planned | ConvertFrom-Json).job
    if (Test-Path -LiteralPath 'generated/manifests/provider_cleanup_probe.json') {
        & py -3.11 tools/providers/cli.py process --job $job --repair
    } else {
        & py -3.11 tools/providers/cli.py execute --job $job
    }
    if ($LASTEXITCODE) { throw 'Local cleanup/Godot pipeline failed' }
    & py -3.11 -m unittest discover -s tools/providers/tests -p 'test_*.py' -v
    if ($LASTEXITCODE) { throw 'Provider acceptance failed' }
    & py -3.11 -m unittest discover -s tools/imagegen -p test_workflow.py -v
    if ($LASTEXITCODE) { throw 'Image workflow regression failed' }
    & pwsh -NoProfile -File tools/test-automation.ps1
    if ($LASTEXITCODE) { throw 'PowerShell regression failed' }
    & pwsh -NoProfile -File tools/pipeline.ps1 asset-create -RequestFile tools/providers/requests/blender_fighter.json
    if ($LASTEXITCODE) { throw 'Original full Blender/Godot pipeline regression failed' }
    Write-Host 'PROVIDER_SUITE_PASS: local protocol, cleanup/PBR, Godot, preview, cost gates and original pipeline'
} finally {
    Pop-Location
}
