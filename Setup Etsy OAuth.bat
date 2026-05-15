@echo off
title OnBrandCraftz - Etsy OAuth Setup
cd /d "%~dp0"

echo.
echo ================================================
echo   OnBrandCraftz - Etsy OAuth Setup
echo ================================================
echo.

:: Check if ETSY_CLIENT_ID is still the placeholder
findstr /C:"ETSY_CLIENT_ID=your_" .env >nul 2>&1
if not errorlevel 1 (
    echo  ETSY_CLIENT_ID is not set yet.
    echo.
    echo  To get your Client ID:
    echo    1. Go to https://www.etsy.com/developers/
    echo    2. Sign in and click "Create a New App"
    echo    3. Copy your Keystring (Client ID)
    echo    4. Open .env in a text editor
    echo    5. Replace the ETSY_CLIENT_ID value with your Keystring
    echo    6. Also set ETSY_CLIENT_SECRET to your Shared Secret
    echo    7. Re-run this script
    echo.
    pause
    exit /b 1
)

:: Load .env variables
for /f "tokens=1,2 delims==" %%A in (.env) do set %%A=%%B

echo  Running Etsy OAuth flow...
echo.
python tools/etsy_oauth.py

if errorlevel 1 (
    echo.
    echo  OAuth failed. Check your ETSY_CLIENT_ID and ETSY_CLIENT_SECRET in .env
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================
echo   Success! Etsy tokens saved to .env
echo   Restart "Start Town" to activate the changes.
echo ================================================
echo.
pause
