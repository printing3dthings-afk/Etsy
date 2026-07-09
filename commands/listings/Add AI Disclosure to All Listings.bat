@echo off
title Add AI Disclosure
cd /d "%~dp0..\.."
echo Adding AI disclosure to listings that are missing it...
python tools/add_ai_disclosure.py
pause
