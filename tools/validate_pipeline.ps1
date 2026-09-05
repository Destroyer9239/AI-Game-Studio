param(
    [string]$GodotPath,
    [switch]$Capture
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$gamePath = Join-Path $projectRoot 'game'
$logPath = Join-Path $projectRoot 'generated/pipeline-test'
New-Item -ItemType Directory -Force -Path $logPath | Out-Null
if (-not $GodotPath) {
    $godotCommand = Get-Command godot -ErrorAction SilentlyContinue
    if ($godotCommand) {
        $GodotPath = $godotCommand.Source
    } else {
        $GodotPath = Join-Path $env:USERPROFILE 'Downloads/Godot_v4.7.2-stable_win64.exe/Godot_v4.7.2-stable_win64_console.exe'
    }
}
if (-not (Test-Path -LiteralPath $GodotPath)) {
    throw 'Godot not found. Supply -GodotPath with the path to its executable.'
}

function Invoke-GodotCheck([string]$Name, [string[]]$Arguments) {
    $outputPath = Join-Path $logPath ($Name + '.log')
    & $GodotPath --log-file $outputPath @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$Name exited with code $LASTEXITCODE" }
    $log = Get-Content -Raw -LiteralPath $outputPath
    if ($log -match '(?im)(SCRIPT ERROR:|ERROR:|Parse Error|Failed to load)') {
        throw "$Name reported an error. See $outputPath"
    }
    Write-Host "PASS: $Name"
}

Invoke-GodotCheck 'godot-import' @('--headless', '--path', $gamePath, '--editor', '--import')
Invoke-GodotCheck 'godot-scene-validation' @('--headless', '--path', $gamePath, '--script', 'res://scripts/validate_pipeline.gd')
Invoke-GodotCheck 'godot-runtime' @('--headless', '--path', $gamePath, '--quit-after', '120', '--fixed-fps', '60')
if ($Capture) {
    $screenshot = Join-Path $logPath 'fighter-preview.png'
    Invoke-GodotCheck 'godot-render' @('--path', $gamePath, '--fixed-fps', '60', '--quit-after', '300', '--', "--capture=$screenshot")
    if (-not (Test-Path -LiteralPath $screenshot)) { throw 'Renderer did not produce a screenshot.' }
}
Write-Host 'PIPELINE_VALIDATION_PASS'
