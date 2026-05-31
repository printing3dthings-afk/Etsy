@echo off
title Rebuild DP1029 Sticker Pack
cd /d "%~dp0..\.."
python tools/rebuild_sticker_pack.py --pid DP1029
pause
