@echo off
title OnBrandCraftz Command Center
echo.
echo  Starting OnBrandCraftz Command Center...
echo.
echo  This computer:  http://localhost:5055
echo  Phone / tablet: Check the window below for your network address
echo  (Phone must be on the same Wi-Fi as this computer)
echo.

REM Open browser after short delay
start "" /B cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5055"

REM Start the server (keep window open — phone URL prints here)
python command_center.py

pause
