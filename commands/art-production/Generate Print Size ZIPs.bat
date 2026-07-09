@echo off
title Generate Print Sizes
cd /d "%~dp0..\.."
echo Generating multi-size print ZIPs for all art files...
python tools/generate_print_sizes.py
pause
