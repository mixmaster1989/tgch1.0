import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from handlers import register_handlers, set_bot
from handlers_promotion import register_promotion_handlers
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение токена из переменных окружения
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("ОШИБКА: Токен бота не найден!")
    print("Текущие переменные окружения:")
    for key, value in os.environ.items():
        if "TOKEN" in key:
            print(f"{key}: {value[:5]}...")
    raise ValueError("Токен бота не найден. Убедитесь, что файл .env содержит BOT_TOKEN=your_token")

print(f"Токен найден: {TOKEN[:5]}...")

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    
    # Сохраняем экземпляр бота в handlers
    set_bot(bot)
    
    # Регистрация обработчиков
    register_handlers(dp)
    register_promotion_handlers(dp)
    
    # Запуск бота
    print("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен!")
    except Exception as e:
        print(f"Произошла ошибка: {e}")