@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

echo.
echo ============================================
echo   Zen Downloader - Starting...
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Python not found. Running setup...
    call setup.bat
    goto :start_app
)

:: Check FFmpeg
where ffmpeg >nul 2>&1
if errorlevel 1 (
    if not exist "%SCRIPT_DIR%\bin\ffmpeg\bin\ffmpeg.exe" (
        echo FFmpeg not found. Running setup...
        call setup.bat
    )
)

:: Check Python dependencies
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Dependencies missing. Running setup...
    call setup.bat
)

:start_app
echo.
echo Starting Zen Downloader...
echo.

:: Start Flask app
start python app.py

:: Wait a moment for server to start
timeout /t 3 /nobreak >nul

:: Open browser
start http://localhost:5000

echo Done! Browser should open shortly...
exit
