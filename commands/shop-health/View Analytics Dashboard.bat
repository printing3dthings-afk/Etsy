@echo off
title Analytics Dashboard
cd /d "%~dp0..\.."
echo Running Analytics Tracker...
python tools/analytics_tracker.py
pause
