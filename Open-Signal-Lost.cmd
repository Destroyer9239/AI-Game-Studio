@echo off
cd /d "%~dp0"
powershell -NoProfile -Command ". ./tools/studio-common.ps1; & (Get-StudioShell) -NoProfile -File tools/unreal.ps1 launch -Game signal-lost"
