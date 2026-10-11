@echo off
cd /d "%~dp0"
powershell -NoProfile -File tools/unreal.ps1 launch
