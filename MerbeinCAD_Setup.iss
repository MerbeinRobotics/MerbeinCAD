; Optional Windows-only standalone .exe installer (requires Inno Setup 6).
; Build with build_standalone_installer.bat on a Windows computer.
#define MyAppName "MerbeinCAD"
#define MyAppVersion "0.7"
[Setup]
AppId={{AA6E0DC2-397C-4B81-9E82-A1BDA2D093F0}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
DefaultDirName={localappdata}\Programs\MerbeinCAD
DefaultGroupName=MerbeinCAD
OutputDir=installer_output
OutputBaseFilename=MerbeinCAD_v0.7_Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=lowest
WizardStyle=modern
[Files]
Source: "dist\MerbeinCAD.exe"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{autoprograms}\MerbeinCAD"; Filename: "{app}\MerbeinCAD.exe"
Name: "{autodesktop}\MerbeinCAD"; Filename: "{app}\MerbeinCAD.exe"
[Run]
Filename: "{app}\MerbeinCAD.exe"; Description: "Launch MerbeinCAD"; Flags: nowait postinstall skipifsilent
