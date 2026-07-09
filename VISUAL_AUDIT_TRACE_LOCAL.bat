@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

echo Running TRACE visual UI audit...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\visual-audit-trace-local.ps1"
set "AUDIT_EXIT=%ERRORLEVEL%"

echo.
echo TRACE visual audit command finished.
echo.
pause
exit /b %AUDIT_EXIT%
