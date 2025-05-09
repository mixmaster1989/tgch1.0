"""
Модуль для кэширования данных о криптовалютах
"""

import time
import logging
import json
from typing import Dict, Any, Optional, Callable, TypeVar, Awaitable
from datetime import datetime, timedelta
from functools import wraps

# Получаем логгер для модуля
logger = logging.getLogger('crypto.data_sources.crypto_cache')

# Тип для кэшируемых данных
T = TypeVar('T')

# Глобальная переменная для хранения экземпляра кэша
_cache_instance = None

def get_cache_instance():
    """
    Получает глобальный экземпляр кэша
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = CryptoCache()
    return _cache_instance

def cached(ttl: int = 3600):
    """
    Декоратор для кэширования результатов функций
    
    Args:
        ttl: Время жизни кэша в секундах
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Получаем экземпляр кэша
            cache = get_cache_instance()
            
            # Формируем ключ кэша на основе имени функции и аргументов
            key = f"{func.__module__}.{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Проверяем, есть ли данные в кэше
            cached_result = cache.get(key)
            if cached_result is not None:
                logger.debug(f"Используем кэшированные данные для {key}")
                return cached_result
            
            # Выполняем оригинальную функцию
            result = await func(*args, **kwargs)
            
            # Сохраняем результат в кэше
            if result is not None:
                cache.set(key, result, ttl=ttl)
                logger.debug(f"Сохранены данные в кэше для {key} на {ttl} секунд")
            
            return result
        return wrapper
    return decorator

class CryptoCache:
    """
    Класс для кэширования данных о криптовалютах
    """
    
    def __init__(self):
        """
        Инициализирует кэш
        """
        # Словарь для хранения кэшированных данных
        # Формат: {key: {'data': data, 'expires': timestamp}}
        self._cache = {}
        
        logger.info("Инициализирован кэш для данных о криптовалютах")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Получает данные из кэша
        
        Args:
            key: Ключ для поиска в кэше
            
        Returns:
            Any: Данные из кэша или None, если данные не найдены или устарели
        """
        if key not in self._cache:
            return None
        
        cache_entry = self._cache[key]
        
        # Проверяем, не устарели ли данные
        if cache_entry['expires'] < time.time():
            # Удаляем устаревшие данные
            del self._cache[key]
            return None
        
        return cache_entry['data']
    
    def set(self, key: str, data: Any, ttl: int = 3600):
        """
        Сохраняет данные в кэш
        
        Args:
            key: Ключ для сохранения в кэше
            data: Данные для сохранения
            ttl: Время жизни данных в секундах (по умолчанию 1 час)
        """
        expires = time.time() + ttl
        
        self._cache[key] = {
            'data': data,
            'expires': expires
        }
    
    def invalidate(self, key: str):
        """
        Инвалидирует данные в кэше
        
        Args:
            key: Ключ для инвалидации
        """
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """
        Очищает весь кэш
        """
        self._cache.clear()
    
    def cleanup(self):
        """
        Удаляет устаревшие данные из кэша
        """
        current_time = time.time()
        keys_to_delete = []
        
        for key, cache_entry in self._cache.items():
            if cache_entry['expires'] < current_time:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self._cache[key]
        
        logger.debug(f"Очищено {len(keys_to_delete)} устаревших записей из кэша")

# Создаем глобальный экземпляр кэша
_cache = CryptoCache()

def get_cache() -> CryptoCache:
    """
    Получает глобальный экземпляр кэша
    
    Returns:
        CryptoCache: Глобальный экземпляр кэша
    """
    return _cache

