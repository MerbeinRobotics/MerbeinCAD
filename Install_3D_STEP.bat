@echo off
cd /d "%~dp0"
echo MerbeinCAD v0.7 - Enable STEP solid export (CadQuery)
echo This uses a compatible 64-bit Python environment and requires internet access.
set "PYTHON_BIN="
if exist "%~dp0python_path.txt" set /p PYTHON_BIN=<"%~dp0python_path.txt"
if defined PYTHON_BIN if exist "%PYTHON_BIN%" goto install
where py >nul 2>nul
if not errorlevel 1 (set "PYTHON_BIN=py -3" & goto install)
where python >nul 2>nul
if not errorlevel 1 (set "PYTHON_BIN=python" & goto install)
echo Python not found. Install MerbeinCAD first.
pause
exit /b 1
:install
%PYTHON_BIN% -m pip install "cadquery>=2.5,<3"
if errorlevel 1 (echo STEP setup failed. See output above.) else (echo STEP support installed.)
pause
