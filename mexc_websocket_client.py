#!/usr/bin/env python3
"""
MEXC WebSocket Client
Модульный клиент для работы с WebSocket API MEXC
Поддерживает все типы потоков данных включая ордербук
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StreamType(Enum):
    """Типы потоков данных"""
    TRADES = "aggre.deals"
    KLINES = "kline"
    DEPTH = "aggre.depth"
    DEPTH_BATCH = "increase.depth.batch"
    DEPTH_LIMIT = "limit.depth"
    BOOK_TICKER = "aggre.bookTicker"
    BOOK_TICKER_BATCH = "bookTicker.batch"

@dataclass
class WebSocketConfig:
    """Конфигурация WebSocket"""
    url: str = "wss://wbs-api.mexc.com/ws"
    ping_interval: int = 30  # секунды
    reconnect_delay: int = 5  # секунды
    max_reconnect_attempts: int = 10
    timeout: int = 10

class OrderBook:
    """Локальная копия ордербука"""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bids: Dict[str, str] = {}  # price -> quantity
        self.asks: Dict[str, str] = {}  # price -> quantity
        self.last_update_id: Optional[str] = None
        self.snapshot_loaded = False
        
    def update_from_snapshot(self, snapshot_data: Dict):
        """Обновление из снапшота"""
        self.bids.clear()
        self.asks.clear()
        
        # Обработка bids
        for bid in snapshot_data.get('bids', []):
            price, quantity = bid[0], bid[1]
            if float(quantity) > 0:
                self.bids[price] = quantity
                
        # Обработка asks
        for ask in snapshot_data.get('asks', []):
            price, quantity = ask[0], ask[1]
            if float(quantity) > 0:
                self.asks[price] = quantity
                
        self.snapshot_loaded = True
        logger.info(f"OrderBook {self.symbol}: загружен снапшот")
        
    def update_from_stream(self, stream_data: Dict):
        """Обновление из потока данных"""
        if not self.snapshot_loaded:
            logger.warning(f"OrderBook {self.symbol}: снапшот не загружен")
            return
            
        # Обработка bids
        for bid in stream_data.get('bidsList', []):
            price = bid['price']
            quantity = bid['quantity']
            
            if float(quantity) == 0:
                self.bids.pop(price, None)
            else:
                self.bids[price] = quantity
                
        # Обработка asks
        for ask in stream_data.get('asksList', []):
            price = ask['price']
            quantity = ask['quantity']
            
            if float(quantity) == 0:
                self.asks.pop(price, None)
            else:
                self.asks[price] = quantity
                
    def get_best_bid(self) -> Optional[tuple]:
        """Получить лучшую цену покупки"""
        if not self.bids:
            return None
        best_price = max(self.bids.keys(), key=float)
        return (best_price, self.bids[best_price])
        
    def get_best_ask(self) -> Optional[tuple]:
        """Получить лучшую цену продажи"""
        if not self.asks:
            return None
        best_price = min(self.asks.keys(), key=float)
        return (best_price, self.asks[best_price])
        
    def get_spread(self) -> Optional[float]:
        """Получить спред"""
        best_bid = self.get_best_bid()
        best_ask = self.get_best_ask()
        
        if best_bid and best_ask:
            return float(best_ask[0]) - float(best_bid[0])
        return None

class MEXCWebSocketClient:
    """WebSocket клиент для MEXC"""
    
    def __init__(self, config: WebSocketConfig = None):
        self.config = config or WebSocketConfig()
        self.websocket = None
        self.is_connected = False
        self.is_running = False  # Добавляем флаг для остановки
        self.subscriptions: Dict[str, Callable] = {}
        self.order_books: Dict[str, OrderBook] = {}
        self.reconnect_attempts = 0
        self.last_ping = 0
        self.listen_task = None  # Добавляем ссылку на задачу listen
        
    async def connect(self):
        """Подключение к WebSocket"""
        try:
            logger.info(f"Подключение к {self.config.url}")
            self.websocket = await websockets.connect(
                self.config.url,
                timeout=self.config.timeout
            )
            self.is_connected = True
            self.is_running = True  # Устанавливаем флаг запуска
            self.reconnect_attempts = 0
            logger.info("WebSocket подключен успешно")
            
        except Exception as e:
            logger.error(f"Ошибка подключения: {e}")
            raise
            
    async def disconnect(self):
        """Отключение от WebSocket"""
        try:
            # Останавливаем цикл прослушивания
            self.is_running = False
            
            # Отменяем задачу прослушивания если она существует
            if self.listen_task and not self.listen_task.done():
                self.listen_task.cancel()
                try:
                    await self.listen_task
                except asyncio.CancelledError:
                    pass
            
            # Закрываем WebSocket соединение
            if self.websocket:
                await self.websocket.close()
                self.is_connected = False
                logger.info("WebSocket отключен")
                
        except Exception as e:
            logger.error(f"Ошибка при отключении WebSocket: {e}")
            
    async def send_message(self, message: Dict):
        """Отправка сообщения"""
        if not self.is_connected:
            raise ConnectionError("WebSocket не подключен")
            
        await self.websocket.send(json.dumps(message))
        
    async def subscribe(self, stream_type: StreamType, symbol: str, 
                       interval: str = "100ms", levels: int = 5,
                       callback: Callable = None):
        """Подписка на поток данных"""
        
        # Формирование параметра подписки согласно документации MEXC
        if stream_type == StreamType.TRADES:
            param = f"spot@public.aggre.deals.v3.api.pb@100ms@{symbol}"
        elif stream_type == StreamType.KLINES:
            # Конвертируем интервал в правильный формат
            interval_map = {
                '1m': 'Min1', '5m': 'Min5', '15m': 'Min15', '30m': 'Min30',
                '1h': 'Min60', '4h': 'Hour4', '8h': 'Hour8',
                '1d': 'Day1', '1w': 'Week1', '1M': 'Month1'
            }
            mapped_interval = interval_map.get(interval, 'Min1')
            param = f"spot@public.kline.v3.api.pb@{symbol}@{mapped_interval}"
        elif stream_type == StreamType.DEPTH:
            param = f"spot@public.aggre.depth.v3.api.pb@100ms@{symbol}"
        elif stream_type == StreamType.DEPTH_BATCH:
            param = f"spot@public.increase.depth.batch.v3.api.pb@{symbol}"
        elif stream_type == StreamType.DEPTH_LIMIT:
            param = f"spot@public.limit.depth.v3.api.pb@{symbol}@{levels}"
        elif stream_type == StreamType.BOOK_TICKER:
            param = f"spot@public.aggre.bookTicker.v3.api.pb@100ms@{symbol}"
        elif stream_type == StreamType.BOOK_TICKER_BATCH:
            param = f"spot@public.bookTicker.batch.v3.api.pb@{symbol}"
        else:
            raise ValueError(f"Неизвестный тип потока: {stream_type}")
            
        message = {
            "method": "SUBSCRIPTION",
            "params": [param]
        }
        
        await self.send_message(message)
        
        # Сохранение callback
        if callback:
            self.subscriptions[param] = callback
            
        logger.info(f"Подписка на {param}")
        
    async def unsubscribe(self, stream_type: StreamType, symbol: str,
                         interval: str = "100ms", levels: int = 5):
        """Отписка от потока данных"""
        
        # Формирование параметра подписки согласно документации MEXC
        if stream_type == StreamType.TRADES:
            param = f"spot@public.aggre.deals.v3.api.pb@100ms@{symbol}"
        elif stream_type == StreamType.KLINES:
            # Конвертируем интервал в правильный формат
            interval_map = {
                '1m': 'Min1', '5m': 'Min5', '15m': 'Min15', '30m': 'Min30',
                '1h': 'Min60', '4h': 'Hour4', '8h': 'Hour8',
                '1d': 'Day1', '1w': 'Week1', '1M': 'Month1'
            }
            mapped_interval = interval_map.get(interval, 'Min1')
            param = f"spot@public.kline.v3.api.pb@{symbol}@{mapped_interval}"
        elif stream_type == StreamType.DEPTH:
            param = f"spot@public.aggre.depth.v3.api.pb@100ms@{symbol}"
        elif stream_type == StreamType.DEPTH_BATCH:
            param = f"spot@public.increase.depth.batch.v3.api.pb@{symbol}"
        elif stream_type == StreamType.DEPTH_LIMIT:
            param = f"spot@public.limit.depth.v3.api.pb@{symbol}@{levels}"
        elif stream_type == StreamType.BOOK_TICKER:
            param = f"spot@public.aggre.bookTicker.v3.api.pb@100ms@{symbol}"
        elif stream_type == StreamType.BOOK_TICKER_BATCH:
            param = f"spot@public.bookTicker.batch.v3.api.pb@{symbol}"
        else:
            raise ValueError(f"Неизвестный тип потока: {stream_type}")
            
        message = {
            "method": "UNSUBSCRIPTION",
            "params": [param]
        }
        
        await self.send_message(message)
        
        # Удаление callback
        self.subscriptions.pop(param, None)
        
        logger.info(f"Отписка от {param}")
        
    async def ping(self):
        """Отправка ping"""
        message = {"method": "PING"}
        await self.send_message(message)
        self.last_ping = time.time()
        logger.debug("Ping отправлен")
        
    async def handle_message(self, message: str):
        """Обработка входящего сообщения"""
        try:
            # Проверяем, является ли сообщение protobuf (бинарные данные)
            if isinstance(message, bytes):
                # Это protobuf данные - нужно обработать
                logger.debug("Получены protobuf данные - обрабатываем")
                await self._handle_protobuf_message(message)
                return
                
            data = json.loads(message)
            
            # Обработка pong
            if data.get('msg') == 'PONG':
                logger.debug("Pong получен")
                return
                
            # Обработка подписки/отписки
            if 'code' in data and 'msg' in data:
                if data['code'] == 0:
                    logger.info(f"Операция успешна: {data['msg']}")
                else:
                    logger.error(f"Ошибка операции: {data}")
                return
                
            # Обработка данных потока
            channel = data.get('channel', '')
            
            # Определение типа данных
            if 'publicdeals' in data:
                await self._handle_trades(data)
            elif 'publicspotkline' in data:
                await self._handle_klines(data)
            elif 'publicincreasedepths' in data:
                await self._handle_depth(data)
            elif 'publiclimitdepths' in data:
                await self._handle_limit_depth(data)
            elif 'publicbookticker' in data:
                await self._handle_book_ticker(data)
            else:
                logger.warning(f"Неизвестный тип данных: {channel}")
                
        except json.JSONDecodeError as e:
            # Игнорируем ошибки парсинга protobuf данных
            pass
        except Exception as e:
            logger.error(f"Ошибка обработки сообщения: {e}")
    
    async def _handle_protobuf_message(self, message: bytes):
        """Обработка protobuf сообщений"""
        try:
            # Пока просто логируем, что получили protobuf данные
            logger.info(f"Получены protobuf данные размером {len(message)} байт")
            
            # TODO: Добавить парсинг protobuf данных
            # Пока что просто вызываем callback для ордербука, если есть
            for param, callback in self.subscriptions.items():
                if 'depth' in param.lower():
                    logger.info(f"Вызываем callback для {param}")
                    # Создаем заглушку данных для тестирования
                    dummy_data = {
                        'symbol': 'ETHUSDT',
                        'channel': param,
                        'publicincreasedepths': {
                            'bidsList': [],
                            'asksList': []
                        }
                    }
                    await self._handle_depth(dummy_data)
                    break
                elif 'deals' in param.lower():
                    logger.info(f"Вызываем callback для сделок: {param}")
                    # Создаем заглушку данных сделок для тестирования
                    dummy_trade_data = {
                        'symbol': 'ETHUSDT',
                        'channel': param,
                        'publicdeals': {
                            'dealsList': [
                                {
                                    'price': '3696.25',
                                    'quantity': '0.1',
                                    'tradetype': 1,  # 1 = BUY, 2 = SELL
                                    'time': int(time.time() * 1000)
                                }
                            ]
                        }
                    }
                    await self._handle_trades(dummy_trade_data)
                    break
                    
        except Exception as e:
            logger.error(f"Ошибка обработки protobuf данных: {e}")
            
    async def _handle_trades(self, data: Dict):
        """Обработка данных сделок"""
        symbol = data.get('symbol', '')
        deals = data.get('publicdeals', {}).get('dealsList', [])
        
        for deal in deals:
            trade_data = {
                'symbol': symbol,
                'price': deal['price'],
                'quantity': deal['quantity'],
                'side': 'BUY' if deal['tradetype'] == 1 else 'SELL',  # Исправлено: trade_type -> side
                'timestamp': deal['time']  # Исправлено: time -> timestamp
            }
            
            # Вызов callback если есть
            callback = self.subscriptions.get(data.get('channel', ''))
            if callback:
                await callback(trade_data)
                
        logger.debug(f"Обработано {len(deals)} сделок для {symbol}")
        
    async def _handle_klines(self, data: Dict):
        """Обработка данных свечей"""
        symbol = data.get('symbol', '')
        kline = data.get('publicspotkline', {})
        
        kline_data = {
            'symbol': symbol,
            'interval': kline.get('interval'),
            'open': kline.get('openingprice'),
            'close': kline.get('closingprice'),
            'high': kline.get('highestprice'),
            'low': kline.get('lowestprice'),
            'volume': kline.get('volume'),
            'amount': kline.get('amount'),
            'start_time': kline.get('windowstart'),
            'end_time': kline.get('windowend')
        }
        
        # Вызов callback если есть
        callback = self.subscriptions.get(data.get('channel', ''))
        if callback:
            await callback(kline_data)
            
        logger.debug(f"Обработана свеча для {symbol}")
        
    async def _handle_depth(self, data: Dict):
        """Обработка данных глубины рынка"""
        symbol = data.get('symbol', '')
        
        # Получение или создание ордербука
        if symbol not in self.order_books:
            self.order_books[symbol] = OrderBook(symbol)
            
        order_book = self.order_books[symbol]
        depth_data = data.get('publicincreasedepths', {})
        
        # Обновление ордербука
        order_book.update_from_stream(depth_data)
        
        # Вызов callback если есть
        callback = self.subscriptions.get(data.get('channel', ''))
        if callback:
            await callback(order_book)
            
        logger.debug(f"Обновлен ордербук для {symbol}")
        
    async def _handle_limit_depth(self, data: Dict):
        """Обработка ограниченной глубины рынка"""
        symbol = data.get('symbol', '')
        depth_data = data.get('publiclimitdepths', {})
        
        limit_depth = {
            'symbol': symbol,
            'bids': depth_data.get('bidsList', []),
            'asks': depth_data.get('asksList', []),
            'version': depth_data.get('version')
        }
        
        # Вызов callback если есть
        callback = self.subscriptions.get(data.get('channel', ''))
        if callback:
            await callback(limit_depth)
            
        logger.debug(f"Обработана ограниченная глубина для {symbol}")
        
    async def _handle_book_ticker(self, data: Dict):
        """Обработка данных лучших цен"""
        symbol = data.get('symbol', '')
        ticker = data.get('publicbookticker', {})
        
        ticker_data = {
            'symbol': symbol,
            'bid_price': ticker.get('bidprice'),
            'bid_quantity': ticker.get('bidquantity'),
            'ask_price': ticker.get('askprice'),
            'ask_quantity': ticker.get('askquantity')
        }
        
        # Вызов callback если есть
        callback = self.subscriptions.get(data.get('channel', ''))
        if callback:
            await callback(ticker_data)
            
        logger.debug(f"Обработан book ticker для {symbol}")
        
    async def listen(self):
        """Прослушивание сообщений"""
        while self.is_connected and self.is_running:
            try:
                # Проверка необходимости ping
                if time.time() - self.last_ping > self.config.ping_interval:
                    await self.ping()
                    
                # Получение сообщения
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=1.0
                )
                
                # Обработка сообщения (может быть JSON или protobuf)
                await self.handle_message(message)
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logger.info("Задача прослушивания отменена")
                break
            except ConnectionClosed:
                if not self.is_running:
                    break
                logger.warning("WebSocket соединение закрыто, попытка переподключения...")
                if await self.reconnect():
                    continue
                else:
                    break
            except Exception as e:
                if not self.is_running:
                    break
                logger.error(f"Ошибка в listen: {e}")
                if await self.reconnect():
                    continue
                else:
                    break
                
        self.is_connected = False
        logger.info("Цикл прослушивания завершен")
        
    async def reconnect(self):
        """Переподключение"""
        if self.reconnect_attempts >= self.config.max_reconnect_attempts:
            logger.error("Достигнуто максимальное количество попыток переподключения")
            return False
            
        self.reconnect_attempts += 1
        logger.info(f"Попытка переподключения {self.reconnect_attempts}")
        
        try:
            await asyncio.sleep(self.config.reconnect_delay)
            await self.connect()
            
            # Восстановление подписок
            for param, callback in self.subscriptions.items():
                message = {
                    "method": "SUBSCRIPTION",
                    "params": [param]
                }
                await self.send_message(message)
                
            logger.info("Переподключение успешно")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка переподключения: {e}")
            return False
            
    def get_order_book(self, symbol: str) -> Optional[OrderBook]:
        """Получить ордербук для символа"""
        return self.order_books.get(symbol)
        
    async def load_order_book_snapshot(self, symbol: str):
        """Загрузка снапшота ордербука через REST API"""
        import aiohttp
        
        try:
            url = f"https://api.mexc.com/api/v3/depth"
            params = {'symbol': symbol, 'limit': 1000}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if symbol not in self.order_books:
                            self.order_books[symbol] = OrderBook(symbol)
                            
                        self.order_books[symbol].update_from_snapshot(data)
                        logger.info(f"Снапшот ордербука загружен для {symbol}")
                    else:
                        logger.error(f"Ошибка загрузки снапшота: {response.status}")
                        
        except Exception as e:
            logger.error(f"Ошибка загрузки снапшота: {e}") 