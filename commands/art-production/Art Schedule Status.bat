@echo off
title Art Schedule Status
cd /d "%~dp0..\.."
python tools/post_scheduled_art.py --status
pause
