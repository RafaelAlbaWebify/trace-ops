@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

echo Running TRACE local code audit...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\audit-trace-local.ps1"
set "AUDIT_EXIT=%ERRORLEVEL%"

echo.
echo Verifying TRACE audit ZIP...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$latest = Get-ChildItem -Path (Join-Path $HOME 'Downloads') -Directory -Filter 'TRACE_LOCAL_CODE_AUDIT_*' | Sort-Object LastWriteTime -Descending | Select-Object -First 1; if (-not $latest) { throw 'No TRACE_LOCAL_CODE_AUDIT folder found in Downloads.' }; $zip = $latest.FullName + '.zip'; if (-not (Test-Path -LiteralPath $zip)) { Compress-Archive -LiteralPath (Join-Path $latest.FullName '*') -DestinationPath $zip -Force }; if (-not (Test-Path -LiteralPath $zip)) { throw ('Audit ZIP was not created: ' + $zip) }; Write-Host ('TRACE audit ZIP ready: ' + $zip)"
if errorlevel 1 (
    echo.
    echo TRACE audit ZIP verification failed.
    pause
    exit /b 1
)

echo.
if not "%AUDIT_EXIT%"=="0" (
    echo TRACE audit completed with findings or failed checks. Upload the ZIP for review.
) else (
    echo TRACE audit completed successfully. Upload the ZIP for review.
)
echo.
pause
exit /b %AUDIT_EXIT%
