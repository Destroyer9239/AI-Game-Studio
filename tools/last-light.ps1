param([ValidateSet('validate','preview','benchmark','launch')][string]$Action='validate',[ValidateRange(0,4)][int]$Quality=2,[switch]$FourK,[ValidateSet('clear','rain')][string]$Weather='rain',[ValidateRange(0,24)][double]$Hour=17.5,[switch]$HideMenu)
. "$PSScriptRoot/studio-common.ps1"
$script:RunDirectory=Get-StudioPath ('generated/reports/last-light-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $script:RunDirectory | Out-Null
$godot=Resolve-StudioTool godot
$game=Get-StudioPath 'game'
Invoke-StudioProcess 'import' $godot @('--headless','--path',$game,'--editor','--import') 180
Invoke-StudioProcess 'mission-test' $godot @('--headless','--path',$game,'--script','res://scripts/test_last_light.gd') 120 'LAST_LIGHT_TEST_PASS'
if($Action -in @('preview','benchmark')) {
 $resolution=if($FourK){'3840x2160'}else{'1920x1080'}
 $arguments=@('--path',$game,'--resolution',$resolution,'res://scenes/last_light.tscn','--',"--quality=$Quality","--hour=$($Hour.ToString([cultureinfo]::InvariantCulture))","--weather=$Weather",'--district-inspection',"--capture=$(Get-StudioPath "generated/previews/last_light_${resolution}_q$Quality.png")","--report=$script:RunDirectory/metrics.json")
 if($Action -eq 'benchmark'){$arguments+=@('--benchmark','--mission-preview')}
 elseif($HideMenu){$arguments+='--mission-preview'}
 Invoke-StudioProcess 'gpu' $godot $arguments 120 'PLAYABLE_PREVIEW_PASS'
 $metrics=Get-Content "$script:RunDirectory/metrics.json" -Raw | ConvertFrom-Json
 if($FourK -and ($metrics.viewport_size[0] -ne 3840 -or $metrics.viewport_size[1] -ne 2160)){throw 'Capture did not render at native 3840x2160'}
 if($FourK -and ($metrics.capture_size[0] -ne 3840 -or $metrics.capture_size[1] -ne 2160)){throw 'Saved image is not exact 3840x2160'}
}
if($Action -eq 'launch'){Start-Process -FilePath $godot -ArgumentList @('--path',$game,'res://scenes/last_light.tscn') -WindowStyle Normal}
$script:StudioStages | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $script:RunDirectory 'stages.json')
Write-Host "LAST_LIGHT_TOOL_PASS: $script:RunDirectory"
