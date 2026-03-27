@echo off
chcp 65001 >nul
title Live Stream Phone Extractor
cd /d "%~dp0"
echo Starting Production App...
python app_production.py
pause
