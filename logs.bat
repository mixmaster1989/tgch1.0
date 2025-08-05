@echo off
chcp 65001 >nul
title MEX Trading Bot - Логи в реальном времени
echo ========================================
echo  MEX TRADING BOT - ЛОГИ РЕАЛЬНОГО ВРЕМЕНИ
echo ========================================
echo.

if not exist "bot.log" (
    echo [ОШИБКА] Файл bot.log не найден!
    echo Запустите сначала бота.
    pause
    exit /b 1
)

echo Показ логов в реальном времени...
echo Нажмите Ctrl+C для выхода
echo.
powershell -Command "Get-Content bot.log -Wait -Tail 20"