@echo off
title OnBrandCraftz - Setup
cd /d "%~dp0"

echo.
echo  ================================================
echo    OnBrandCraftz - Setup
echo  ================================================
echo.

REM -- Check Python --
echo  [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python not found.
    echo  Download from: https://www.python.org/downloads/
    echo  Check "Add Python to PATH" during install.
    pause
    exit /b 1
)
python --version
echo  Python OK.
echo.

REM -- Install packages --
echo  [2/3] Installing required packages...
pip install -r requirements.txt --quiet
echo  Packages installed.
echo.

REM -- Create .env file --
echo  [3/3] Setting up .env file...
if not exist ".env" (
    copy .env.example .env >nul
    echo  Created .env file.
) else (
    echo  .env already exists.
)
echo.

REM -- Ask for Anthropic API key --
echo  ================================================
echo    Enter your Anthropic API key
echo  ================================================
echo.
echo  Get your free key at: console.anthropic.com
echo  Sign in - click API Keys - Create Key - copy it
echo.

REM -- Check if key already set --
powershell -Command "if ((Get-Content .env | Select-String 'ANTHROPIC_API_KEY=sk-').Count -gt 0) { exit 0 } else { exit 1 }" >nul 2>&1
if not errorlevel 1 (
    echo  API key already saved - skipping.
    goto DONE
)

echo.
set /p APIKEY="  Paste your API key and press Enter: "

if "%APIKEY%"=="" (
    echo  No key entered. Re-run Setup.bat to add it later.
    goto DONE
)

powershell -Command "(Get-Content .env) -replace 'ANTHROPIC_API_KEY=.*', ('ANTHROPIC_API_KEY=' + '%APIKEY%') | Set-Content .env"
echo  API key saved.

:DONE
echo.
echo  ================================================
echo    Setup complete!
echo.
echo    OPTIONAL - open your .env file to add:
echo      OPENAI_API_KEY  - enables AI art generation
echo      ETSY_API_KEY    - connect your Etsy shop
echo      SMTP_PASSWORD   - email digital files
echo.
echo    Then double-click "Start Town.bat" to launch.
echo  ================================================
echo.
pause
