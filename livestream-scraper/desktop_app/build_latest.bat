@echo off
setlocal
title Build Latest Desktop App

cd /d "%~dp0"
set "ICON_PNG=%~dp0..\NBF.png"
set "ICON_ICO=%~dp0build\NBF.ico"

echo ==========================================
echo Build latest version only (clean old artifacts first)
echo ==========================================
echo.

echo [1/5] Cleaning old build artifacts...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "release" rmdir /s /q "release"
for %%F in (*.spec) do del /q "%%F"
mkdir release
mkdir build

echo [2/5] Installing build dependencies...
python -m pip install -q pyinstaller
if errorlevel 1 (
    echo Failed to install PyInstaller.
    exit /b 1
)
python -m pip install -q pillow
if errorlevel 1 (
    echo Failed to install Pillow.
    exit /b 1
)

echo [3/5] Preparing icon...
if not exist "%ICON_PNG%" (
    echo Icon file not found: %ICON_PNG%
    exit /b 1
)
python -c "from PIL import Image; img=Image.open(r'%ICON_PNG%'); img.save(r'%ICON_ICO%', format='ICO', sizes=[(256,256),(128,128),(64,64),(32,32),(16,16)])"
if errorlevel 1 (
    echo Failed to convert PNG icon to ICO.
    exit /b 1
)

echo [4/5] Building FINAL_APP.py...
pyinstaller --noconfirm --clean --onefile --windowed -p . --hidden-import extractor --icon "%ICON_ICO%" --name LeisuPhoneExtractor_latest FINAL_APP.py
if errorlevel 1 (
    echo Build failed.
    exit /b 1
)

echo [5/5] Publishing latest artifact...
copy /y "dist\LeisuPhoneExtractor_latest.exe" "release\LeisuPhoneExtractor_latest.exe" >nul
if errorlevel 1 (
    echo Failed to copy artifact.
    exit /b 1
)

echo.
echo Build completed:
echo   %cd%\release\LeisuPhoneExtractor_latest.exe
exit /b 0
