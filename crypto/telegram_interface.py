"""
Интерфейс для взаимодействия с Telegram
Этот модуль обеспечивает совместимость со старым кодом
"""

import logging
from aiogram.types import Message

from .handlers import cmd_crypto_mode

# Получаем логгер для модуля
logger = logging.getLogger('crypto.telegram_interface')

async def cmd_crypto(message: Message):
    """
    Обработчик команды /crypto для совместимости со старым кодом
    Просто перенаправляет на новый обработчик
    
    Args:
        message: Сообщение от пользователя
    """
    logger.info(f"Перенаправление команды /crypto на /crypto_mode для пользователя {message.from_user.id}")
    await cmd_crypto_mode(message)