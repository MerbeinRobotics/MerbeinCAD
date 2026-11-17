@echo off
cd /d "%~dp0"
echo Building optional standalone MerbeinCAD installer on Windows.
call build_windows_exe.bat
if errorlevel 1 exit /b 1
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
  echo Inno Setup 6 not detected. Install from https://jrsoftware.org/isinfo.php
  echo Then run this script again.
  pause
  exit /b 1
)
"%ISCC%" MerbeinCAD_Setup.iss
if errorlevel 1 pause & exit /b 1
echo Standalone installer created in installer_output.
pause
