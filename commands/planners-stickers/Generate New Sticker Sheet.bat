@echo off
title Generate Sticker Sheet
cd /d "%~dp0..\.."
echo Generating a new sticker sheet (shows for approval)...
python tools/gen_sticker_sheet.py
pause
