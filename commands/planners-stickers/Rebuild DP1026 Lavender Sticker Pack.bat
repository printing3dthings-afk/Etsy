@echo off
title Rebuild DP1026 Sticker Pack
cd /d "%~dp0..\.."
python tools/rebuild_sticker_pack.py --pid DP1026
pause
