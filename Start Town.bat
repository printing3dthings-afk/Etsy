@echo off
title OnBrandCraftz Town
cd /d "%~dp0"

echo.
echo  ================================================
echo    OnBrandCraftz Town - Starting...
echo  ================================================
echo.

REM -- Pull latest code --
git --version >nul 2>&1
if not errorlevel 1 (
    echo  Checking for updates...
    git pull --ff-only >nul 2>&1
    if not errorlevel 1 (
        echo  Up to date.
    ) else (
        echo  Could not auto-update - continuing.
    )
)
echo.

REM -- Check Python --
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found.
    echo  Download from python.org and check "Add to PATH".
    pause
    exit /b 1
)

REM -- Check .env --
if not exist ".env" (
    echo  ERROR: .env file not found. Run Setup.bat first.
    pause
    exit /b 1
)

REM -- Check API key --
powershell -Command "if ((Get-Content .env | Select-String 'ANTHROPIC_API_KEY=sk-').Count -gt 0) { exit 0 } else { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo  ERROR: ANTHROPIC_API_KEY not set in .env
    echo  Run Setup.bat and paste your Anthropic API key.
    pause
    exit /b 1
)

REM -- Install / update packages --
echo  Checking packages...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  WARNING: Some packages may have failed to install.
)
echo  Packages OK.
echo.

REM -- Open firewall port 8080 --
netsh advfirewall firewall show rule name="OnBrandCraftz Town" >nul 2>&1
if errorlevel 1 (
    netsh advfirewall firewall add rule name="OnBrandCraftz Town" dir=in action=allow protocol=TCP localport=8080 >nul 2>&1
)

REM -- Get local IP via PowerShell --
for /f "usebackq delims=" %%I in (`powershell -Command "(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.*' } | Select-Object -First 1).IPAddress" 2^>nul`) do set LOCAL_IP=%%I

REM -- Ask access mode --
echo  How do you want to access the Town?
echo.
echo    [1]  Local only   (same WiFi)
echo    [2]  Public URL   (anywhere, requires ngrok)
echo.
set /p ACCESS_MODE="  Enter 1 or 2 then press Enter: "
echo.

if "%ACCESS_MODE%"=="2" goto NGROK_MODE

REM ==================================================
:LOCAL_MODE
echo  ================================================
echo.
echo    This PC :  http://localhost:8080
if defined LOCAL_IP (
    echo    Phone   :  http://%LOCAL_IP%:8080
    echo.
    echo    Connect your phone to the same WiFi network.
)
echo.
echo    Starting server... browser will open in ~2 sec.
echo    Keep this window open.  Ctrl+C to stop.
echo  ================================================
echo.
python town_app\server.py 2>&1
set EXITCODE=%ERRORLEVEL%
echo.
echo  ================================================
echo  Server stopped (exit code %EXITCODE%).
echo  If you see an error above, copy it for support.
echo  ================================================
echo.
pause
exit /b 0

REM ==================================================
:NGROK_MODE
ngrok version >nul 2>&1
if errorlevel 1 (
    echo  ngrok not found.
    echo.
    echo  Quick install:
    echo    1. Download from https://ngrok.com/download  (Windows ZIP)
    echo    2. Extract ngrok.exe into this folder
    echo    3. Sign up free at ngrok.com, then run once:
    echo         ngrok config add-authtoken YOUR_TOKEN
    echo    4. Re-run Start Town.bat and choose option 2.
    echo.
    pause
    exit /b 1
)

REM -- Start server in background --
echo  Starting server...
start "OnBrandCraftz Server" /b python town_app\server.py

REM -- Wait until server is accepting connections --
echo  Waiting for server to be ready...
:WAIT_LOOP
timeout /t 1 /nobreak >nul
powershell -Command "try{(Invoke-WebRequest http://localhost:8080 -UseBasicParsing -TimeoutSec 1).StatusCode;exit 0}catch{exit 1}" >nul 2>&1
if errorlevel 1 goto WAIT_LOOP
echo  Server ready.
echo.

REM -- Start ngrok --
echo  Opening ngrok tunnel...
start "ngrok" /b ngrok http 8080

REM -- Poll ngrok API for the public URL --
timeout /t 3 /nobreak >nul
:NGROK_WAIT
timeout /t 1 /nobreak >nul
powershell -Command "try{$r=(Invoke-WebRequest http://localhost:4040/api/tunnels -UseBasicParsing).Content|ConvertFrom-Json;if($r.tunnels.Count -gt 0){exit 0}else{exit 1}}catch{exit 1}" >nul 2>&1
if errorlevel 1 goto NGROK_WAIT

for /f "usebackq delims=" %%U in (`powershell -Command "(Invoke-WebRequest http://localhost:4040/api/tunnels -UseBasicParsing).Content|ConvertFrom-Json|Select-Object -ExpandProperty tunnels|Where-Object{$_.proto -eq 'https'}|Select-Object -First 1 -ExpandProperty public_url"`) do set PUBLIC_URL=%%U

echo  ================================================
echo.
echo    PUBLIC URL (share this -- works from anywhere):
echo.
echo      %PUBLIC_URL%
echo.
if defined LOCAL_IP (echo    WiFi only  :  http://%LOCAL_IP%:8080)
echo    This PC    :  http://localhost:8080
echo.
echo    Free plan: URL changes each restart.
echo    ngrok.com paid plan = permanent URL.
echo.
echo    Keep this window open.  Press any key to stop.
echo  ================================================
echo.
start "" "%PUBLIC_URL%"
pause >nul

REM -- Clean shutdown --
taskkill /f /fi "WINDOWTITLE eq ngrok" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq OnBrandCraftz Server" >nul 2>&1
