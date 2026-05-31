@echo off
title Pinterest Batch Poster
cd /d "%~dp0..\.."
echo Posting all listings to Pinterest...
python tools/pinterest_batch_poster.py
pause
