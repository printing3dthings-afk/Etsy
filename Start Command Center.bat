@echo off
title OnBrandCraftz Command Center
echo.
echo  Starting OnBrandCraftz Command Center...
echo  Opening browser to http://localhost:5055
echo.

REM Open browser after short delay
start "" /B cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5055"

REM Start the server (keep window open)
python command_center.py

pause
