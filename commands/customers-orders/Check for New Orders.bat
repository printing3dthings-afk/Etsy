@echo off
title Check Orders
cd /d "%~dp0..\.."
python tools/order_notifier.py
pause
