"""
Криптомодуль для телеграм-бота
"""

from aiogram import Router

# Получаем логгер для модуля
logger = logging.getLogger('crypto')

# Создаем роутер для обработчиков
router = Router()

# Импортируем сервисы
from .user_settings.user_preferences import UserPreferences

# Инициализируем сервисы
alert_service = AlertService()
user_preferences = UserPreferences()

# Импортируем менеджер данных после всех импортов
try:
    from .data_sources.crypto_data_manager import get_data_manager
    data_manager = get_data_manager()
    logger.info("Инициализирован менеджер данных о криптовалютах")
except Exception as e:
    logger.error(f"Ошибка при инициализации менеджера данных: {e}")
    data_manager = None


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