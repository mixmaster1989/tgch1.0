@echo off
chcp 65001 >nul
title MEX Trading Bot - Установка
echo ========================================
echo   MEX TRADING BOT - УСТАНОВКА
echo ========================================
echo.

echo Проверка Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден!
    echo Установите Python 3.8+ с python.org
    pause
    exit /b 1
)

echo [OK] Python найден
echo.

echo Установка зависимостей...
pip install -r requirements.txt

if %errorlevel% == 0 (
    echo.
    echo [OK] Зависимости установлены
    echo.
    echo Настройте файл .env перед запуском:
    echo 1. Скопируйте .env.example в .env
    echo 2. Заполните API ключи
    echo 3. Запустите start.bat
) else (
    echo [ОШИБКА] Не удалось установить зависимости
)

echo.
pause