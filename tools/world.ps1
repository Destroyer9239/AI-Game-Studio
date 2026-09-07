param([ValidateSet('validate','preview','launch')][string]$Action='validate')
. "$PSScriptRoot/studio-common.ps1"
$script:RunDirectory=Get-StudioPath ('generated/reports/world-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $script:RunDirectory | Out-Null
$godot=Resolve-StudioTool godot
$game=Get-StudioPath 'game'
Invoke-StudioProcess 'world-import' $godot @('--headless','--path',$game,'--editor','--import') 180
Invoke-StudioProcess 'world-resources' $godot @('--headless','--path',$game,'--script','res://scripts/validate_resources.gd') 90 'PIPELINE_RESOURCES_PASS'
Invoke-StudioProcess 'streaming-tests' $godot @('--headless','--path',$game,'--script','res://scripts/test_streaming.gd') 120 'STREAMING_TESTS_PASS'
if($Action -eq 'preview') {
 Invoke-StudioProcess 'city-preview' $godot @('--path',$game,'--rendering-method','forward_plus','res://scenes/city_block_demo.tscn','--',"--capture=$(Get-StudioPath 'generated/previews/city_block.png')") 120 'CITY_PREVIEW_PASS'
} elseif($Action -eq 'launch') {
 Start-Process -FilePath $godot -ArgumentList @('--path',$game,'res://scenes/city_block_demo.tscn') -WindowStyle Normal
}
Write-Host "WORLD_TOOL_PASS: $script:RunDirectory"
