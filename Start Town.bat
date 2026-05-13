@echo off
title OnBrandCraftz Town
cd /d "%~dp0"

echo.
echo  ================================================
echo    OnBrandCraftz Town - Starting...
echo  ================================================
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
python -c "from dotenv import dotenv_values; v=dotenv_values('.env'); exit(0 if str(v.get('ANTHROPIC_API_KEY','')).startswith('sk-') else 1)" 2>nul
if errorlevel 1 (
    echo  ERROR: ANTHROPIC_API_KEY not set in .env
    echo  Run Setup.bat to add your API key.
    pause
    exit /b 1
)

REM ── Check fastapi/uvicorn installed ───────────────
python -c "import fastapi, uvicorn" >nul 2>&1
if errorlevel 1 (
    echo  Installing missing packages...
    pip install fastapi "uvicorn[standard]" --quiet
)

echo  All checks passed.
echo  Your browser will open automatically.
echo  Keep this window open. Press Ctrl+C to stop.
echo.

python town_app\server.py

pause
