param([ValidateSet('doctor','setup','export','build','validate','test','preview','launch','play','package')][string]$Action='doctor',[string]$EngineRoot=$env:UE_ENGINE_ROOT)
. "$PSScriptRoot/studio-common.ps1"
. "$PSScriptRoot/unreal/process.ps1"
if(-not $EngineRoot){$EngineRoot='C:\Program Files\Epic Games\UE_5.7'}
$editor=Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
if(-not(Test-Path $editor)){throw "UE 5.7 editor missing: $editor. Set UE_ENGINE_ROOT."}
$version=Get-Content (Join-Path $EngineRoot 'Engine/Build/Build.version') -Raw | ConvertFrom-Json
if($version.MajorVersion -ne 5 -or $version.MinorVersion -ne 7){throw 'Pipeline pinned to UE 5.7; validate upgrades separately.'}
$project=Get-StudioPath 'unreal/Cinder/Cinder.uproject'
$projectDir=Split-Path $project
$script:RunDirectory=Get-StudioPath ('generated/reports/unreal-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Force $script:RunDirectory | Out-Null
$env:CINDER_REPORT_DIR=$script:RunDirectory
$env:CINDER_ACTION=$Action
if($Action -eq 'doctor'){
 $vswhere='C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe'
 $inventory=@{engine=$EngineRoot;version=$version;editor_exists=(Test-Path $editor);vswhere_exists=(Test-Path $vswhere);free_bytes=(Get-PSDrive C).Free;ram_bytes=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory}
 $inventory | ConvertTo-Json -Depth 5 | Set-Content "$script:RunDirectory/doctor.json"
 $inventory | ConvertTo-Json -Depth 5
}
if($Action -in @('setup','build')){
 # Copy only missing installed Epic template files. Never overwrite authored assets.
 $template=Join-Path $EngineRoot 'Templates/TP_FirstPersonBP'
 $copies=@(@{source="$template/Content";target="$projectDir/Content"})
 foreach($pack in @('Characters','Input','LevelPrototyping')){$copies+=@{source=(Join-Path $EngineRoot "Templates/TemplateResources/High/$pack/Content");target="$projectDir/Content/$pack"}}
 foreach($copy in $copies){
  if(-not(Test-Path $copy.source)){throw "Missing installed template pack: $($copy.source)"}
  foreach($file in Get-ChildItem $copy.source -Recurse -File){
   $relative=$file.FullName.Substring($copy.source.Length).TrimStart('\','/')
   $destination=Join-Path $copy.target $relative
   if(-not(Test-Path $destination)){New-Item -ItemType Directory -Force (Split-Path $destination) | Out-Null;Copy-Item -LiteralPath $file.FullName -Destination $destination}
  }
 }
 if(-not(Test-Path "$projectDir/Config/DefaultInput.ini")){Copy-Item "$template/Config/DefaultInput.ini" "$projectDir/Config/DefaultInput.ini"}
}
if($Action -in @('export','build')){
 Invoke-StudioProcess 'blender-export' (Resolve-StudioTool blender) @('--background','--factory-startup','--python-exit-code','1','--python',(Get-StudioPath 'tools/unreal/export_static.py')) 240 'UNREAL_EXPORT_PASS'
}
if($Action -in @('build','validate','test','preview')){
 $scriptFile=Get-StudioPath 'tools/unreal/editor_pipeline.py'
 $arguments=@($project,'/Engine/Maps/Entry','-unattended','-nop4','-nosplash','-stdout','-FullStdOutLogOutput',"-abslog=$script:RunDirectory/editor.log")
 # Level creation in this installed build crashes with NullRHI. Use the actual
 # renderer offscreen for editor subsystems and GPU-backed asset preparation.
 $arguments+=@('-RenderOffscreen',"-ExecutePythonScript=$scriptFile")
 Invoke-UnrealProcess $editor $arguments 'CINDER_UNREAL_PASS'
 if(-not(Test-Path "$script:RunDirectory/result.json")){throw 'Missing Unreal validation artifact'}
 $result=Get-Content "$script:RunDirectory/result.json" -Raw | ConvertFrom-Json
 if($result.status -ne 'PASS'){throw 'Unreal validation failed'}
}
if($Action -in @('launch','play')){
 $arguments=@($project)
 if($Action -eq 'play'){$arguments+=@('-game','-windowed','-ResX=1920','-ResY=1080')}
 Start-Process -FilePath (Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe') -ArgumentList (@($arguments | ForEach-Object {Format-StudioArgument $_}) -join ' ') -WindowStyle Normal
}
if($Action -eq 'package'){
 Invoke-UnrealProcess (Get-StudioShell) @('-NoProfile','-File',(Get-StudioPath 'tools/unreal/package.ps1'),'-EngineRoot',$EngineRoot,'-Project',$project,'-Output',(Get-StudioPath 'generated/unreal/package')) 'BUILD SUCCESSFUL' 1800
}
$script:StudioStages | ConvertTo-Json -Depth 8 | Set-Content "$script:RunDirectory/stages.json"
Write-Host "UNREAL_TOOL_PASS: $script:RunDirectory"
