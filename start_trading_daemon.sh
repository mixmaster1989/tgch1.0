#!/bin/bash
"""
Скрипт запуска торгового бота в фоновом режиме
Бот будет работать даже после закрытия SSH сессии
"""

# Настройки
BOT_NAME="mexca_trading_bot"
LOG_DIR="logs"
LOG_FILE="trading_bot.log"
PID_FILE="trading_bot.pid"
PYTHON_SCRIPT="run_auto_trader.py"

echo "🚀 ЗАПУСК ТОРГОВОГО БОТА В ФОНОВОМ РЕЖИМЕ"
echo "=========================================="

# Проверяем, не запущен ли уже бот
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "❌ Бот уже запущен с PID: $PID"
        echo "Для остановки: ./stop_trading_daemon.sh"
        exit 1
    else
        echo "⚠️ Найден старый PID файл, удаляем..."
        rm -f "$PID_FILE"
    fi
fi

# Создаем директорию для логов если её нет
mkdir -p "$LOG_DIR"

# Запускаем бота в фоновом режиме с nohup
echo "📈 Запуск торгового бота..."
nohup python3 "$PYTHON_SCRIPT" > "$LOG_DIR/$LOG_FILE" 2>&1 &

# Сохраняем PID
echo $! > "$PID_FILE"
PID=$(cat "$PID_FILE")

echo "✅ Бот запущен с PID: $PID"
echo "📁 Логи: $LOG_DIR/$LOG_FILE"
echo "🆔 PID файл: $PID_FILE"
echo ""
echo "📱 Проверяйте Telegram для уведомлений!"
echo ""
echo "🔧 Команды управления:"
echo "  Остановка: ./stop_trading_daemon.sh"
echo "  Статус: ./status_trading_daemon.sh"
echo "  Логи: tail -f $LOG_DIR/$LOG_FILE"
echo ""
echo "🌙 Можете выключать ноут - бот продолжит работать!" 

# Обрезаем лог до 100MB, чтобы не разрастался
if [ -x "./scripts/trim_log.sh" ]; then
  ./scripts/trim_log.sh "$LOG_DIR/$LOG_FILE" 104857600 || true
fi 