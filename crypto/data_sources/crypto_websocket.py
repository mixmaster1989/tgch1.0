"""
Модуль для работы с WebSocket API криптобирж
"""

import json
import logging
import asyncio
import websockets
from typing import Dict, List, Any, Optional, Callable, Set
from datetime import datetime

# Получаем логгер для модуля
logger = logging.getLogger('crypto.data_sources.crypto_websocket')

class CryptoWebSocket:
    """
    Класс для работы с WebSocket API криптобирж
    """
    
    def __init__(self):
        """
        Инициализирует WebSocket клиент
        """
        # Словарь для хранения последних данных о ценах
        # Формат: {symbol: {'price': price, 'timestamp': timestamp, ...}}
        self._price_data = {}
        
        # Множество для хранения подписчиков на обновления
        # Формат: {callback_function}
        self._subscribers = set()
        
        # Флаг для управления работой WebSocket
        self._running = False
        
        # Задача для WebSocket соединения
        self._task = None
        
        logger.info("Инициализирован WebSocket клиент для криптобирж")

        # Создаем экземпляр WebSocket клиента
        self._client = None
        
        # Задача для управления соединением
        self._connection_task = None
        
        # Флаг для отслеживания состояния подключения
        self._connected = False

        # Словарь для хранения подписчиков
        self._subscribers = {}


# Глобальная переменная для хранения экземпляра WebSocket клиента
_websocket_instance = None

def get_websocket():
    """
    Получает глобальный экземпляр WebSocket клиента
    """
    global _websocket_instance
    if _websocket_instance is None:
        _websocket_instance = CryptoWebSocket()
    return _websocket_instance
