@echo off
cd /d "%~dp0"
if not exist "generated\unreal\package\Windows\Cinder.exe" (
  echo Packaged build missing. Ask the agent to run the Unreal acceptance pipeline.
  exit /b 1
)
start "" "generated\unreal\package\Windows\Cinder.exe" -windowed -ResX=1920 -ResY=1080
