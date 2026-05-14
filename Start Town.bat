@echo off
title OnBrandCraftz Town
cd /d "%~dp0"

echo.
echo  ================================================
echo    OnBrandCraftz Town - Starting...
echo  ================================================
echo.

REM ── Pull latest code from git ─────────────────────
git --version >nul 2>&1
if not errorlevel 1 (
    echo  Checking for updates...
    git pull --ff-only >nul 2>&1
    if not errorlevel 1 (
        echo  Code is up to date.
    ) else (
        echo  Could not auto-update (local changes present or no network).
        echo  Continuing with current version...
    )
) else (
    echo  Git not found - skipping update check.
)
echo.

REM ── Check Python ──────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found. Run Setup.bat first.
    pause
    exit /b 1
)

REM ── Check .env exists ─────────────────────────────
if not exist ".env" (
    echo  ERROR: .env file not found. Run Setup.bat first.
    pause
    exit /b 1
)

REM ── Check API key is set ──────────────────────────
powershell -Command "if ((Get-Content .env | Select-String 'ANTHROPIC_API_KEY=sk-').Count -gt 0) { exit 0 } else { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo  ERROR: ANTHROPIC_API_KEY not set in .env
    echo  Run Setup.bat to add your API key.
    pause
    exit /b 1
)

REM ── Install / update packages ─────────────────────
echo  Installing/updating packages from requirements.txt...
pip install -r requirements.txt --quiet
echo  Packages OK.
echo.

REM ── Open firewall port 8080 (requires admin — skips silently if denied) ───
netsh advfirewall firewall show rule name="OnBrandCraftz Town" >nul 2>&1
if errorlevel 1 (
    echo  Adding firewall rule for port 8080...
    netsh advfirewall firewall add rule name="OnBrandCraftz Town" dir=in action=allow protocol=TCP localport=8080 >nul 2>&1
    if not errorlevel 1 (
        echo  Firewall rule added.
    ) else (
        echo  Could not add firewall rule (run as admin to fix).
    )
)
echo.

REM ── Get local IP address ──────────────────────────
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "127.0.0.1" ^| findstr /v "Tunnel"') do (
    set LOCAL_IP=%%A
    goto :GOT_IP
)
:GOT_IP
set LOCAL_IP=%LOCAL_IP: =%

echo  ================================================
echo.
echo    This PC:   http://localhost:8080
if defined LOCAL_IP (
    echo    Phone/TV:  http://%LOCAL_IP%:8080
    echo.
    echo    Make sure your phone is on the same WiFi.
) else (
    echo    Phone/TV:  connect to same WiFi then visit
    echo               http://YOUR-PC-IP:8080
)
echo.
echo    Keep this window open. Ctrl+C to stop.
echo  ================================================
echo.

start "" http://localhost:8080
python town_app\server.py

pause
