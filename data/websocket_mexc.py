import asyncio
import websockets
import json
import pandas as pd
from datetime import datetime

class MEXCWebSocket:
    def __init__(self):
        self.uri = "wss://wbs.mexc.com/ws"
        self.pairs = ["BTC_USDT", "ETH_USDT", "SOL_USDT"]  # Пары для отслеживания
        self.ohlcv_data = {}  # Хранение данных OHLCV
    
    async def connect(self):
        """Подключение к WebSocket MEXC"""
        async with websockets.connect(self.uri) as websocket:
            # Подписка на данные по парам
            for pair in self.pairs:
                subscribe_msg = {
                    "method": "SUBSCRIBE",
                    "params": [f"{pair.lower()}@kline_1m"],
                    "id": 1
                }
                await websocket.send(json.dumps(subscribe_msg))
            
            # Обработка входящих сообщений
            while True:
                try:
                    message = await websocket.recv()
                    data = json.loads(message)
                    await self._process_message(data)
                except Exception as e:
                    print(f"Ошибка при получении данных: {e}")
                    break
    
    async def _process_message(self, data):
        """Обработка полученного сообщения с данными"""
        if 'data' in data and 'k' in data['data']:
            symbol = data['data']['s']
            kline = data['data']['k']
            
            # Извлечение данных свечи
            timestamp = datetime.fromtimestamp(kline['t']/1000)
            open_price = float(kline['o'])
            high_price = float(kline['h'])
            low_price = float(kline['l'])
            close_price = float(kline['c'])
            volume = float(kline['v'])
            
            # Добавление данных в хранилище
            if symbol not in self.ohlcv_data:
                self.ohlcv_data[symbol] = []
            
            self.ohlcv_data[symbol].append({
                'timestamp': timestamp,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            # Ограничение длины хранилища (например, последние 100 свечей)
            if len(self.ohlcv_data[symbol]) > 100:
                self.ohlcv_data[symbol] = self.ohlcv_data[symbol][-100:]
    
    def get_ohlcv(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        """Получение данных OHLCV в формате DataFrame"""
        if symbol not in self.ohlcv_data:
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        
        df = pd.DataFrame(self.ohlcv_data[symbol][-limit:])
        return df.sort_values('timestamp').reset_index(drop=True)