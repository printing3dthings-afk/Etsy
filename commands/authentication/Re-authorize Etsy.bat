@echo off
title Etsy OAuth
cd /d "%~dp0..\.."
echo Re-authorizing Etsy (opens browser)...
python tools/etsy_oauth.py
pause
