import asyncio
import os
from aiogram import Bot, Dispatcher
from handlers import register_handlers
from dotenv import load_dotenv

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

bot = Bot(token=TOKEN)
dp = Dispatcher()

register_handlers(dp)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())