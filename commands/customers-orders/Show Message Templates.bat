@echo off
title Message Templates
cd /d "%~dp0..\.."
python tools/etsy_messages.py
pause
