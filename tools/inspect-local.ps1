param([string]$OutputDirectory = (Join-Path (Split-Path -Parent $PSScriptRoot) 'generated/reports/local-inventory'))
# Read-only inventory; never starts services, installs software, or downloads models.
$ErrorActionPreference = 'Stop'
New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$inventory = [ordered]@{utc=[DateTime]::UtcNow.ToString('o'); notes=@(); commands=@{}; hardware=@{}; python=@{}; models=@{}; software=@(); services=@{}}
foreach ($name in @('godot','blender','py','python','python3','nvidia-smi','nvcc','ollama')) {
    $command = Get-Command $name -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    $inventory.commands[$name] = if ($command) { $command.Source } else { $null }
}
try {
    $inventory.hardware['cpu'] = (Get-CimInstance Win32_Processor).Name
    $inventory.hardware['ram_bytes'] = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory
} catch { $inventory.notes += "CPU/RAM query unavailable: $($_.Exception.Message)" }
$inventory.hardware['disks'] = @(Get-PSDrive -PSProvider FileSystem | Where-Object Name -NE 'Temp' | Select-Object Name,Used,Free)
if ($inventory.commands['nvidia-smi']) {
    $inventory.hardware['nvidia'] = @(& $inventory.commands['nvidia-smi'] --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader)
}
if ($inventory.commands['py']) {
    $inventory.python['interpreters'] = @(& $inventory.commands['py'] -0p 2>&1 | ForEach-Object ToString)
    foreach ($version in @('3.11','3.14')) {
        $inventory.python[$version] = @(& $inventory.commands['py'] "-$version" -c 'import sys,importlib.util,json; print(json.dumps({"version":sys.version,"packages":{m:bool(importlib.util.find_spec(m)) for m in ["torch","diffusers","transformers","PIL","numpy"]}}))' 2>&1 | ForEach-Object ToString)
    }
}
foreach ($pair in @(@('ollama', '.ollama/models/manifests/registry.ollama.ai/library'), @('huggingface', '.cache/huggingface/hub'))) {
    $modelPath = Join-Path $env:USERPROFILE $pair[1]
    $inventory.models[$pair[0]] = @(Get-ChildItem -LiteralPath $modelPath -Directory -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Name)
}
$roots = @('C:\Tools', (Join-Path $env:USERPROFILE 'Coding projects'), (Join-Path $env:USERPROFILE 'Documents'), (Join-Path $env:USERPROFILE 'Downloads'), (Join-Path $env:LOCALAPPDATA 'Programs'), 'C:\Program Files\Allegorithmic', 'C:\Program Files\Autodesk')
$inventory.software = @(foreach ($path in $roots) {
    if (Test-Path -LiteralPath $path) {
        Get-ChildItem -LiteralPath $path -Directory -Depth 2 -ErrorAction SilentlyContinue |
            Where-Object Name -Match 'Comfy|Stable.?Diffusion|Fooocus|InvokeAI|SwarmUI|AUTOMATIC1111|Substance|Maya2026|Ollama' |
            Select-Object -ExpandProperty FullName
    }
})
foreach ($service in @(@('comfyui','http://127.0.0.1:8188/system_stats'), @('ollama','http://127.0.0.1:11434/api/tags'))) {
    try { $inventory.services[$service[0]] = Invoke-RestMethod -Uri $service[1] -TimeoutSec 3 }
    catch { $inventory.services[$service[0]] = "Not reachable: $($_.Exception.Message)" }
}
$inventory.notes += 'CUDA version reported by nvidia-smi describes driver support; it does not prove CUDA Toolkit or GPU-enabled PyTorch is installed.'
$inventory.notes += 'Tool discovery is bounded to common installation locations and selected caches, not an exhaustive search of every disk or virtual environment.'
$inventory | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'local-inventory.json')
Write-Host "Inventory saved: $OutputDirectory/local-inventory.json"
