@echo off
cd /d "%~dp0"
py -3 -m pip install -r requirements.txt pyinstaller
if errorlevel 1 pause & exit /b 1
py -3 -m PyInstaller --noconfirm --onefile --windowed --name MerbeinCAD app.py
if errorlevel 1 pause & exit /b 1
echo EXE created at dist\MerbeinCAD.exe
pause
