# Powered by Poly Haven — downloads CC0 assets; no runtime network dependency.
$ErrorActionPreference='Stop'
. "$PSScriptRoot/studio-common.ps1"
$headers=@{'User-Agent'='AI-Game-Studio/1.0 (local development asset acquisition)'}
$total=0
foreach($id in @('asphalt_02','brushed_concrete')) {
 $catalog=Invoke-RestMethod -Uri "https://api.polyhaven.com/files/$id" -Headers $headers
 $folder=Get-StudioPath "game/assets/textures/polyhaven/$id"
 New-Item -ItemType Directory -Force $folder | Out-Null
 $records=@()
 foreach($pair in @(@('Diffuse','basecolor'),@('nor_gl','normal'),@('Rough','roughness'))) {
  $entry=$catalog.($pair[0]).'2k'.png
  if(-not $entry -or $entry.url -notlike 'https://dl.polyhaven.org/*'){throw 'Unexpected asset metadata'}
  $total+=[long]$entry.size
  if($total -gt 150000000){throw '150 MB acquisition budget exceeded'}
  $target=Join-Path $folder ($pair[1]+'.png')
  if(-not (Test-Path $target)){Invoke-WebRequest -Uri $entry.url -Headers $headers -OutFile ($target+'.partial'); Move-Item -LiteralPath ($target+'.partial') -Destination $target}
  if((Get-Item $target).Length -ne $entry.size -or (Get-FileHash $target -Algorithm MD5).Hash.ToLowerInvariant() -ne $entry.md5){throw "Asset verification failed: $id/$($pair[1])"}
  $records+=@{role=$pair[1];url=$entry.url;bytes=$entry.size;sha256=(Get-FileHash $target -Algorithm SHA256).Hash.ToLowerInvariant()}
 }
 @{asset=$id;source="https://polyhaven.com/a/$id";license='CC0';license_url='https://polyhaven.com/license';resolution=2048;credit='Powered by Poly Haven';maps=$records} | ConvertTo-Json -Depth 6 | Set-Content (Join-Path $folder 'provenance.json')
}
Write-Host "PBR_FETCH_PASS: verified six maps; $total bytes"
