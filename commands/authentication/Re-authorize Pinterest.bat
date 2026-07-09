@echo off
title Pinterest OAuth
cd /d "%~dp0..\.."
python tools/pinterest_oauth.py
pause
