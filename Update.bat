@echo off
title OnBrandCraftz - Update
cd /d "%~dp0"

echo.
echo  ================================================
echo    OnBrandCraftz Town - Update
echo  ================================================
echo.

REM -- Try git pull first (fastest) --
git --version >nul 2>&1
if not errorlevel 1 (
    if exist ".git" (
        echo  Git found - pulling latest code...
        git fetch origin
        git checkout claude/etsy-automation-agents-WFAPU >nul 2>&1
        git pull origin claude/etsy-automation-agents-WFAPU
        if not errorlevel 1 (
            echo.
            echo  Update complete via git.
            goto INSTALL
        )
        echo  Git pull failed - falling back to ZIP download...
    ) else (
        echo  No .git folder found - using ZIP download...
    )
) else (
    echo  Git not installed - using ZIP download...
)
echo.

REM -- ZIP download fallback (no git needed) --
set ZIP_URL=https://github.com/printing3dthings-afk/Etsy/archive/refs/heads/claude/etsy-automation-agents-WFAPU.zip
set ZIP_FILE=%TEMP%\onbrandcraftz_update.zip
set EXTRACT_DIR=%TEMP%\onbrandcraftz_update

echo  Downloading latest code from GitHub...
powershell -Command "Invoke-WebRequest -Uri '%ZIP_URL%' -OutFile '%ZIP_FILE%' -UseBasicParsing"
if errorlevel 1 (
    echo.
    echo  ERROR: Download failed. Check your internet connection.
    echo  If the repo is private, log into GitHub first then retry.
    pause
    exit /b 1
)
echo  Download complete.
echo.

echo  Extracting...
if exist "%EXTRACT_DIR%" rmdir /s /q "%EXTRACT_DIR%"
powershell -Command "Expand-Archive -Path '%ZIP_FILE%' -DestinationPath '%EXTRACT_DIR%' -Force"
if errorlevel 1 (
    echo  ERROR: Extraction failed.
    pause
    exit /b 1
)

REM -- Find the extracted folder --
for /d %%D in ("%EXTRACT_DIR%\*") do set SOURCE_DIR=%%D

echo  Copying updated files...
echo  (Your .env and data files are kept as-is)
echo.

REM -- Copy everything except .env and data/ --
robocopy "%SOURCE_DIR%" "%~dp0" /E /XF ".env" /XD "data" "__pycache__" ".git" /NFL /NDL /NJH /NJS >nul

REM -- Clean up temp files --
del "%ZIP_FILE%" >nul 2>&1
rmdir /s /q "%EXTRACT_DIR%" >nul 2>&1

echo  Files updated successfully.

REM -- Install / update packages --
:INSTALL
echo.
echo  Installing/updating packages...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo  WARNING: Some packages may not have installed.
    echo  Try running: pip install -r requirements.txt
)
echo  Packages OK.
echo.

echo  ================================================
echo    Update complete!
echo    Run "Start Town.bat" to launch.
echo  ================================================
echo.
pause
