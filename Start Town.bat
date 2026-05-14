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

REM ── Open firewall port 8080 ───────────────────────
netsh advfirewall firewall show rule name="OnBrandCraftz Town" >nul 2>&1
if errorlevel 1 (
    netsh advfirewall firewall add rule name="OnBrandCraftz Town" dir=in action=allow protocol=TCP localport=8080 >nul 2>&1
)

REM ── Get local IP ──────────────────────────────────
for /f "tokens=2 delims=:" %%A in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "127.0.0.1" ^| findstr /v "Tunnel"') do (
    set LOCAL_IP=%%A
    goto :GOT_IP
)
:GOT_IP
set LOCAL_IP=%LOCAL_IP: =%

REM ── Ask: local or public (ngrok)? ─────────────────
echo  How do you want to access the Town?
echo.
echo    [1]  Local only  (same WiFi — fastest, private)
echo    [2]  Public URL  (access from anywhere via ngrok)
echo.
set /p ACCESS_MODE="  Enter 1 or 2: "
echo.

if "%ACCESS_MODE%"=="2" goto :NGROK_MODE

REM ══════════════════════════════════════════════════
:LOCAL_MODE
echo  ================================================
echo.
echo    This PC:   http://localhost:8080
if defined LOCAL_IP (
    echo    Phone/TV:  http://%LOCAL_IP%:8080
    echo.
    echo    Make sure your phone is on the same WiFi.
)
echo.
echo    Keep this window open. Ctrl+C to stop.
echo  ================================================
echo.
start "" http://localhost:8080
python town_app\server.py
goto :EOF

REM ══════════════════════════════════════════════════
:NGROK_MODE
REM ── Check ngrok installed ─────────────────────────
ngrok version >nul 2>&1
if errorlevel 1 (
    echo  ngrok not found.
    echo.
    echo  Install it in 30 seconds:
    echo    1. Go to https://ngrok.com/download
    echo    2. Download the Windows ZIP
    echo    3. Extract ngrok.exe to this folder  OR  add it to PATH
    echo    4. Sign up free at ngrok.com, copy your authtoken, run:
    echo         ngrok config add-authtoken YOUR_TOKEN
    echo    5. Re-run Start Town.bat and choose option 2 again.
    echo.
    pause
    exit /b 1
)

REM ── Start the server in the background ────────────
echo  Starting server...
start /b python town_app\server.py

REM ── Wait for server to be ready ───────────────────
echo  Waiting for server to start...
:WAIT_LOOP
timeout /t 1 /nobreak >nul
powershell -Command "try { (Invoke-WebRequest http://localhost:8080 -UseBasicParsing -TimeoutSec 1).StatusCode } catch { exit 1 }" >nul 2>&1
if errorlevel 1 goto :WAIT_LOOP
echo  Server ready.
echo.

REM ── Start ngrok tunnel ────────────────────────────
echo  Opening ngrok tunnel...
start /b ngrok http 8080 --log=stdout > ngrok.log 2>&1

REM ── Wait for ngrok to get a URL ───────────────────
timeout /t 3 /nobreak >nul
:NGROK_WAIT
timeout /t 1 /nobreak >nul
powershell -Command "try { $r=(Invoke-WebRequest http://localhost:4040/api/tunnels -UseBasicParsing).Content | ConvertFrom-Json; if($r.tunnels.Count -gt 0){exit 0}else{exit 1} } catch { exit 1 }" >nul 2>&1
if errorlevel 1 goto :NGROK_WAIT

REM ── Extract and display the public URL ────────────
for /f "usebackq delims=" %%U in (`powershell -Command "(Invoke-WebRequest http://localhost:4040/api/tunnels -UseBasicParsing).Content | ConvertFrom-Json | Select-Object -ExpandProperty tunnels | Where-Object {$_.proto -eq 'https'} | Select-Object -ExpandProperty public_url"`) do set PUBLIC_URL=%%U

echo  ================================================
echo.
echo    PUBLIC URL (works from anywhere):
echo.
echo      %PUBLIC_URL%
echo.
echo    Local WiFi:  http://%LOCAL_IP%:8080
echo    This PC:     http://localhost:8080
echo.
echo    Share the PUBLIC URL with your phone, tablet,
echo    or anyone — no VPN or same-WiFi needed.
echo.
echo    URL changes each restart (free plan).
echo    Sign up at ngrok.com for a fixed domain.
echo.
echo    Keep this window open. Ctrl+C to stop both.
echo  ================================================
echo.

start "" %PUBLIC_URL%

REM ── Keep window alive (server is already running) ─
echo  Press any key to stop the server and tunnel.
pause >nul
taskkill /f /im ngrok.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
