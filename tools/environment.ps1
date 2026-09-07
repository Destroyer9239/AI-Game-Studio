param(
 [ValidateSet('material','build','validate','benchmark','launch')][string]$Action='validate',
 [ValidateSet('LOW','MEDIUM','HIGH','ULTRA','CINEMATIC')][string]$Quality='HIGH',
 [ValidateRange(0,20000)][int]$Instances=100
)
. "$PSScriptRoot/studio-common.ps1"
$script:RunDirectory = Get-StudioPath ('generated/reports/environment-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $script:RunDirectory | Out-Null
$config = Get-Content (Get-StudioPath 'tools/providers/image_generation/comfyui.json') -Raw | ConvertFrom-Json
$python = Join-Path $config.runtime 'python_embeded/python.exe'
if ($Action -in @('material','build')) {
 $manifest = Get-Content (Get-StudioPath 'generated/manifests/industrial_concrete_4k.json') -Raw | ConvertFrom-Json
 Invoke-StudioProcess 'material' $python @((Get-StudioPath 'tools/imagegen/material_factory.py'),'--source',$manifest.original_file) 180 'MATERIAL_FACTORY_PASS'
}
if ($Action -eq 'build') {
 & (Get-StudioShell) -NoProfile -File "$PSScriptRoot/pipeline.ps1" test-pipeline -Asset environment_probe
 if ($LASTEXITCODE -ne 0) { throw 'Environment asset pipeline failed' }
}
if ($Action -eq 'validate') {
 Invoke-StudioProcess 'material-validation' $python @((Get-StudioPath 'tools/imagegen/material_factory.py'),'--validate') 90 'MATERIAL_VALIDATION_PASS'
 & (Get-StudioShell) -NoProfile -File "$PSScriptRoot/pipeline.ps1" validate
 if ($LASTEXITCODE -ne 0) { throw 'Godot validation failed' }
}
if ($Action -in @('benchmark','launch','build')) {
 $godot = Resolve-StudioTool godot
 Invoke-StudioProcess 'lab-import' $godot @('--headless','--path',(Get-StudioPath 'game'),'--editor','--import') 180
 Invoke-StudioProcess 'lab-contract' $godot @('--headless','--path',(Get-StudioPath 'game'),'--script','res://scripts/validate_environment.gd') 90 'ENVIRONMENT_CONTRACT_PASS'
 $arguments = @('--path',(Get-StudioPath 'game'),'--rendering-method','forward_plus','res://scenes/environment_lab.tscn')
 if ($Action -ne 'launch') {
  $preview = Get-StudioPath "generated/previews/environment_$Quality.png"
  $arguments += @('--disable-vsync','--',"--quality=$Quality","--instances=$Instances","--capture=$preview","--report=$script:RunDirectory/benchmark.json")
  Invoke-StudioProcess 'lab-benchmark' $godot $arguments 240 'ENVIRONMENT_LAB_PASS'
  Get-Content "$script:RunDirectory/benchmark.json"
 } else {
  Start-Process -FilePath $godot -ArgumentList $arguments -WindowStyle Normal
 }
}
Write-Host "ENVIRONMENT_TOOL_PASS: $script:RunDirectory"
