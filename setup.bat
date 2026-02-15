@echo off
setlocal enabledelayedexpansion

:: ============================================
:: Setup Script
:: ============================================

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
cd /d "%SCRIPT_DIR%"

:: Colors
set "reset="
set "green="
set "red="
set "yellow="
set "cyan="
set "bold="

echo.
echo ============================================
echo   Zen Downloader - Setup
echo ============================================
echo.

:: ============================================
:: Step 1: Check Python
:: ============================================
echo [1/6] Checking Python installation...

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed!
    echo Please install Python 3.10+ from: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PYTHON_VERSION=%%v"
echo [OK] Python %PYTHON_VERSION% found

:: ============================================
:: Step 2: Check FFmpeg
:: ============================================
echo.
echo [2/6] Checking FFmpeg...

:: Check if FFmpeg is in system PATH
where ffmpeg >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%i in ('where ffmpeg') do set "FFMPEG_PATH=%%i"
    echo [OK] FFmpeg found in system: %FFMPEG_PATH%
    set "FFMPEG_READY=true"
    goto :install_deps
)

:: Check if FFmpeg exists in bin folder
if exist "%SCRIPT_DIR%\bin\ffmpeg\bin\ffmpeg.exe" (
    echo [OK] FFmpeg found in bin folder
    set "FFMPEG_READY=true"
    goto :install_deps
)

:: FFmpeg not found - try to install
echo FFmpeg not found. Attempting to install...

:: Try Chocolatey first
where choco >nul 2>&1
if not errorlevel 1 (
    echo Trying Chocolatey installation...
    choco install ffmpeg -y >nul 2>&1
    if not errorlevel 1 (
        where ffmpeg >nul 2>&1
        if not errorlevel 1 (
            echo [OK] FFmpeg installed via Chocolatey
            set "FFMPEG_READY=true"
            goto :install_deps
        )
    )
)

:: Chocolatey failed or not available - download portable FFmpeg
echo Downloading portable FFmpeg (this may take a minute)...

:: Create bin folder
if not exist "%SCRIPT_DIR%\bin" mkdir "%SCRIPT_DIR%\bin"

:: Download FFmpeg using curl
set "FFMPEG_ZIP=%TEMP%\ffmpeg.zip"
set "FFMPEG_URL=https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl-shared.zip"

echo Downloading from: %FFMPEG_URL%

:: Try curl first, then certutil (Windows built-in)
curl -L -o "%FFMPEG_ZIP%" "%FFMPEG_URL%" --ssl-no-revoke 2>nul
if not exist "%FFMPEG_ZIP%" (
    echo Trying certutil download...
    certutil -urlcache -split -f "%FFMPEG_URL%" "%FFMPEG_ZIP%" 2>nul
)

if not exist "%FFMPEG_ZIP%" (
    echo ERROR: Failed to download FFmpeg!
    echo.
    echo Please download FFmpeg manually:
    echo 1. Go to: https://ffmpeg.org/download.html
    echo 2. Download Windows builds
    echo 3. Extract to: %SCRIPT_DIR%\bin\ffmpeg\
    echo.
    pause
    exit /b 1
)

echo Extracting FFmpeg...

:: Try multiple extraction methods
set "EXTRACTED=false"

:: Method 1: Try PowerShell with full path
if exist "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" (
    "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe" -Command "Expand-Archive -Path '%FFMPEG_ZIP%' -DestinationPath '%TEMP%\ffmpeg_extract' -Force" 2>nul
    if exist "%TEMP%\ffmpeg_extract" set "EXTRACTED=true"
)

:: Method 2: Try 7-Zip if available
if "%EXTRACTED%"=="false" (
    where 7z >nul 2>&1
    if not errorlevel 1 (
        7z x "%FFMPEG_ZIP%" -o"%TEMP%\ffmpeg_extract" -y >nul 2>&1
        if exist "%TEMP%\ffmpeg_extract" set "EXTRACTED=true"
    )
)

