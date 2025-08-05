@echo off
chcp 65001 >nul
title MEX Trading Bot - Перезапуск
echo ========================================
echo   MEX TRADING BOT - ПЕРЕЗАПУСК
echo ========================================
echo.

echo Остановка всех Python процессов...
taskkill /f /im python.exe >nul 2>&1
if %errorlevel% == 0 (
    echo [OK] Процессы остановлены
) else (
    echo [INFO] Процессы не найдены
)

echo Ожидание 3 секунды...
timeout /t 3 /nobreak >nul

echo Запуск MEX Trading Bot...
python main.py
pause