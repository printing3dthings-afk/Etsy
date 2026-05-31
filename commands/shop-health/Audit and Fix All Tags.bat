@echo off
title Audit and Fix Tags
cd /d "%~dp0..\.."
echo Auditing and fixing wall art tags...
python tools/audit_fix_wall_art_tags.py
pause
