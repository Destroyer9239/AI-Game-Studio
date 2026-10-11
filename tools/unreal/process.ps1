# UE logs optional profiling DLL absence as Failed to load. Keep that precise
# exception local to UE; do not weaken Godot's existing strict process validator.
function Invoke-UnrealProcess([string]$Executable,[string[]]$Arguments,[string]$Marker,[int]$Timeout=1200){
 $start=[Diagnostics.ProcessStartInfo]::new()
 $start.FileName=$Executable;$start.WorkingDirectory=$script:StudioRoot
 $start.UseShellExecute=$false;$start.CreateNoWindow=$true
 $start.RedirectStandardOutput=$true;$start.RedirectStandardError=$true
 Set-StudioProcessArguments $start $Arguments
 $process=[Diagnostics.Process]::new();$process.StartInfo=$start
 $timer=[Diagnostics.Stopwatch]::StartNew();$status='FAIL';$code=-1
 $path=Join-Path $script:RunDirectory 'process.log'
 try{
  $null=$process.Start();$stdout=$process.StandardOutput.ReadToEndAsync();$stderr=$process.StandardError.ReadToEndAsync()
  if(-not $process.WaitForExit($Timeout*1000)){
   $process.Kill($true);$process.WaitForExit()
   [IO.File]::WriteAllText($path,$stdout.GetAwaiter().GetResult()+"`n"+$stderr.GetAwaiter().GetResult())
   throw "Owned Unreal process timed out. Inspect $path"
  }
  $code=$process.ExitCode
  $log=$stdout.GetAwaiter().GetResult()+"`n"+$stderr.GetAwaiter().GetResult()
  [IO.File]::WriteAllText($path,$log)
  $scan=$log -replace "(?im)^.*LogWindows: Failed to load '(aqProf|VtuneApi|VtuneApi32e|WinPixGpuCapturer|Wintab32)\.dll'.*$",''
  $scan=$scan -replace '(?im)^.*LogAudio: Display: No default SoundConcurrencyObject specified \(or failed to load\)\..*$',''
  if($code -ne 0 -or $scan -match '(?im)(: Error:|Fatal error:|Traceback \(most recent call last\)|Failed to load)' -or -not $log.Contains($Marker)){throw "Unreal failed (exit $code). Inspect $path"}
  $status='PASS';Write-Host "UNREAL_PROCESS_PASS: $path"
 }finally{
  $script:StudioStages.Add(@{name='unreal';status=$status;exit_code=$code;seconds=$timer.Elapsed.TotalSeconds;log=$path})
  $script:StudioStages | ConvertTo-Json -Depth 8 | Set-Content "$script:RunDirectory/stages.json"
  $process.Dispose()
 }
}
