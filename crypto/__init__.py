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

__all__ = ['register_crypto_handlers']