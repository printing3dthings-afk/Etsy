@echo off
title Post Art to Etsy
cd /d "%~dp0..\.."
echo WARNING: This will post a LIVE listing to Etsy.
set /p confirm="Type YES to continue: "
if /i "%confirm%"=="YES" (
    python tools/post_scheduled_art.py --force
) else (
    echo Cancelled.
)
pause
