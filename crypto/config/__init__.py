"""
Пакет для работы с конфигурацией
"""

import logging
from typing import Any, Optional  # Убедимся, что импорт в самом начале

logger = logging.getLogger('crypto.config.__init__')

# Попытаемся импортировать функции из config
try:
    from .config import get_config, get_cryptorank_api_key
    logger.info("Успешно импортированы функции из config")
    __all__ = ['get_config', 'get_cryptorank_api_key']
except Exception as e:
    logger.error(f"Ошибка при импорте из config: {e}")
    # Определим заглушки, если импорт не удался
    def get_config() -> None:
        raise ImportError("Не удалось загрузить конфигурацию")
    
    def get_cryptorank_api_key() -> str:
        raise ImportError("Не удалось получить API-ключ Cryptorank")
    
    __all__ = []
