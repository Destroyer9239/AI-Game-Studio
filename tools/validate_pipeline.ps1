# Backward-compatible entry point. New automation lives in pipeline.ps1.
param([string]$GodotPath, [switch]$Capture)
& "$PSScriptRoot/pipeline.ps1" validate -GodotPath $GodotPath -Capture:$Capture
