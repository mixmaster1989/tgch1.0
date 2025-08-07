#!/bin/bash
"""
Скрипт остановки торгового бота
"""

PID_FILE="trading_bot.pid"

echo "🛑 ОСТАНОВКА ТОРГОВОГО БОТА"
echo "============================"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "📋 Найден PID: $PID"
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "🔄 Остановка процесса..."
        kill $PID
        
        # Ждем завершения
        sleep 2
        
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️ Процесс не остановился, принудительная остановка..."
            kill -9 $PID
        fi
        
        echo "✅ Бот остановлен"
    else
        echo "⚠️ Процесс уже не запущен"
    fi
    
    # Удаляем PID файл
    rm -f "$PID_FILE"
    echo "🗑️ PID файл удален"
    
else
    echo "❌ PID файл не найден"
    echo "Попытка найти процесс по имени..."
    
    # Ищем процесс по имени
    PIDS=$(pgrep -f "run_auto_trader.py")
    if [ ! -z "$PIDS" ]; then
        echo "🔍 Найдены процессы: $PIDS"
        for pid in $PIDS; do
            echo "🔄 Остановка процесса $pid..."
            kill $pid
        done
        echo "✅ Все процессы остановлены"
    else
        echo "❌ Процессы не найдены"
    fi
fi

echo ""
echo "📊 Проверьте Telegram для финального отчета" 