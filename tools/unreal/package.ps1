param([string]$EngineRoot,[string]$Project,[string]$Output)
$ErrorActionPreference='Stop'
# No -UpdateIfNeeded / installer flags: missing toolchains must fail visibly.
& (Join-Path $EngineRoot 'Engine/Build/BatchFiles/RunUAT.bat') BuildCookRun "-project=$Project" "-unrealexe=$(Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe')" -noP4 -installed -nocompileeditor -platform=Win64 -clientconfig=Development -build -cook -stage -pak -archive "-archivedirectory=$Output" -utf8output
exit $LASTEXITCODE
