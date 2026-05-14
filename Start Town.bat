@echo off
title OnBrandCraftz Town
cd /d "%~dp0"

echo.
echo  ================================================
echo    OnBrandCraftz Town - Starting...
echo  ================================================
echo.

REM ── Pull latest code from git ─────────────────────
git --version >nul 2>&1
if not errorlevel 1 (
    echo  Checking for updates...
    git pull --ff-only >nul 2>&1
    if not errorlevel 1 (
        echo  Code is up to date.
    ) else (
        echo  Could not auto-update (local changes present or no network).
        echo  Continuing with current version...
    )
) else (
    echo  Git not found - skipping update check.
)
echo.

REM ── Check Python ──────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found. Run Setup.bat first.
    pause
    exit /b 1
)

REM ── Check .env exists ─────────────────────────────
if not exist ".env" (
    echo  ERROR: .env file not found. Run Setup.bat first.
    pause
    exit /b 1
)

REM ── Check API key is set ──────────────────────────
powershell -Command "if ((Get-Content .env | Select-String 'ANTHROPIC_API_KEY=sk-').Count -gt 0) { exit 0 } else { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo  ERROR: ANTHROPIC_API_KEY not set in .env
    echo  Run Setup.bat to add your API key.
    pause
    exit /b 1
)

REM ── Install / update packages ─────────────────────
echo  Installing/updating packages from requirements.txt...
pip install -r requirements.txt --quiet
echo  Packages OK.
echo.

echo  All checks passed.
echo  Opening browser to http://localhost:8080
echo  Keep this window open. Press Ctrl+C to stop.
echo.

start "" http://localhost:8080
python town_app\server.py

pause
