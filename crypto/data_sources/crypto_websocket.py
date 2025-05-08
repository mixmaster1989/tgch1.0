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
    
    async def start(self, symbols: Optional[List[str]] = None):
        """
        Запускает WebSocket соединение
        
        Args:
            symbols: Список символов монет для отслеживания (по умолчанию основные монеты)
        """
        if self._running:
            logger.warning("WebSocket соединение уже запущено")
            return
        
        if not symbols:
            symbols = ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE"]
        
        self._running = True
        self._task = asyncio.create_task(self._run_websocket(symbols))
        
        logger.info(f"Запущено WebSocket соединение для {len(symbols)} монет")
    
    async def stop(self):
        """
        Останавливает WebSocket соединение
        """
        if not self._running:
            logger.warning("WebSocket соединение не запущено")
            return
        
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        
        logger.info("Остановлено WebSocket соединение")
    
    async def _run_websocket(self, symbols: List[str]):
        """
        Запускает WebSocket соединение с Binance
        
        Args:
            symbols: Список символов монет для отслеживания
        """
        # Формируем строку для подписки на несколько потоков
        streams = [f"{symbol.lower()}usdt@ticker" for symbol in symbols]
        uri = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
        
        reconnect_delay = 1
        max_reconnect_delay = 60
        
        while self._running:
            try:
                async with websockets.connect(uri) as websocket:
                    logger.info("Установлено WebSocket соединение с Binance")
                    reconnect_delay = 1  # Сбрасываем задержку при успешном подключении
                    
                    while self._running:
                        try:
                            message = await websocket.recv()
                            await self._process_message(message)
                        except websockets.ConnectionClosed:
                            logger.warning("WebSocket соединение закрыто")
                            break
            except Exception as e:
                logger.error(f"Ошибка WebSocket соединения: {e}")
            
            if self._running:
                logger.info(f"Переподключение через {reconnect_delay} секунд...")
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
    
    async def _process_message(self, message: str):
        """
        Обрабатывает сообщение от WebSocket
        
        Args:
            message: JSON-строка с данными
        """
        try:
            data = json.loads(message)
            
            # Проверяем формат данных Binance
            if 'data' in data:
                ticker_data = data['data']
                symbol = ticker_data.get('s', '').replace('USDT', '')
                
                if symbol:
                    # Извлекаем нужные данные
                    price = float(ticker_data.get('c', 0))  # Текущая цена
                    price_change = float(ticker_data.get('p', 0))  # Изменение цены за 24 часа
                    price_change_percent = float(ticker_data.get('P', 0))  # Процент изменения за 24 часа
                    volume = float(ticker_data.get('v', 0))  # Объем за 24 часа
                    high = float(ticker_data.get('h', 0))  # Максимальная цена за 24 часа
                    low = float(ticker_data.get('l', 0))  # Минимальная цена за 24 часа
                    
                    # Сохраняем данные
                    self._price_data[symbol] = {
                        'price': price,
                        'price_change': price_change,
                        'price_change_percent': price_change_percent,
                        'volume': volume,
                        'high': high,
                        'low': low,
                        'timestamp': datetime.now()
                    }
                    
                    # Уведомляем подписчиков
                    await self._notify_subscribers(symbol, self._price_data[symbol])
        except json.JSONDecodeError:
            logger.error("Ошибка декодирования JSON из WebSocket")
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения WebSocket: {e}")
    
    async def _notify_subscribers(self, symbol: str, data: Dict[str, Any]):
        """
        Уведомляет подписчиков об обновлении данных
        
        Args:
            symbol: Символ монеты
            data: Данные о монете
        """
        for subscriber in self._subscribers:
            try:
                await subscriber(symbol, data)
            except Exception as e:
                logger.error(f"Ошибка при уведомлении подписчика: {e}")
    
    def subscribe(self, callback: Callable[[str, Dict[str, Any]], None]):
        """
        Подписывает функцию на обновления данных
        
        Args:
            callback: Функция обратного вызова, принимающая символ и данные
        """
        self._subscribers.add(callback)
    
    def unsubscribe(self, callback: Callable[[str, Dict[str, Any]], None]):
        """
        Отписывает функцию от обновлений данных
        
        Args:
            callback: Функция обратного вызова для отписки
        """
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def get_price_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Получает последние данные о цене монеты
        
        Args:
            symbol: Символ монеты
            
        Returns:
            Optional[Dict[str, Any]]: Данные о цене или None, если данных нет
        """
        return self._price_data.get(symbol)
    
    def get_all_price_data(self) -> Dict[str, Dict[str, Any]]:
        """
        Получает все данные о ценах
        
        Returns:
            Dict[str, Dict[str, Any]]: Словарь с данными о ценах
        """
        return self._price_data.copy()

# Создаем глобальный экземпляр WebSocket клиента
_websocket = CryptoWebSocket()

def get_websocket() -> CryptoWebSocket:
    """
    Получает глобальный экземпляр WebSocket клиента
    
    Returns:
        CryptoWebSocket: Глобальный экземпляр WebSocket клиента
    """
    return _websocket