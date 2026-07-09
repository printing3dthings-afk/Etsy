@echo off
title Refresh Market References
cd /d "%~dp0..\.."
echo Downloading 200 reference images from Etsy (10 per category)...
python tools/fetch_market_examples.py --refresh
echo Done. Open market_references.html to browse.
pause
