@echo off
chcp 65001 >nul
title MEX Trading Bot - Главное меню

:menu
cls
echo ========================================
echo      MEX TRADING BOT - МЕНЮ
echo ========================================
echo.
echo 1. Запуск бота
echo 2. Перезапуск бота  
echo 3. Остановка бота
echo 4. Статус бота
echo 5. Логи в реальном времени
echo 6. Установка зависимостей
echo 7. Выход
echo.
set /p choice="Выберите действие (1-7): "

if "%choice%"=="1" (
    call start.bat
    goto menu
)
if "%choice%"=="2" (
    call restart.bat
    goto menu
)
if "%choice%"=="3" (
    call stop.bat
    goto menu
)
if "%choice%"=="4" (
    call status.bat
    goto menu
)
if "%choice%"=="5" (
    call logs.bat
    goto menu
)
if "%choice%"=="6" (
    call install.bat
    goto menu
)
if "%choice%"=="7" (
    exit
)

echo Неверный выбор!
timeout /t 2 /nobreak >nul
goto menu