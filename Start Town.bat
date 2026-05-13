@echo off
title OnBrandCraftz Town
cd /d "%~dp0"

echo.
echo  ================================================
echo    OnBrandCraftz Town  ^|  Starting up...
echo  ================================================
echo.

REM ── Check Python is installed ──────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found.
    echo  Download and install Python 3.10+ from:
    echo  https://www.python.org/downloads/
    echo  Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

REM ── Activate virtual environment if it exists ──────
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else (
    echo  No virtual environment found - run Setup.bat first.
    echo.
    pause
    exit /b 1
)

REM ── Check .env file exists ─────────────────────────
if not exist ".env" (
    echo  ERROR: .env file not found!
    echo  Run Setup.bat first to create it.
    echo.
    pause
    exit /b 1
)

echo  All checks passed. Opening town in your browser...
echo  Press Ctrl+C in this window to stop the server.
echo.

python town_app\server.py

pause
