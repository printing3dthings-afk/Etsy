@echo off
title Generate Sticker Pack Photos
cd /d "%~dp0..\.."
echo Generating sticker pack listing photos...
python tools/gen_sticker_listing_photos.py
pause
