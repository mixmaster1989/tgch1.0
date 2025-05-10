import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Добавляем корневую директорию в PYTHONPATH
import pathlib
sys.path.append(str(pathlib.Path(__file__).parent.parent))

# Загрузка переменных окружения
load_dotenv()

def check_environment():
    """Проверяет наличие необходимых переменных окружения"""
    required_keys = ['BINANCE_API_KEY', 'CRYPTORANK_API_KEY', 'TELEGRAM_BOT_TOKEN']
    for key in required_keys:
        if key not in os.environ:
            raise SystemExit(f"Отсутствует ключ: {key}")

async def main():
    """Основная функция запуска бота"""
    check_environment()
    
    print("[INFO] Бот запущен -", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("[INFO] Инициализация модулей...")
    
    try:
        # Импорты внутри функции для ускорения запуска
        from bot.data.websocket_binance import BinanceWebSocketHandler
        from bot.analytics.smart_money import SmartMoneySignal
        from bot.notification.signal_formatter import format_signal
        
        # Инициализация компонентов
        ws_handler = BinanceWebSocketHandler()
        signal_generator = SmartMoneySignal()
        
        print("[INFO] Все модули успешно инициализированы")
        print("[INFO] Начинаю обработку данных...")
        
        # Запуск обработки сделок
        await ws_handler._process_trades()
        
    except Exception as e:
        print(f"[ERROR] Критическая ошибка: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Запуск основного цикла
    asyncio.run(main())