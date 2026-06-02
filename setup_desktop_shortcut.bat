@echo off
title OnBrandCraftz Dashboard — Desktop Shortcut Setup
echo.
echo  Setting up OnBrandCraftz Dashboard desktop shortcut...
echo.

:: Find the pythonw.exe path
for /f "delims=" %%i in ('where pythonw.exe 2^>nul') do set PYTHONW=%%i
if "%PYTHONW%"=="" (
    for /f "delims=" %%i in ('where python.exe 2^>nul') do set PYTHONW=%%i
)
if "%PYTHONW%"=="" (
    echo  ERROR: Python not found in PATH. Please install Python and try again.
    pause
    exit /b 1
)

:: Replace python.exe with pythonw.exe if needed
set PYTHONW=%PYTHONW:python.exe=pythonw.exe%

set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
set SCRIPT=%SCRIPT_DIR%\launch_dashboard.pyw
set ICON=%SCRIPT_DIR%\data\brand\dashboard_icon.ico
set SHORTCUT=%USERPROFILE%\Desktop\OnBrandCraftz Dashboard.lnk

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ws = New-Object -ComObject WScript.Shell; ^
   $sc = $ws.CreateShortcut('%SHORTCUT%'); ^
   $sc.TargetPath = '%PYTHONW%'; ^
   $sc.Arguments = '\""%SCRIPT%\"\"'; ^
   $sc.WorkingDirectory = '%SCRIPT_DIR%'; ^
   $sc.IconLocation = '%ICON%'; ^
   $sc.Description = 'Open OnBrandCraftz Dashboard'; ^
   $sc.Save()"

if exist "%SHORTCUT%" (
    echo  Done! Shortcut created on your Desktop.
    echo  Double-click "OnBrandCraftz Dashboard" to open the dashboard anytime.
    echo.
    echo  The dashboard will auto-refresh from Etsy each time you open it.
) else (
    echo  ERROR: Shortcut could not be created. Check that Desktop path is accessible.
)

echo.
pause
