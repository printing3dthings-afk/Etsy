@echo off
title Rebuild DP1028 Sticker Pack
cd /d "%~dp0..\.."
python tools/rebuild_sticker_pack.py --pid DP1028
pause
