@echo off
REM Multi-Language Desktop Application Launcher

echo ==========================================
echo  Live Stream Phone Extractor
echo  直播手机号提取器
echo ==========================================
echo.

REM Check if in correct directory
if not exist "app_multilang.py" (
    echo Error: app_multilang.py not found
    echo Please run from desktop_app directory
    pause
    exit /b 1
)

echo Starting application...
echo 启动应用程序...
echo.
echo Select your language / 选择您的语言
echo.

REM Run the application
pythonw app_multilang.py

if errorlevel 1 (
    echo.
    echo Failed to start with pythonw, trying python...
    python app_multilang.py
    pause
)
