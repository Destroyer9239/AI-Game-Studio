# Existing accepted assets are validated, not regenerated. No provider submission.
param([switch]$SkipGpu)
. "$PSScriptRoot/studio-common.ps1"
$script:RunDirectory=Get-StudioPath ('generated/reports/world-regression-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $script:RunDirectory | Out-Null
$py=(Get-Command py -CommandType Application | Select-Object -First 1).Source
$blender=Resolve-StudioTool blender
Invoke-StudioProcess 'provider-unit' $py @('-3.11','-m','unittest','discover','-s','tools/providers/tests','-p','test_*.py','-v') 120 'OK'
Invoke-StudioProcess 'workflow-unit' $py @('-3.11','-m','unittest','discover','-s','tools/imagegen','-p','test_workflow.py','-v') 90 'OK'
Invoke-StudioProcess 'multiview-unit' $py @('-3.11','tools/world/test_multiview.py') 90 'OK'
Invoke-StudioProcess 'city-contract' $py @('-3.11','tools/world/test_city_contract.py') 90 'OK'
foreach($asset in @('fighter','worker')) {
 Invoke-StudioProcess "canonical-$asset" $py @('-3.11','tools/world/multiview_gate.py',"generated/references/canonical_$asset/package.json",'--review',"generated/references/canonical_$asset/visual_review.json") 90 'PASS'
}
Invoke-StudioProcess 'character-source' $blender @('--background','--factory-startup','--python-exit-code','1','--python','blender/scripts/validate_character.py','--','tools/world/worker_character.json') 90 'CHARACTER_SOURCE_PASS'
Invoke-StudioProcess 'building-recipe' $blender @('--background','--factory-startup','--python-exit-code','1','--python','blender/scripts/test_building_recipe.py') 180 'BUILDING_RECIPE_TESTS_PASS'
$config=Get-Content (Get-StudioPath 'tools/providers/image_generation/comfyui.json') -Raw | ConvertFrom-Json
Invoke-StudioProcess 'material-regression' (Join-Path $config.runtime 'python_embeded/python.exe') @('tools/imagegen/test_environment.py') 120 'OK'
foreach($entry in @('test-automation.ps1','pipeline.ps1')) {
 [string[]]$arguments=if($entry -eq 'pipeline.ps1'){@('validate')}else{@()}
 & pwsh -NoProfile -File "$PSScriptRoot/$entry" @arguments
 if($LASTEXITCODE -ne 0){throw "$entry failed"}
}
& pwsh -NoProfile -File "$PSScriptRoot/world.ps1" stress -Runs 5
if($LASTEXITCODE -ne 0){throw 'World stress failed'}
if(-not $SkipGpu) {
 & pwsh -NoProfile -File "$PSScriptRoot/world.ps1" benchmark -Weather rain
 if($LASTEXITCODE -ne 0){throw 'GPU benchmark failed'}
}
Invoke-StudioProcess 'artifact-audit' $py @('-3.11','tools/audit_git.py') 90 'PASS'
$script:StudioStages | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $script:RunDirectory 'stages.json')
Write-Host "WORLD_REGRESSION_PASS: $script:RunDirectory; GPU skipped=$SkipGpu; live inference not repeated"

