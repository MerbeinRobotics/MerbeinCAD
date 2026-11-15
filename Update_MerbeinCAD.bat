@echo off
cd /d "%~dp0"
echo MerbeinCAD v0.4 update installer
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install_Update.ps1"
if errorlevel 1 (echo FAILED: inspect the message above) else (echo Installation completed. Start C:\MerbeinCAD\Application\launch_windows.bat)
pause
