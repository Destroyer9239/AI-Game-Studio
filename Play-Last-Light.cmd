@echo off
cd /d "%~dp0"
powershell -NoProfile -File tools/last-light.ps1 launch
