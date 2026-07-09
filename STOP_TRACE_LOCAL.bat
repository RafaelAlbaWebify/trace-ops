@echo off
setlocal

set "SCRIPT_DIR=%~dp0"

echo Stopping TRACE local backend/frontend processes on ports 8000 and 5173...
echo.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%scripts\stop-trace-local.ps1"
set "STOP_EXIT=%ERRORLEVEL%"

echo.
if "%STOP_EXIT%"=="0" (
    echo TRACE local cleanup finished.
) else (
    echo TRACE local cleanup finished with warnings or errors.
)
echo.
pause
exit /b %STOP_EXIT%
