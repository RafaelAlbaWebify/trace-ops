@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

echo Running TRACE local code audit...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\audit-trace-local.ps1"

echo.
echo TRACE audit finished. Review the ZIP created in your Downloads folder.
echo.
pause
