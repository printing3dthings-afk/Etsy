@echo off
rem Keeps the Bambu P1S bridge running on a Windows laptop at home (Scott, 2026-10-24).
rem Fetches the latest code before every start and restarts the bridge if it stops.
rem Set this to run at startup with Task Scheduler: tools\relay\BRIDGE_LAPTOP_SETUP.md, step 6.
cd /d "%~dp0\..\.."
:loop
git pull --ff-only
python tools\relay\bambu_p1s_bridge.py
echo [%date% %time%] bridge stopped; restarting in 15 seconds
ping -n 16 127.0.0.1 >nul
goto loop
