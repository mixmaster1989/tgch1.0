@echo off
chcp 65001 >nul
title MEX Trading Bot - Запуск
echo ========================================
echo    MEX TRADING BOT - ЗАПУСК
echo ========================================
echo.

echo Проверка процессов...
tasklist /fi "imagename eq python.exe" | find "python.exe" >nul
if %errorlevel% == 0 (
    echo [ВНИМАНИЕ] Python процессы уже запущены!
    echo Остановите их перед запуском нового бота.
    pause
    exit /b 1
)

echo Запуск MEX Trading Bot...
python main.py
pause