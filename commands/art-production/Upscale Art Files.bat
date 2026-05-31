@echo off
title Upscale Art Files
cd /d "%~dp0..\.."
echo Upscaling art files under 3000px...
python tools/upscale_art.py
pause
