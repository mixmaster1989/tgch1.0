import os
import yaml
from telegram.ext import Application
from dotenv import load_dotenv

# Загрузка переменных окружения из .env или .env.local файла
load_dotenv()
load_dotenv('.env.local')

# Загрузка конфигурации
with open('configs/thresholds.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Импорты компонентов
try:
    from analytics.smart_money import SmartMoneyAnalyzer
    from data.websocket_mexc import MEXCWebSocket
    from notification.signal_formatter import SignalFormatter
    from risk.levels_calculator import LevelsCalculator
except ImportError as e:
    print(f"Ошибка импорта: {e}")
    raise

async def main():
    # Проверка .env
    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        raise ValueError("TELEGRAM_BOT_TOKEN не найден в .env")
    
    if not os.getenv('MEXC_API_KEY') or not os.getenv('MEXC_SECRET_KEY'):
        raise ValueError("MEXC API ключи не найдены в .env")
    
    # Инициализация основных компонентов
    try:
        sm_analyzer = SmartMoneyAnalyzer()
        mexc_ws = MEXCWebSocket()
        signal_formatter = SignalFormatter()
        levels_calculator = LevelsCalculator()
    except Exception as e:
        print(f"Ошибка инициализации компонентов: {e}")
        raise
    
    # Создание и запуск бота
    try:
        application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
        print("Бот запущен и готов к работе!")
        return application
    except Exception as e:
        print(f"Ошибка запуска бота: {e}")
        raise

if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем.")
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")