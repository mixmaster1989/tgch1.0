import os
import yaml
from telegram.ext import Application
from dotenv import load_dotenv  # Добавлен импорт для загрузки .env

# Загрузка переменных окружения из .env или .env.local файла
load_dotenv()
load_dotenv('.env.local')  # Добавлена поддержка локального файла с секретами

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
    sm_analyzer = SmartMoneyAnalyzer()
    mexc_ws = MEXCWebSocket()
    signal_formatter = SignalFormatter()
    levels_calculator = LevelsCalculator()
    
    # Создание и запуск бота
    application = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    # Здесь будет реализация обработчиков команд
    
    print("Бот запущен и готов к работе!")
    return application

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())