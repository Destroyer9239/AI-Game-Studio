param([ValidateSet('generate','validate','preview','benchmark','launch')][string]$Action='validate',[ValidateSet(2,4)][int]$Quality=2,[switch]$ReferenceBlock)
. "$PSScriptRoot/studio-common.ps1"
$script:RunDirectory=Get-StudioPath ('generated/reports/district-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $script:RunDirectory | Out-Null
$godot=Resolve-StudioTool godot
$game=Get-StudioPath 'game'
$py=(Get-Command py -CommandType Application | Select-Object -First 1).Source
if($Action -eq 'generate') {
 Invoke-StudioProcess 'district-compose' $py @('-3.11','tools/world/generate_district.py') 60 'DISTRICT_GENERATION_PASS'
}
Invoke-StudioProcess 'district-contract' $py @('-3.11','tools/world/test_district.py') 60 'OK'
Invoke-StudioProcess 'district-import' $godot @('--headless','--path',$game,'--editor','--import') 180
Invoke-StudioProcess 'district-runtime' $godot @('--headless','--path',$game,'--script','res://scripts/test_district.gd') 120 'DISTRICT_TEST_PASS'
if($Action -eq 'preview') {
 Invoke-StudioProcess 'district-preview' $godot @('--path',$game,'--script','res://scripts/review_district.gd') 120 'DISTRICT_REVIEW_PASS'
}
if($Action -eq 'benchmark') {
 $scene=if($ReferenceBlock){'res://scenes/playable_block.tscn'}else{'res://scenes/district_demo.tscn'}
 $label=if($ReferenceBlock){'reference'}else{'district'}
 Invoke-StudioProcess 'district-benchmark' $godot @('--path',$game,'--rendering-method','forward_plus',$scene,'--','--weather=rain','--hour=15',"--quality=$Quality",'--district-inspection','--benchmark',"--capture=$(Get-StudioPath "generated/previews/${label}_q$Quality.png")","--report=$script:RunDirectory/quality_$Quality.json") 120 'PLAYABLE_PREVIEW_PASS'
 $metrics=Get-Content "$script:RunDirectory/quality_$Quality.json" -Raw | ConvertFrom-Json
 if($metrics.chunks.loaded -ne 2){throw 'Benchmark requires both corridor cells loaded'}
}
if($Action -eq 'launch') {Start-Process -FilePath $godot -ArgumentList @('--path',$game,'res://scenes/district_demo.tscn') -WindowStyle Normal}
$script:StudioStages | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $script:RunDirectory 'stages.json')
Write-Host "DISTRICT_TOOL_PASS: $script:RunDirectory"
