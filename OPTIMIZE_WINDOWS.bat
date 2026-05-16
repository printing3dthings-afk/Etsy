@echo off
:: ============================================================
::  Windows Laptop Optimizer — Launcher
::  Run as Administrator for full functionality
:: ============================================================

:: Self-elevate to admin if not already
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting administrator rights...
    powershell -Command "Start-Process cmd -ArgumentList '/c, cd /d %~dp0 && %~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

:: Check for Python
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+ and add it to PATH.
    pause
    exit /b 1
)

:: Install psutil if missing
python -c "import psutil" >nul 2>&1
if %errorLevel% neq 0 (
    echo Installing required dependency: psutil ...
    pip install psutil
)

cls
python tools\windows_optimizer.py %*
pause
