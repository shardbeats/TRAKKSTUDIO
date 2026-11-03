@echo off
setlocal EnableExtensions
title TRAKKSTUDIO - Run
cd /d "%~dp0"

echo ================================================
echo   TRAKKSTUDIO
echo   Launch (existing .venv)
echo ================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo Run start.bat first to create it.
    echo.
    pause
    exit /b 1
)

echo Launching the app...
".venv\Scripts\python.exe" main.py %*
if errorlevel 1 (
    echo.
    echo [ERROR] The app exited with an error.
    pause
)

endlocal
