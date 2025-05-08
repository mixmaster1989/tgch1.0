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

def cached(ttl: int = 3600):
    """
    Декоратор для кэширования результатов функций
    
    Args:
        ttl: Время жизни данных в секундах (по умолчанию 1 час)
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Создаем ключ на основе имени функции и аргументов
            cache_key = f"{func.__name__}:{hash(str(args))}-{hash(str(kwargs))}"
            
            # Проверяем кэш
            cache = get_cache()
            cached_result = cache.get(cache_key)
            
            if cached_result is not None:
                logger.debug(f"Возвращен результат из кэша для {func.__name__}")
                return cached_result
            
            # Если данных нет в кэше, вызываем функцию
            result = await func(*args, **kwargs)
            
            # Сохраняем результат в кэш
            cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator