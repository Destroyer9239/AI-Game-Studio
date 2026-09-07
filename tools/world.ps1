param([ValidateSet('validate','preview','launch','test-gameplay','stress','preview-playable','benchmark')][string]$Action='validate',[ValidateSet('clear','rain','heavy_rain','fog','cloudy','storm')][string]$Weather='clear',[ValidateRange(0,4)][int]$Quality=2,[ValidateRange(1,20)][int]$Runs=5,[ValidateRange(0,24)][float]$Hour=16)
. "$PSScriptRoot/studio-common.ps1"
$script:RunDirectory=Get-StudioPath ('generated/reports/world-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $script:RunDirectory | Out-Null
$godot=Resolve-StudioTool godot
$game=Get-StudioPath 'game'
Invoke-StudioProcess 'world-import' $godot @('--headless','--path',$game,'--editor','--import') 180
Invoke-StudioProcess 'world-resources' $godot @('--headless','--path',$game,'--script','res://scripts/validate_resources.gd') 90 'PIPELINE_RESOURCES_PASS'
Invoke-StudioProcess 'streaming-tests' $godot @('--headless','--path',$game,'--script','res://scripts/test_streaming.gd') 120 'STREAMING_TESTS_PASS'
Invoke-StudioProcess 'environment-state-tests' $godot @('--headless','--path',$game,'--script','res://scripts/test_environment_state.gd') 90 'ENVIRONMENT_STATE_TESTS_PASS'
if($Action -in @('test-gameplay','preview-playable','stress','benchmark')) {
 Invoke-StudioProcess 'gameplay-tests' $godot @('--headless','--path',$game,'--script','res://scripts/test_gameplay.gd') 120 'GAMEPLAY_TESTS_PASS'
}
if($Action -eq 'stress') {
 foreach($iteration in 1..$Runs) { Invoke-StudioProcess "streaming-stress-$iteration" $godot @('--headless','--path',$game,'--script','res://scripts/test_streaming_stress.gd') 180 'STREAMING_STRESS_PASS' }
}
if($Action -eq 'benchmark') {
 foreach($preset in 0..4) {
 Invoke-StudioProcess "playable-quality-$preset" $godot @('--path',$game,'--rendering-method','forward_plus','res://scenes/playable_block.tscn','--',"--weather=$Weather","--hour=$Hour","--quality=$preset","--inspection","--benchmark","--capture=$(Get-StudioPath "generated/previews/playable_${Weather}_q$preset.png")","--report=$script:RunDirectory/quality_$preset.json") 120 'PLAYABLE_PREVIEW_PASS'
 }
}
if($Action -eq 'preview-playable') {
 Invoke-StudioProcess 'playable-preview' $godot @('--path',$game,'--rendering-method','forward_plus','res://scenes/playable_block.tscn','--',"--weather=$Weather","--hour=$Hour","--quality=$Quality","--inspection","--capture=$(Get-StudioPath "generated/previews/playable_$Weather.png")","--report=$script:RunDirectory/playable_metrics.json") 120 'PLAYABLE_PREVIEW_PASS'
}
if($Action -eq 'preview') {
 Invoke-StudioProcess 'city-preview' $godot @('--path',$game,'--rendering-method','forward_plus','res://scenes/city_block_demo.tscn','--',"--weather=$Weather","--capture=$(Get-StudioPath "generated/previews/city_block_$Weather.png")") 120 'CITY_PREVIEW_PASS'
} elseif($Action -eq 'launch') {
 Start-Process -FilePath $godot -ArgumentList @('--path',$game,'res://scenes/playable_block.tscn') -WindowStyle Normal
}
Write-Host "WORLD_TOOL_PASS: $script:RunDirectory"
$script:StudioStages | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $script:RunDirectory 'stages.json')
