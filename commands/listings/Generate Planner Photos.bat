@echo off
title Generate Planner Photos
cd /d "%~dp0..\.."
echo Generating and uploading planner listing photos...
python tools/gen_planner_listing_photos.py
pause
