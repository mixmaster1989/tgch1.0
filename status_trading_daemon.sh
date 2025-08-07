#!/bin/bash
"""
Скрипт проверки статуса торгового бота
"""

PID_FILE="trading_bot.pid"
LOG_FILE="logs/trading_bot.log"

echo "📊 СТАТУС ТОРГОВОГО БОТА"
echo "========================"

# Проверяем PID файл
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "🆔 PID файл: $PID"
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Бот ЗАПУЩЕН (PID: $PID)"
        
        # Показываем информацию о процессе
        echo ""
        echo "📋 Информация о процессе:"
        ps -p $PID -o pid,ppid,cmd,etime,pcpu,pmem
        
        # Показываем последние логи
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo "📝 Последние 10 строк логов:"
            echo "----------------------------------------"
            tail -10 "$LOG_FILE"
            echo "----------------------------------------"
        fi
        
    else
        echo "❌ Бот НЕ ЗАПУЩЕН (процесс не найден)"
        echo "🗑️ Удаляем старый PID файл..."
        rm -f "$PID_FILE"
    fi
else
    echo "❌ PID файл не найден"
fi

echo ""
echo "🔍 Поиск процессов по имени..."
PIDS=$(pgrep -f "run_auto_trader.py")
if [ ! -z "$PIDS" ]; then
    echo "✅ Найдены процессы: $PIDS"
    for pid in $PIDS; do
        echo "  PID $pid: $(ps -p $pid -o cmd --no-headers)"
    done
else
    echo "❌ Процессы не найдены"
fi

echo ""
echo "📱 Проверьте Telegram для актуальных уведомлений" 