@echo off
echo.
echo  OnBrandCraftz Agent Hub - Setup
echo  ================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python is not installed.
    echo  Download it from python.org/downloads
    echo  Make sure to check "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo  Installing required packages...
pip install -r requirements.txt

echo.
echo  Creating .env file...
if not exist .env (
    echo ANTHROPIC_API_KEY=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> .env
    echo ETSY_API_KEY=fubs9x2li9laade3oq5ef45h>> .env
    echo ETSY_SHOP_ID=onbrandcraftz>> .env
    echo PINTEREST_APP_ID=>> .env
    echo PINTEREST_APP_SECRET=>> .env
    echo PINTEREST_ACCESS_TOKEN=>> .env
    echo PINTEREST_REFRESH_TOKEN=>> .env
    echo  .env file created.
) else (
    echo  .env file already exists, skipping.
)

echo.
echo  Setup complete!
echo  Run START_HUB.bat to launch the Agent Hub.
echo.
pause
