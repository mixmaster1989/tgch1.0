@echo off
chcp 65001 >nul
title MEX Trading Bot - Build GUI
echo ========================================
echo   MEX TRADING BOT - BUILD GUI
echo ========================================
echo.

cd /d "%~dp0"

echo Installing PyInstaller...
pip install pyinstaller

echo.
echo Building EXE file...
python "%~dp0build_exe.py"

if exist "MEX_Trading_Bot_Manager.exe" (
    echo.
    echo [OK] EXE file created: MEX_Trading_Bot_Manager.exe
    echo Run it to manage the bot!
) else (
    echo [ERROR] Failed to create EXE file
)

echo.
pause