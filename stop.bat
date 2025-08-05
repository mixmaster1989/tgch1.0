@echo off
chcp 65001 >nul
title MEX Trading Bot - Остановка
echo ========================================
echo   MEX TRADING BOT - ОСТАНОВКА
echo ========================================
echo.

echo Остановка всех Python процессов...
taskkill /f /im python.exe
if %errorlevel% == 0 (
    echo [OK] Бот остановлен
) else (
    echo [INFO] Процессы не найдены
)

echo.
pause