@echo off
title Email Templates
cd /d "%~dp0..\.."
python tools/email_leadmagnet.py --templates
pause
