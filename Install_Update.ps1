param([switch]$WaitForExit)
$ErrorActionPreference = 'Stop'
$root='C:\MerbeinCAD'
$app=Join-Path $root 'Application'
$backupDir=Join-Path $root 'Backups'
$source=Join-Path $PSScriptRoot 'Application'
$stage=Join-Path $root 'Application_v04_staging'
$old=Join-Path $root 'Application_before_v04_pending'
try {
    if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'Expected C:\MerbeinCAD to exist.' }
    if (-not (Test-Path (Join-Path $source 'app.py'))) { throw 'Update archive was not extracted correctly.' }
    if ($WaitForExit) { Start-Sleep -Seconds 3 }
    $running=Get-Process -Name 'MerbeinCAD','python','pythonw' -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$root*" }
    if ($running) { throw 'Close MerbeinCAD and try again.' }
    if ((Test-Path $stage) -or (Test-Path $old)) { throw 'A previous incomplete update folder exists. Please inspect it first.' }
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null
    Copy-Item -LiteralPath $source -Destination $stage -Recurse -Force
    if (-not (Test-Path (Join-Path $stage 'updater.py'))) { throw 'Update staging validation failed.' }
    if (Test-Path -LiteralPath $app) {
        $stamp=Get-Date -Format 'yyyyMMdd_HHmmss'
        $backup=Join-Path $backupDir "Application_before_v04_$stamp"
        Copy-Item -LiteralPath $app -Destination $backup -Recurse
        Write-Host "Previous version backed up: $backup"
        Move-Item -LiteralPath $app -Destination $old
    }
    try { Move-Item -LiteralPath $stage -Destination $app }
    catch {
        if ((Test-Path $old) -and -not (Test-Path $app)) { Move-Item -LiteralPath $old -Destination $app }
        throw
    }
    if (Test-Path $old) { Remove-Item -LiteralPath $old -Recurse -Force }
    Write-Host 'SUCCESS: MerbeinCAD v0.4 installed.' -ForegroundColor Green
    Write-Host 'Your Projects, Exports and Updates folders have not been changed.'
} catch {
    Write-Host "FAILED: $($_.Exception.Message)" -ForegroundColor Red
    if ((Test-Path $old) -and -not (Test-Path $app)) { Move-Item -LiteralPath $old -Destination $app }
    exit 1
} finally {
    if ($WaitForExit) { Read-Host 'Press Enter to close installer' }
}
