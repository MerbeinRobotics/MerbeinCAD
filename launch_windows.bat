@echo off
cd /d "%~dp0"
set "PYTHON_BIN="
if exist "%~dp0python_path.txt" set /p PYTHON_BIN=<"%~dp0python_path.txt"
if defined PYTHON_BIN if exist "%PYTHON_BIN%" goto run
where py >nul 2>nul
if not errorlevel 1 (
  py -3 app.py
  goto done
)
where python >nul 2>nul
if not errorlevel 1 (
  python app.py
  goto done
)
echo Python could not be found. Run Install_MerbeinCAD.bat to set up Python and dependencies.
pause
exit /b 1
:run
"%PYTHON_BIN%" app.py
:done
if errorlevel 1 pause
