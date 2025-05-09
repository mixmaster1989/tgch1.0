import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from handlers import register_handlers, set_bot
from handlers_promotion import register_promotion_handlers
from crypto import register_crypto_handlers
from crypto.main_menu import register_crypto_menu_handlers
from aiogram.filters import Command  # Импортируем Command для фильтрации команд
from aiogram.types import Message, types  # Добавляем импорт типов сообщений
import logging

# Настройка более подробного логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
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

async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=TOKEN)
    dp = Dispatcher()

    # Сохраняем экземпляр бота в handlers и других модулях
    set_bot(bot)

    # Регистрация обработчиков
    register_handlers(dp)
    register_promotion_handlers(dp)

    # Добавляем обработчики для криптомодуля
    from crypto.handlers import register_crypto_handlers
    from crypto.main_menu import register_crypto_menu_handlers

    # Регистрация обработчиков криптомодуля
    register_crypto_handlers(dp)
    register_crypto_menu_handlers(dp)

    # Добавляем обработчик для команды /crypto
    @dp.message(Command("crypto"))
    async def crypto_command(message: types.Message):
        """Обработчик команды /crypto для всех пользователей"""
        # Имитируем вызов криптомодуля
        from crypto.handlers import cmd_crypto_mode
        await cmd_crypto_mode(message)

    # Добавляем обработчик для команды /crypto_mode
    @dp.message(Command("crypto_mode"))
    async def crypto_mode_command(message: types.Message):
        """Обработчик команды /crypto_mode для всех пользователей"""
        # Имитируем вызов криптомодуля
        from crypto.handlers import cmd_crypto_mode
        await cmd_crypto_mode(message)

    # Добавляем обработчик для кнопки "🪙 Криптомодуль"
    @dp.message(F.text == "🪙 Криптомодуль")
    async def crypto_module(message: types.Message):
        """Переход в криптомодуль через кнопку"""
        from crypto.handlers import cmd_crypto_mode
        await cmd_crypto_mode(message)

    # Регистрация обработчиков криптомодуля
    register_crypto_handlers(dp)
    register_crypto_menu_handlers(dp)

    # Устанавливаем экземпляр бота для криптомодуля
    from crypto.handlers import set_bot as crypto_set_bot
    from crypto.main_menu import set_bot as crypto_menu_set_bot
    from crypto.signal_dispatcher import SignalDispatcher

    crypto_set_bot(bot)
    crypto_menu_set_bot(bot)

    # Инициализируем диспетчер сигналов
    signal_dispatcher = SignalDispatcher()
    signal_dispatcher.set_bot(bot)
    await signal_dispatcher.start()

    # Инициализируем менеджер данных
    from crypto.data_sources.crypto_data_manager import get_data_manager
    data_manager = get_data_manager()
    await data_manager.start()

    # Инициализируем сервис уведомлений
    from crypto.notification.alert_service import AlertService
    alert_service = AlertService()
    alert_service.set_bot(bot)
    asyncio.create_task(alert_service.start_monitoring())

    # Запуск бота
    logger = logging.getLogger(__name__)
    logger.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен!")
    except Exception as e:
        logger.error(f"Произошла ошибка: {e}", exc_info=True)
