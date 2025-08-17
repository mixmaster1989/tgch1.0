#!/usr/bin/env python3
"""
Тест улучшения стабильности WebSocket соединений
"""

import asyncio
import websockets
import json
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StableWebSocketClient:
    def __init__(self):
        self.websocket = None
        self.is_connected = False
        self.last_ping = 0
        self.ping_interval = 30  # секунды
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 5  # секунды
        self.subscriptions = {}
        
    async def connect(self):
        """Подключение с улучшенной обработкой ошибок"""
        try:
            logger.info("🔌 Подключение к WebSocket...")
            self.websocket = await websockets.connect(
                "wss://wbs-api.mexc.com/ws",
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10,
                max_size=2**20,  # 1MB
                compression=None
            )
            self.is_connected = True
            self.reconnect_attempts = 0
            logger.info("✅ WebSocket подключен успешно")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения: {e}")
            return False
            
    async def disconnect(self):
        """Отключение"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("🔌 WebSocket отключен")
            
    async def send_message(self, message):
        """Отправка сообщения с проверкой соединения"""
        if not self.is_connected or not self.websocket:
            logger.warning("WebSocket не подключен")
            return False
            
        try:
            await self.websocket.send(json.dumps(message))
            return True
        except Exception as e:
            logger.error(f"Ошибка отправки: {e}")
            return False
            
    async def subscribe(self, symbol: str):
        """Подписка на символ с правильными форматами"""
        subscriptions = [
            {
                "method": "SUBSCRIPTION",
                "params": [f"spot@public.aggre.deals.v3.api.pb@100ms@{symbol}"]
            },
            {
                "method": "SUBSCRIPTION", 
                "params": [f"spot@public.kline.v3.api.pb@{symbol}@Min1"]
            },
            {
                "method": "SUBSCRIPTION",
                "params": [f"spot@public.aggre.depth.v3.api.pb@100ms@{symbol}"]
            }
        ]
        
        for sub in subscriptions:
            success = await self.send_message(sub)
            if success:
                logger.info(f"✅ Подписка: {sub['params'][0]}")
            else:
                logger.error(f"❌ Ошибка подписки: {sub['params'][0]}")
                
    async def ping(self):
        """Отправка ping"""
        if time.time() - self.last_ping > self.ping_interval:
            await self.send_message({"method": "PING"})
            self.last_ping = time.time()
            logger.debug("🏓 Ping отправлен")
            
    async def listen(self, duration: int = 60):
        """Прослушивание с улучшенной стабильностью"""
        start_time = time.time()
        message_count = 0
        
        logger.info(f"🎧 Начинаем прослушивание на {duration} секунд...")
        
        while time.time() - start_time < duration and self.is_connected:
            try:
                # Проверяем ping
                await self.ping()
                
                # Получаем сообщение с timeout
                message = await asyncio.wait_for(
                    self.websocket.recv(),
                    timeout=5.0
                )
                
                message_count += 1
                
                # Обрабатываем разные типы сообщений
                if isinstance(message, bytes):
                    logger.debug(f"📨 Protobuf данные #{message_count}")
                else:
                    try:
                        data = json.loads(message)
                        if data.get('msg') == 'PONG':
                            logger.debug("🏓 Pong получен")
                        elif 'code' in data:
                            logger.info(f"📨 Ответ: {data}")
                        else:
                            logger.debug(f"📨 Данные #{message_count}: {message[:100]}...")
                    except json.JSONDecodeError:
                        logger.debug(f"📨 Неизвестный формат #{message_count}")
                        
            except asyncio.TimeoutError:
                logger.debug("⏰ Timeout, продолжаем...")
                continue
            except websockets.exceptions.ConnectionClosed:
                logger.warning("🔌 Соединение закрыто, переподключение...")
                if await self.reconnect():
                    continue
                else:
                    break
            except Exception as e:
                logger.error(f"❌ Ошибка в listen: {e}")
                if await self.reconnect():
                    continue
                else:
                    break
                
        logger.info(f"📊 Получено сообщений: {message_count}")
        return message_count
        
    async def reconnect(self):
        """Переподключение с exponential backoff"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Достигнуто максимальное количество попыток")
            return False
            
        self.reconnect_attempts += 1
        delay = self.reconnect_delay * (2 ** (self.reconnect_attempts - 1))
        
        logger.info(f"🔄 Попытка переподключения {self.reconnect_attempts} (задержка {delay}с)")
        
        try:
            await asyncio.sleep(delay)
            if await self.connect():
                # Восстанавливаем подписки
                for symbol in self.subscriptions:
                    await self.subscribe(symbol)
                logger.info("✅ Переподключение успешно")
                return True
            else:
                return False
        except Exception as e:
            logger.error(f"❌ Ошибка переподключения: {e}")
            return False

async def test_websocket_stability():
    """Тест стабильности WebSocket"""
    print("🔌 ТЕСТ СТАБИЛЬНОСТИ WEB SOCKET")
    print("=" * 50)
    
    client = StableWebSocketClient()
    
    try:
        # Подключение
        if not await client.connect():
            print("❌ Не удалось подключиться")
            return False
            
        # Подписка на символы
        symbols = ['BTCUSDT', 'ETHUSDT']
        for symbol in symbols:
            client.subscriptions[symbol] = True
            await client.subscribe(symbol)
            
        # Прослушивание
        message_count = await client.listen(duration=30)
        
        print(f"📊 Результат: {message_count} сообщений за 30 секунд")
        
        if message_count > 0:
            print("✅ WebSocket стабильно работает!")
            return True
        else:
            print("❌ Нет данных от WebSocket")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_websocket_stability()) 