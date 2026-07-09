@echo off
title OnBrandCraftz - Pinterest OAuth Setup
cd /d "%~dp0"

echo.
echo ================================================
echo   OnBrandCraftz - Pinterest OAuth Setup
echo ================================================
echo.

:: Check if PINTEREST_APP_ID is still the placeholder
findstr /C:"PINTEREST_APP_ID=your_" .env >nul 2>&1
if not errorlevel 1 (
    echo  PINTEREST_APP_ID is not set yet.
    echo.
    echo  To get your App ID and Secret:
    echo    1. Go to https://developers.pinterest.com/
    echo    2. Sign in and click "New App"
    echo    3. Fill in the app name and description, then submit
    echo    4. Copy your App ID and App Secret key
    echo    5. Open .env in a text editor
    echo    6. Set PINTEREST_APP_ID to your App ID
    echo    7. Set PINTEREST_APP_SECRET to your App Secret
    echo    8. Re-run this script
    echo.
    pause
    exit /b 1
)

:: Load .env variables
for /f "tokens=1,2 delims==" %%A in (.env) do set %%A=%%B

echo  Running Pinterest OAuth flow...
echo.
python tools/pinterest_oauth.py

if errorlevel 1 (
    echo.
    echo  OAuth failed. Check your PINTEREST_APP_ID and PINTEREST_APP_SECRET in .env
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   Success! Pinterest connected and tokens saved.
echo   You can now post pins directly from the hub.
echo ================================================
echo.
pause
