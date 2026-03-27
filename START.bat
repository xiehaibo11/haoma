@echo off
chcp 65001 >nul
title Live Stream Phone Extractor
color 0A
cls

echo.
echo  +==================================================================+
echo  ^|                                                                  ^|
echo  ^|          Live Stream Phone Extractor v2.0                       ^|
echo  ^|                                                                  ^|
echo  ^|          Extract phone numbers from live streams                ^|
echo  ^|                                                                  ^|
echo  +==================================================================+
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python is not installed or not in PATH!
    echo.
    echo  Please install Python 3.8+ from https://python.org
    echo  Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo  [OK] Python detected.

:: Check if setup has been run (check for output directory)
if not exist "output" (
    echo.
    echo  [FIRST RUN] Setting up the extractor...
    echo.
    python setup.py
    if errorlevel 1 (
        echo.
        echo  [ERROR] Setup failed!
        pause
        exit /b 1
    )
)

:: Run the startup program
echo.
echo  [OK] Starting Phone Extractor...
echo.
echo  ------------------------------------------------------------------
echo.

python start.py

:: Pause before closing (in case of error)
if errorlevel 1 (
    echo.
    echo  [ERROR] Program exited with error code %errorlevel%
    pause
)
