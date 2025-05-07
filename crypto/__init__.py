"""
Криптомодуль для анализа Smart Money и отслеживания криптовалютных сигналов.
Работает независимо от основного функционала бота.
"""

import logging
from aiogram import Router, Dispatcher

# Настройка логирования для криптомодуля
logger = logging.getLogger('crypto')
logger.setLevel(logging.INFO)

# Создаем обработчики для файлов логов
file_handler_info = logging.FileHandler('logs/smart_money_info.log')
file_handler_info.setLevel(logging.INFO)

file_handler_error = logging.FileHandler('logs/smart_money_errors.log')
file_handler_error.setLevel(logging.ERROR)

# Форматирование логов
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler_info.setFormatter(formatter)
file_handler_error.setFormatter(formatter)

# Добавляем обработчики к логгеру
logger.addHandler(file_handler_info)
logger.addHandler(file_handler_error)

# Создаем основной роутер для криптомодуля
crypto_router = Router()

def register_crypto_handlers(dp: Dispatcher):
    """
    Регистрирует все обработчики криптомодуля в диспетчере.
    
    Args:
        dp: Экземпляр диспетчера aiogram
    """
    from .handlers import setup_crypto_handlers
    
    # Настраиваем обработчики
    setup_crypto_handlers(crypto_router)
    
    # Подключаем роутер к диспетчеру
    dp.include_router(crypto_router)
    
    logger.info("Криптомодуль успешно инициализирован и подключен")