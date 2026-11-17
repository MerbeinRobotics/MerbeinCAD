# MerbeinCAD v0.6 first-time installation on Windows (run through Install_MerbeinCAD.bat).
$ErrorActionPreference='Stop'
$root='C:\MerbeinCAD'
$app=Join-Path $root 'Application'
$source=$PSScriptRoot
function Get-CadPython {
    $candidates=@(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python311\python.exe')
    )
    foreach($candidate in $candidates){if(Test-Path $candidate){return $candidate}}
    $cmd=Get-Command py.exe -ErrorAction SilentlyContinue
    if($cmd){try{ $p=(& $cmd.Source -3 -c 'import sys; print(sys.executable)' 2>$null | Select-Object -First 1); if($p -and (Test-Path $p)){return $p}}catch{}}
    $cmd=Get-Command python.exe -ErrorAction SilentlyContinue
    if($cmd){try{ $p=(& $cmd.Source -c 'import sys; print(sys.executable)' 2>$null | Select-Object -First 1); if($p -and (Test-Path $p)){return $p}}catch{}}
    return $null
}
try {
    if(-not (Test-Path (Join-Path $source 'app.py'))){throw 'Run the installer from the extracted Application folder.'}
    $python=Get-CadPython
    if(-not $python){
        Write-Host 'Python not detected. Attempting to install Python 3.12 with Windows Package Manager (winget)...'
        $wg=Get-Command winget.exe -ErrorAction SilentlyContinue
        if(-not $wg){throw 'Python is missing and winget is unavailable. Install Python 3.12 from python.org and rerun this installer.'}
        & $wg.Source install --id Python.Python.3.12 --exact --source winget --scope user --accept-package-agreements --accept-source-agreements
        if($LASTEXITCODE -ne 0){throw 'Python installation failed or was cancelled. Rerun after installing Python 3.12.'}
        $python=Get-CadPython
        if(-not $python){throw 'Python installed but not yet detected. Close this window and run the installer again.'}
    }
    Write-Host "Using Python: $python"
    foreach($folder in @('Projects','Backups','Updates','Exports')){New-Item -Force -ItemType Directory -Path (Join-Path $root $folder) | Out-Null}
    $stage=Join-Path $root 'Application_v06_new'
    if(Test-Path $stage){throw "Existing staging directory: $stage. Inspect it before retrying."}
    Copy-Item -LiteralPath $source -Destination $stage -Recurse
    if(-not(Test-Path (Join-Path $stage 'app.py'))){throw 'Copy validation failed.'}
    $old=Join-Path $root 'Application_v06_previous'
    if(Test-Path $old){throw "Existing previous-application directory: $old. Inspect it before retrying."}
    if(Test-Path $app){
        $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
        Copy-Item -LiteralPath $app -Destination (Join-Path $root "Backups\Application_before_v06_$stamp") -Recurse
        Move-Item -LiteralPath $app -Destination $old
    }
    try{Move-Item -LiteralPath $stage -Destination $app}
    catch{if((Test-Path $old) -and -not(Test-Path $app)){Move-Item -LiteralPath $old -Destination $app};throw}
    if(Test-Path $old){Remove-Item -LiteralPath $old -Recurse -Force}
    # Save detected interpreter: launch script can use this even if PATH has not refreshed.
    Set-Content -Path (Join-Path $app 'python_path.txt') -Value $python -Encoding Ascii
    $desktop=[Environment]::GetFolderPath('Desktop')
    $shell=New-Object -ComObject WScript.Shell
    $shortcut=$shell.CreateShortcut((Join-Path $desktop 'MerbeinCAD.lnk'))
    $shortcut.TargetPath=Join-Path $app 'launch_windows.bat'
    $shortcut.WorkingDirectory=$app
    $shortcut.Description='MerbeinCAD v0.6 engineering CAD'
    $shortcut.Save()
    Write-Host 'Installing required Python packages (internet connection required)...'
    & $python -m pip install -r (Join-Path $app 'requirements.txt')
    if($LASTEXITCODE -ne 0){throw 'Application copied, but dependency installation failed. Check your internet connection and rerun the installer.'}
    Write-Host 'SUCCESS: MerbeinCAD installed at C:\MerbeinCAD\Application' -ForegroundColor Green
    Write-Host 'Desktop shortcut created. Drawings and exports remain in separate folders.'
}catch{
    Write-Host "INSTALLATION FAILED: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
