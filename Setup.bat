@echo off
title OnBrandCraftz - First Time Setup
cd /d "%~dp0"

echo.
echo  ================================================
echo    OnBrandCraftz - First Time Setup
echo  ================================================
echo.

REM ── Check Python ───────────────────────────────────
echo  [1/4] Checking Python...
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
echo  [2/4] Creating virtual environment...
if exist ".venv" (
    echo  Virtual environment already exists, skipping.
) else (
    python -m venv .venv
    echo  Done.
)
echo.

REM ── Activate and install packages ─────────────────
echo  [3/4] Installing packages (this may take a minute)...
call .venv\Scripts\activate.bat
pip install -r requirements.txt --quiet
echo  Done.
echo.

REM ── Create .env file ───────────────────────────────
echo  [4/4] Setting up .env file...
if exist ".env" (
    echo  .env already exists, skipping.
) else (
    copy .env.example .env >nul
    echo  Created .env from template.
)
echo.

echo  ================================================
echo    Setup complete!
echo  ================================================
echo.
echo  IMPORTANT: You must add your API key before running.
echo.
echo  Opening your .env file now - paste your
echo  ANTHROPIC_API_KEY value after the = sign, then
echo  save and close the file.
echo.
echo  Get your key at: console.anthropic.com
echo.
pause

notepad .env

echo.
echo  All done! Double-click "Start Town.bat" to launch.
echo.
pause
