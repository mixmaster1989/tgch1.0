@echo off
chcp 65001 >nul
title MEX Trading Bot - GUI Manager
echo ========================================
echo   MEX TRADING BOT - GUI MANAGER
echo ========================================
echo.

cd /d "%~dp0"

if exist "MEX_Trading_Bot_Manager.exe" (
    echo Starting GUI Manager...
    start MEX_Trading_Bot_Manager.exe
) else (
    echo EXE file not found. Running via Python...
    python gui_manager.py
)

echo.
pause