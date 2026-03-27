@echo off
chcp 65001 >nul
title 雷速直播手机号提取器
cd /d "%~dp0"
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python -X utf8 app_optimized.py
