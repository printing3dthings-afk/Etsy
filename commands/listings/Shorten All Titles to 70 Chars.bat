@echo off
title Shorten Listing Titles
cd /d "%~dp0..\.."
echo Trimming all listing titles to 70 characters...
python tools/shorten_titles.py
pause
