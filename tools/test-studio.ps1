# Full local acceptance. Real GPU inference and rendering; never paid generation.
param([switch]$SkipInference)
$ErrorActionPreference='Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
function Check-Exit([string]$Step) { if($LASTEXITCODE -ne 0){ throw "$Step failed" } }
if (-not $SkipInference) {
 & py -3.11 tools/imagegen/test_local_backend.py
 Check-Exit 'Local backend acceptance'
}
& (Get-StudioShell) -NoProfile -File tools/environment.ps1 build
Check-Exit 'Environment vertical slice'
& (Get-StudioShell) -NoProfile -File tools/test-providers.ps1
Check-Exit 'Provider suite'
$config=Get-Content tools/providers/image_generation/comfyui.json -Raw | ConvertFrom-Json
& (Join-Path $config.runtime 'python_embeded/python.exe') tools/imagegen/test_environment.py
Check-Exit 'Material regression'
foreach($quality in @('LOW','MEDIUM','HIGH','ULTRA','CINEMATIC')) {
 & (Get-StudioShell) -NoProfile -File tools/environment.ps1 benchmark -Quality $quality
 Check-Exit "Benchmark $quality"
}
& py -3.11 tools/audit_git.py
Check-Exit 'Git credential/artifact audit'
Write-Host 'STUDIO_ACCEPTANCE_PASS: 23 provider tests, 3 workflow tests, 9 automation checks, 9 material/lifecycle tests, five GPU profiles; live inference included unless explicitly skipped.'
