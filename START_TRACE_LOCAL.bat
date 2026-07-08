@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

echo Starting TRACE local demo...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\start-trace-local.ps1" -Mode All

echo.
echo TRACE launcher finished. Backend and frontend should be opening in separate PowerShell windows.
echo Frontend: http://127.0.0.1:5173
echo Backend docs: http://127.0.0.1:8000/docs
echo.
pause
