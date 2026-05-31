@echo off
title Art Category Rotation List
cd /d "%~dp0..\.."
python tools/post_scheduled_art.py --list
pause
