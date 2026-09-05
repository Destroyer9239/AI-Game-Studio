# Small regression checks for the automation's failure handling and templates.
. "$PSScriptRoot/studio-common.ps1"
$script:RunDirectory = Get-StudioPath ('generated/reports/automation-tests-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $script:RunDirectory | Out-Null
$pwsh = (Get-Process -Id $PID).Path
$count = 0
function Expect-Failure([scriptblock]$Work, [string]$Expected) {
    $message = ''
    try { & $Work } catch { $message = $_.Exception.Message }
    if (-not $message.Contains($Expected)) { throw "Expected failure containing '$Expected', got '$message'" }
    $script:count++
}
Expect-Failure { Get-StudioPath '../escape' } 'escapes the project'
Expect-Failure { Read-StudioAsset '../escape' } 'Asset ID'
Expect-Failure { Resolve-StudioTool godot (Join-Path $script:RunDirectory 'missing.exe') } 'Executable not found'
$fake = Join-Path $script:RunDirectory 'fake-error.ps1'
Set-Content -LiteralPath $fake -Value 'Write-Output "ERROR: simulated zero-exit failure"; exit 0'
Expect-Failure { Invoke-StudioProcess 'zero-exit-error' $pwsh @('-NoProfile','-File',$fake) } 'failed (exit 0)'
Set-Content -LiteralPath $fake -Value 'Write-Output "no completion marker"; exit 0'
Expect-Failure { Invoke-StudioProcess 'missing-marker' $pwsh @('-NoProfile','-File',$fake) 10 'EXPECTED_PASS' } 'did not report'
Set-Content -LiteralPath $fake -Value 'Write-Output "intentional nonzero"; exit 7'
Expect-Failure { Invoke-StudioProcess 'nonzero' $pwsh @('-NoProfile','-File',$fake) } 'failed (exit 7)'

# Test scaffolding in an isolated miniature workspace, leaving real assets alone.
$fixture = Join-Path $script:RunDirectory 'fixture'
foreach ($relative in @('tools/pipeline.ps1','tools/studio-common.ps1','tools/templates/asset.json.template','tools/templates/asset-spec.md.template','blender/scripts/templates/generate_asset.py.template')) {
    $target = Join-Path $fixture $relative
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $target) | Out-Null
    Copy-Item -LiteralPath (Get-StudioPath $relative) -Destination $target
}
$entry = Join-Path $fixture 'tools/pipeline.ps1'
& $pwsh -NoProfile -File $entry scaffold -Asset automation_fixture
if ($LASTEXITCODE -ne 0) { throw 'Scaffold failed' }
$manifest = Get-Content -Raw -LiteralPath (Join-Path $fixture 'tools/assets/automation_fixture.json') | ConvertFrom-Json
if ($manifest.status -ne 'draft' -or $manifest.generator -ne 'blender/scripts/generate_automation_fixture.py') { throw 'Invalid scaffold' }
$count++
& $pwsh -NoProfile -File $entry scaffold -Asset automation_fixture
if ($LASTEXITCODE -eq 0) { throw 'Scaffold overwrote an existing asset' }
$count++
& $pwsh -NoProfile -File $entry generate -Asset automation_fixture
if ($LASTEXITCODE -eq 0) { throw 'Draft asset was allowed to generate' }
$count++
Write-Host "AUTOMATION_TESTS_PASS: $count checks. Fixture and expected-failure logs: $script:RunDirectory"
exit 0
