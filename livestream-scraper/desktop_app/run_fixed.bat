@echo off
REM Fixed Desktop Application Launcher

echo ==========================================
echo  Live Stream Phone Extractor (Fixed)
echo ==========================================
echo.

cd /d "%~dp0"

if not exist "app_fixed.py" (
    echo Error: app_fixed.py not found
    pause
    exit /b 1
)

echo Starting application with improved scraper...
echo.

python app_fixed.py

if errorlevel 1 (
    echo.
    echo Failed to start, trying with console visible...
    python app_fixed.py
    pause
)
