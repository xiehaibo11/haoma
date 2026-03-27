@echo off
REM Launcher for Desktop Application

echo Starting Live Stream Phone Extractor...
echo.

REM Check if in correct directory
if not exist "FINAL_APP.py" (
    echo Error: Please run this from the desktop_app directory
    pause
    exit /b 1
)

REM Run the application
pythonw FINAL_APP.py

if errorlevel 1 (
    echo.
    echo Error starting application. Trying with console...
    python FINAL_APP.py
    pause
)
