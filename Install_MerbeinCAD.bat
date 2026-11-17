@echo off
cd /d "%~dp0"
echo MerbeinCAD v0.7 - First Time Windows Installer
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install_MerbeinCAD.ps1"
if errorlevel 1 (echo Installation did not complete. See the message above.) else (echo Installation complete. Launch MerbeinCAD from your desktop shortcut.)
pause
