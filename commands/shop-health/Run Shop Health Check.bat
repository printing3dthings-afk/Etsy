@echo off
title Shop Health Check
cd /d "%~dp0..\.."
echo Running Shop Health Check...
python tools/shop_health_check.py
pause
