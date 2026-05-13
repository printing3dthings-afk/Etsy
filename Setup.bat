@echo off
title OnBrandCraftz - Setup
cd /d "%~dp0"

echo.
echo  ================================================
echo    OnBrandCraftz - Setup
echo  ================================================
echo.

REM ── Check Python ───────────────────────────────────
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

REM ── Install packages ──────────────────────────────
echo  [2/3] Installing required packages...
pip install anthropic python-dotenv flask Pillow reportlab openai fastapi "uvicorn[standard]" --quiet
echo  Packages installed.
echo.

REM ── Create .env file ───────────────────────────────
echo  [3/3] Setting up .env file...
if not exist ".env" (
    copy .env.example .env >nul
    echo  Created .env file.
) else (
    echo  .env already exists.
)
echo.

REM ── Ask for Anthropic API key ──────────────────────
echo  ================================================
echo    Enter your Anthropic API key
echo  ================================================
echo.
echo  Get your free key at: console.anthropic.com
echo  Sign in - click API Keys - Create Key - copy it
echo.

REM Check if key already set
python -c "from dotenv import dotenv_values; v=dotenv_values('.env'); print('SET' if str(v.get('ANTHROPIC_API_KEY','')).startswith('sk-') else 'MISSING')" 2>nul > .keycheck.tmp
set /p KEYCHECK=<.keycheck.tmp
del .keycheck.tmp >nul 2>&1

if "%KEYCHECK%"=="SET" (
    echo  API key already saved - skipping.
    goto DONE
)

echo.
set /p APIKEY="  Paste your API key and press Enter: "

if "%APIKEY%"=="" (
    echo.
    echo  No key entered. Re-run Setup.bat to add it later.
    goto DONE
)

python -c "
import re, sys
key = sys.argv[1]
with open('.env', 'r') as f:
    content = f.read()
content = re.sub(r'ANTHROPIC_API_KEY=.*', 'ANTHROPIC_API_KEY=' + key, content)
with open('.env', 'w') as f:
    f.write(content)
print('  API key saved.')
" "%APIKEY%"

:DONE
echo.
echo  ================================================
echo    Setup complete!
echo    Double-click "Start Town.bat" to launch.
echo  ================================================
echo.
pause
