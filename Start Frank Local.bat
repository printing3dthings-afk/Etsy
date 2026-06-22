@echo off
REM Run Frank (tools\api_server\main.py) on this machine, no Railway required.
REM Offline/local fallback launcher.
cd /d "%~dp0"

if not exist .env (
  echo ERROR: .env not found in %cd%.
  echo Copy .env.example to .env and fill in at least ANTHROPIC_API_KEY and APP_SECRET_TOKEN.
  pause
  exit /b 1
)

set ANTHROPIC_API_KEY=
set APP_SECRET_TOKEN=
for /f "usebackq tokens=1,* delims==" %%A in (`findstr /r "^[A-Za-z_][A-Za-z0-9_]*=" .env`) do (
  set "%%A=%%B"
)

if "%ANTHROPIC_API_KEY%"=="" (
  echo ERROR: ANTHROPIC_API_KEY is not set in .env.
  pause
  exit /b 1
)
if "%APP_SECRET_TOKEN%"=="" (
  echo ERROR: APP_SECRET_TOKEN is not set in .env.
  pause
  exit /b 1
)

echo Installing/checking dependencies...
pip install -q -r requirements.txt

if "%PORT%"=="" set PORT=8011

echo.
echo Starting Frank locally at http://localhost:%PORT%/frank
echo (Ctrl+C to stop)
echo.
python tools\api_server\main.py
pause
