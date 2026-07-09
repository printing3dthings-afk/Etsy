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

REM -- Kill any process already on port 8080 --
echo  Checking if port 8080 is free...
for /f "tokens=5" %%P in ('netstat -ano 2^>nul ^| findstr ":8080 " ^| findstr "LISTENING"') do (
    echo  Stopping old server on port 8080 (PID %%P)...
    taskkill /f /pid %%P >nul 2>&1
)
timeout /t 1 /nobreak >nul
echo.

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
echo    [2]  Public URL   (anywhere, free - no account needed)
echo.
set /p ACCESS_MODE="  Enter 1 or 2 then press Enter: "
echo.

if "%ACCESS_MODE%"=="2" goto CLOUDFLARED_MODE

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
:CLOUDFLARED_MODE

REM -- Download cloudflared if not present --
if not exist "cloudflared.exe" (
    echo  cloudflared.exe not found. Downloading ^(~40 MB, one time^)...
    powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe' -OutFile 'cloudflared.exe' -UseBasicParsing"
    if errorlevel 1 (
        echo  ERROR: Download failed. Check your internet connection.
        pause
        exit /b 1
    )
    echo  cloudflared.exe downloaded.
    echo.
)

REM -- Start server in background --
echo  Starting server...
start "OnBrandCraftz Server" /b python town_app\server.py

REM -- Wait until server is accepting connections --
echo  Waiting for server to be ready...
:CF_WAIT_SERVER
timeout /t 1 /nobreak >nul
powershell -NoProfile -Command "try{(Invoke-WebRequest http://localhost:8080 -UseBasicParsing -TimeoutSec 1).StatusCode;exit 0}catch{exit 1}" >nul 2>&1
if errorlevel 1 goto CF_WAIT_SERVER
echo  Server ready.
echo.

REM -- Start cloudflared, pipe output to a temp log --
echo  Opening Cloudflare tunnel (no account needed)...
set "CF_LOG=%TEMP%\oncraftz_cf.log"
if exist "%CF_LOG%" del "%CF_LOG%"
start "cloudflared" /b cmd /c "cloudflared.exe tunnel --url http://localhost:8080 --no-autoupdate 1>"%CF_LOG%" 2>&1"

REM -- Poll log for trycloudflare.com URL (up to ~30 s) --
echo  Waiting for public URL...
set CF_TRIES=0
:CF_URL_WAIT
timeout /t 2 /nobreak >nul
set /a CF_TRIES+=1
if %CF_TRIES% gtr 15 (
    echo  ERROR: Timed out waiting for cloudflared URL.
    echo  Check your internet connection and try again.
    goto CF_SHUTDOWN
)
set PUBLIC_URL=
for /f "usebackq delims=" %%U in (`powershell -NoProfile -Command "$c=Get-Content '%CF_LOG%' -ErrorAction SilentlyContinue -Raw;if($c){$m=[regex]::Match($c,'https://[a-z0-9-]+\.trycloudflare\.com');if($m.Success){Write-Output $m.Value}}"`) do set PUBLIC_URL=%%U
if not defined PUBLIC_URL goto CF_URL_WAIT

REM -- Post URL to server so the town UI shows it --
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'http://localhost:8080/api/tunnel-url' -Method POST -Body '{\"url\":\"%PUBLIC_URL%\"}' -ContentType 'application/json' -UseBasicParsing" >nul 2>&1

echo.
echo  ================================================
echo.
echo    PUBLIC URL (works from anywhere, free):
echo.
echo      %PUBLIC_URL%
echo.
if defined LOCAL_IP (echo    Same WiFi  :  http://%LOCAL_IP%:8080)
echo    This PC    :  http://localhost:8080
echo.
echo    No account required.  URL changes each restart.
echo    Keep this window open.  Press any key to stop.
echo  ================================================
echo.
start "" "%PUBLIC_URL%"
pause >nul

:CF_SHUTDOWN
REM -- Clear tunnel URL and shut down --
powershell -NoProfile -Command "Invoke-WebRequest -Uri 'http://localhost:8080/api/tunnel-url' -Method POST -Body '{\"url\":\"\"}' -ContentType 'application/json' -UseBasicParsing" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq cloudflared" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq OnBrandCraftz Server" >nul 2>&1
