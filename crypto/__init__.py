"""
Криптомодуль для телеграм-бота
"""

from aiogram import Router

def register_crypto_handlers(dp):
    """
    Регистрирует обработчики для криптомодуля
    
    Args:
        dp: Диспетчер aiogram
    """
    from .handlers import register_crypto_handlers as register_handlers
    register_handlers(dp)

# Инициализация менеджера данных при импорте модуля
from .data_sources.crypto_data_manager import get_data_manager
data_manager = get_data_manager()

__all__ = ['register_crypto_handlers', 'data_manager']