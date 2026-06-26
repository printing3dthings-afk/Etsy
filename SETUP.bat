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
    copy .env.example .env >nul
    echo  .env file created from .env.example — open it and fill in your API keys.
) else (
    echo  .env file already exists, skipping.
)

echo.
echo  Setup complete!
echo  Run START_HUB.bat to launch the Agent Hub.
echo.
pause
