import asyncio
from aiogram import Bot, Dispatcher
from handlers import register_handlers
import os

TOKEN = os.getenv("TG_BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

register_handlers(dp)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())