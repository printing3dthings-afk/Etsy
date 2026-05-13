@echo off
title OnBrandCraftz - First Time Setup
cd /d "%~dp0"

echo.
echo  ================================================
echo    OnBrandCraftz - First Time Setup
echo  ================================================
echo.

REM ── Check Python ───────────────────────────────────
echo  [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo  ERROR: Python not found.
    echo  Download and install Python 3.10+ from:
    echo  https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)
python --version
echo  Python OK.
echo.

REM ── Create virtual environment ─────────────────────
echo  [2/5] Creating virtual environment...
if exist ".venv" (
    echo  Already exists, skipping.
) else (
    python -m venv .venv
    echo  Done.
)
echo.

REM ── Activate and install packages ─────────────────
echo  [3/5] Installing packages (this may take a minute)...
call .venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
echo  Done.
echo.

REM ── Create .env file ───────────────────────────────
echo  [4/5] Setting up .env file...
if not exist ".env" (
    copy .env.example .env >nul
    echo  Created .env file.
) else (
    echo  .env already exists.
)
echo.

REM ── Ask for Anthropic API key ──────────────────────
echo  [5/5] Anthropic API Key
echo.
echo  You need a free API key from Anthropic to run the agents.
echo.
echo  To get one:
echo    1. Open your browser
echo    2. Go to: console.anthropic.com
echo    3. Sign in or create a free account
echo    4. Click "API Keys" then "Create Key"
echo    5. Copy the key (starts with sk-ant-...)
echo    6. Come back here and paste it below
echo.

REM Check if key is already set
python -c "from dotenv import dotenv_values; v=dotenv_values('.env'); print('SET' if v.get('ANTHROPIC_API_KEY','').startswith('sk-') else 'MISSING')" 2>nul > .keycheck.tmp
set /p KEYCHECK=<.keycheck.tmp
del .keycheck.tmp >nul 2>&1

if "%KEYCHECK%"=="SET" (
    echo  API key is already set - skipping.
    goto DONE
)

echo.
set /p APIKEY="  Paste your API key here and press Enter: "

if "%APIKEY%"=="" (
    echo.
    echo  No key entered. You can add it later by editing the .env file.
    goto DONE
)

REM Write the key into the .env file
python -c "
import re, sys
key = sys.argv[1]
with open('.env', 'r') as f:
    content = f.read()
content = re.sub(r'ANTHROPIC_API_KEY=.*', 'ANTHROPIC_API_KEY=' + key, content)
with open('.env', 'w') as f:
    f.write(content)
print('  API key saved successfully.')
" "%APIKEY%"

:DONE
echo.
echo  ================================================
echo    Setup complete!
echo  ================================================
echo.
echo  Double-click "Start Town.bat" to launch the app.
echo.
pause