:: Method 3: Try Windows tar (Windows 10+)
if "%EXTRACTED%"=="false" (
    mkdir "%TEMP%\ffmpeg_extract" 2>nul
    tar -xf "%FFMPEG_ZIP%" -C "%TEMP%\ffmpeg_extract" 2>nul
    if exist "%TEMP%\ffmpeg_extract" set "EXTRACTED=true"
)

if "%EXTRACTED%"=="false" (
    echo ERROR: Failed to extract FFmpeg! No extraction tool available.
    echo Please download FFmpeg manually from: https://ffmpeg.org/download.html
    pause
    exit /b 1
)

:: Find and move ffmpeg folder
set "FOUND_FFMPEG=false"
for /d /r "%TEMP%\ffmpeg_extract" %%d in (*) do (
    if exist "%%d\ffmpeg.exe" (
        move "%%d" "%SCRIPT_DIR%\bin\ffmpeg" >nul 2>&1
        set "FOUND_FFMPEG=true"
        goto :ffmpeg_moved
    )
    if exist "%%d\bin\ffmpeg.exe" (
        move "%%d" "%SCRIPT_DIR%\bin\ffmpeg" >nul 2>&1
        set "FOUND_FFMPEG=true"
        goto :ffmpeg_moved
    )
)

:ffmpeg_moved
if exist "%SCRIPT_DIR%\bin\ffmpeg\bin\ffmpeg.exe" (
    echo [OK] FFmpeg extracted to bin folder
    set "FFMPEG_READY=true"
) else (
    :: Try finding any ffmpeg.exe in extracted folder
    for /r "%TEMP%\ffmpeg_extract" %%f in (ffmpeg.exe) do (
        if exist "%%f" (
            mkdir "%SCRIPT_DIR%\bin\ffmpeg\bin" 2>nul
            move "%%f" "%SCRIPT_DIR%\bin\ffmpeg\bin\" >nul 2>&1
            if exist "%SCRIPT_DIR%\bin\ffmpeg\bin\ffmpeg.exe" (
                echo [OK] FFmpeg extracted to bin folder
                set "FFMPEG_READY=true"
                goto :ffmpeg_ready
            )
        )
    )
)

:ffmpeg_ready
if "%FFMPEG_READY%"=="true" (
    echo [OK] FFmpeg ready
) else (
    echo ERROR: Could not find ffmpeg.exe in extracted files
    echo Please download FFmpeg manually from: https://ffmpeg.org/download.html
    pause
    exit /b 1
)

:: Cleanup
del /f /q "%FFMPEG_ZIP%" 2>nul
rmdir /s /q "%TEMP%\ffmpeg_extract" 2>nul

:: ============================================
:: Step 3: Install Python Dependencies
:: ============================================
:install_deps
echo.
echo [3/6] Installing Python dependencies...

pip install -r requirements.txt >nul 2>&1
if errorlevel 1 (
    echo ERROR: Failed to install dependencies!
    pip install -r requirements.txt
    pause
    exit /b 1
)
echo [OK] Dependencies installed

:: ============================================
:: Step 4: Update yt-dlp
:: ============================================
echo.
echo [4/6] Updating yt-dlp to latest version...

pip install -U yt-dlp >nul 2>&1
if errorlevel 1 (
    echo WARNING: Failed to update yt-dlp
) else (
    for /f "tokens=*" %%v in ('yt-dlp --version') do set "YT_DLP_VERSION=%%v"
    echo [OK] yt-dlp %YT_DLP_VERSION% installed
)

:: ============================================
:: Step 5: Verify Setup
:: ============================================
echo.
echo [5/6] Verifying setup...

:: Test yt-dlp
yt-dlp --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: yt-dlp verification failed!
    pause
    exit /b 1
)
echo [OK] yt-dlp working

:: ============================================
:: Step 6: Final Status
:: ============================================
echo.
echo [6/6] Setup complete!
echo.
echo ============================================
echo   Setup Successful!
echo ============================================
echo.
echo You can now run the app with:
echo   python app.py
echo.
echo Then open: http://localhost:5000
echo.
pause
