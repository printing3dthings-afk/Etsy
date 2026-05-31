@echo off
title Generate Art Preview
cd /d "%~dp0..\.."
echo Generating art for next category (preview only - will NOT post)...
python tools/post_scheduled_art.py --preview
pause
