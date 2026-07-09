@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

echo Running TRACE local code audit...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\audit-trace-local-v2.ps1"
set "AUDIT_EXIT=%ERRORLEVEL%"

echo.
echo TRACE audit command finished.
echo.
pause
exit /b %AUDIT_EXIT%
