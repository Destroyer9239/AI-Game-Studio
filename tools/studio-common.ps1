# Shared helpers. Run entry points with PowerShell 7 (pwsh).
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$script:StudioRoot = Split-Path -Parent $PSScriptRoot
$script:StudioStages = [System.Collections.Generic.List[object]]::new()

function Resolve-StudioTool([string]$Name, [string]$Override) {
    if ($Override) {
        if (-not (Test-Path -LiteralPath $Override -PathType Leaf)) { throw "Executable not found: $Override" }
        return (Resolve-Path -LiteralPath $Override).Path
    }
    $found = Get-Command $Name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { return $found.Source }
    $fallback = switch ($Name) {
        'godot' { 'C:\Tools\Godot\godot.exe' }
        'blender' { 'C:\Program Files\Blender Foundation\Blender 5.0\blender.exe' }
        default { throw "No fallback for $Name" }
    }
    if (-not (Test-Path -LiteralPath $fallback -PathType Leaf)) { throw "$Name not found on PATH or at $fallback. Supply an executable override." }
    return $fallback
}

function Get-StudioPath([string]$Relative) {
    if ([IO.Path]::IsPathRooted($Relative)) { throw "Expected a project-relative path: $Relative" }
    $absolute = [IO.Path]::GetFullPath((Join-Path $script:StudioRoot $Relative))
    if (-not $absolute.StartsWith($script:StudioRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes the project: $Relative"
    }
    $ancestor = $absolute
    while ($ancestor -and $ancestor -ne $script:StudioRoot) {
        if (Test-Path -LiteralPath $ancestor) {
            if ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Pipeline paths must not traverse reparse points: $ancestor"
            }
        }
        $ancestor = Split-Path -Parent $ancestor
    }
    return $absolute
}

function Read-StudioAsset([string]$Id) {
    if ($Id -notmatch '^[a-z][a-z0-9_]{0,63}$') { throw 'Asset ID must use lowercase letters, digits and underscores, starting with a letter.' }
    $file = Get-StudioPath "tools/assets/$Id.json"
    $asset = Get-Content -Raw -LiteralPath $file | ConvertFrom-Json
    if ($asset.schema_version -ne 1 -or $asset.id -ne $Id) { throw "Invalid manifest: $file" }
    if ($asset.status -ne 'ready') { throw "Asset $Id is a draft. Complete its design/generator and set status to ready first." }
    $expected = @{
        generator = "blender/scripts/generate_$Id.py"
        blend = "blender/projects/$Id.blend"
        model = "game/assets/models/$Id.glb"
        scene = "game/scenes/assets/$Id.tscn"
        specification = "docs/assets/$Id.md"
    }
    foreach ($field in $expected.Keys) {
        if ($asset.$field -ne $expected[$field]) { throw "Manifest $field must be $($expected[$field])" }
        $null = Get-StudioPath $asset.$field
    }
    if ($asset.max_triangles -lt 1 -or $asset.max_materials -lt 1) { throw 'Asset budgets must be positive.' }
    if ($asset.uv_mode -notin @('none', 'required', 'smart')) { throw 'uv_mode must be none, required or smart.' }
    if (-not (Test-Path -LiteralPath (Get-StudioPath $asset.specification))) { throw 'Missing design specification.' }
    return $asset
}

function Invoke-StudioProcess([string]$Name, [string]$Executable, [string[]]$Arguments, [int]$TimeoutSeconds = 180, [string]$PassMarker = '') {
    $logFile = Join-Path $script:RunDirectory ($Name + '.log')
    $start = [Diagnostics.ProcessStartInfo]::new()
    $start.FileName = $Executable
    $start.WorkingDirectory = $script:StudioRoot
    $start.UseShellExecute = $false
    $start.CreateNoWindow = $true
    $start.RedirectStandardOutput = $true
    $start.RedirectStandardError = $true
    foreach ($argument in $Arguments) { $start.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $start
    $timer = [Diagnostics.Stopwatch]::StartNew()
    $exitCode = -1
    $result = 'FAIL'
    try {
        Write-Host "Running $Name..."
        $null = $process.Start()
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit($TimeoutSeconds * 1000)) {
            $process.Kill($true)
            $process.WaitForExit()
            [IO.File]::WriteAllText($logFile, $stdout.GetAwaiter().GetResult() + "`n" + $stderr.GetAwaiter().GetResult())
            throw "$Name exceeded its $TimeoutSeconds second timeout. Only this process tree was stopped."
        }
        $exitCode = $process.ExitCode
        $log = $stdout.GetAwaiter().GetResult() + "`n" + $stderr.GetAwaiter().GetResult()
        [IO.File]::WriteAllText($logFile, $log)
        if ($exitCode -ne 0 -or $log -match '(?im)(SCRIPT ERROR:|ERROR:|Parse Error|Traceback \(most recent call last\)|Failed to load)') {
            throw "$Name failed (exit $exitCode). See $logFile`n$log"
        }
        if ($PassMarker -and -not $log.Contains($PassMarker)) { throw "$Name did not report $PassMarker. See $logFile" }
        $result = 'PASS'
        Write-Host "PASS: $Name"
    } finally {
        $script:StudioStages.Add([ordered]@{name=$Name; status=$result; exit_code=$exitCode; seconds=[math]::Round($timer.Elapsed.TotalSeconds, 2); log=$logFile; executable=$Executable; arguments=$Arguments})
        $process.Dispose()
    }
}
