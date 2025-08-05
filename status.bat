@echo off
chcp 65001 >nul
title MEX Trading Bot - Статус
echo ========================================
echo    MEX TRADING BOT - СТАТУС
echo ========================================
echo.

echo Проверка процессов Python...
tasklist /fi "imagename eq python.exe" /fo table | findstr "python.exe"
if %errorlevel% == 0 (
    echo.
    echo [СТАТУС] Бот ЗАПУЩЕН
) else (
    echo [СТАТУС] Бот ОСТАНОВЛЕН
)

echo.
echo Последние 10 строк лога:
echo ----------------------------------------
if exist "bot.log" (
    powershell -Command "Get-Content bot.log -Tail 10"
) else (
    echo Лог файл не найден
)

echo.
pause