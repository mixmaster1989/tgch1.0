#!/usr/bin/env python3
"""
Тест кэширования данных для корреляций
"""

import asyncio
import aiohttp
import ssl
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List

class CorrelationCache:
    def __init__(self):
        self.price_history = {}  # symbol -> [prices]
        self.correlation_data = {}  # symbol -> correlation_data
        self.max_history_size = 100
        
    async def fetch_price_data(self, symbol: str) -> float:
        """Получение текущей цены через REST API"""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        try:
            async with aiohttp.ClientSession(connector=connector) as session:
                url = "https://api.mexc.com/api/v3/ticker/24hr"
                params = {'symbol': symbol}
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return float(data['lastPrice'])
                    else:
                        print(f"❌ HTTP {response.status} для {symbol}")
                        return None
        except Exception as e:
            print(f"❌ Ошибка получения цены {symbol}: {e}")
            return None
            
    def add_price(self, symbol: str, price: float):
        """Добавление цены в историю"""
        if symbol not in self.price_history:
            self.price_history[symbol] = []
            
        self.price_history[symbol].append({
            'price': price,
            'timestamp': datetime.now()
        })
        
        # Ограничиваем размер истории
        if len(self.price_history[symbol]) > self.max_history_size:
            self.price_history[symbol] = self.price_history[symbol][-self.max_history_size:]
            
        print(f"💰 {symbol}: ${price:.2f} (история: {len(self.price_history[symbol])})")
        
    def calculate_correlation(self, symbol1: str, symbol2: str) -> float:
        """Расчет корреляции между двумя символами"""
        if symbol1 not in self.price_history or symbol2 not in self.price_history:
            return 0.0
            
        prices1 = [p['price'] for p in self.price_history[symbol1]]
        prices2 = [p['price'] for p in self.price_history[symbol2]]
        
        # Берем минимальную длину
        min_len = min(len(prices1), len(prices2))
        if min_len < 5:
            return 0.0
            
        prices1 = prices1[-min_len:]
        prices2 = prices2[-min_len:]
        
        # Простой расчет корреляции
        try:
            mean1 = sum(prices1) / len(prices1)
            mean2 = sum(prices2) / len(prices2)
            
            numerator = sum((p1 - mean1) * (p2 - mean2) for p1, p2 in zip(prices1, prices2))
            denominator1 = sum((p1 - mean1) ** 2 for p1 in prices1)
            denominator2 = sum((p2 - mean2) ** 2 for p2 in prices2)
            
            if denominator1 == 0 or denominator2 == 0:
                return 0.0
                
            correlation = numerator / (denominator1 * denominator2) ** 0.5
            return max(-1.0, min(1.0, correlation))  # Ограничиваем [-1, 1]
            
        except Exception as e:
            print(f"❌ Ошибка расчета корреляции: {e}")
            return 0.0
            
    def get_correlation_data(self, symbol: str) -> Dict:
        """Получение данных корреляции для символа"""
        if symbol not in self.price_history:
            return {
                'symbol': symbol,
                'btc_correlation': 0.0,
                'eth_correlation': 0.0,
                'volatility_rank': 0,
                'correlation_strength': 'neutral',
                'data_points': 0
            }
            
        data_points = len(self.price_history[symbol])
        
        # Корреляции с BTC и ETH
        btc_correlation = self.calculate_correlation(symbol, 'BTCUSDT')
        eth_correlation = self.calculate_correlation(symbol, 'ETHUSDT')
        
        # Определяем силу корреляции
        max_correlation = max(abs(btc_correlation), abs(eth_correlation))
        if max_correlation > 0.7:
            strength = 'strong'
        elif max_correlation > 0.3:
            strength = 'moderate'
        else:
            strength = 'weak'
            
        return {
            'symbol': symbol,
            'btc_correlation': btc_correlation,
            'eth_correlation': eth_correlation,
            'volatility_rank': data_points,
            'correlation_strength': strength,
            'data_points': data_points
        }
        
    def get_all_correlations(self) -> Dict[str, Dict]:
        """Получение всех корреляций"""
        symbols = list(self.price_history.keys())
        correlations = {}
        
        for symbol in symbols:
            correlations[symbol] = self.get_correlation_data(symbol)
            
        return correlations

async def test_correlation_cache():
    """Тест кэширования корреляций"""
    print("📊 ТЕСТ КЭШИРОВАНИЯ КОРРЕЛЯЦИЙ")
    print("=" * 50)
    
    cache = CorrelationCache()
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
    
    try:
        print("📡 Сбор данных о ценах...")
        
        # Собираем данные в течение 30 секунд
        start_time = time.time()
        collection_duration = 30
        
        while time.time() - start_time < collection_duration:
            for symbol in symbols:
                price = await cache.fetch_price_data(symbol)
                if price:
                    cache.add_price(symbol, price)
                    
            # Пауза между запросами
            await asyncio.sleep(2)
            
        print(f"\n📊 Собрано данных:")
        for symbol in symbols:
            if symbol in cache.price_history:
                print(f"  {symbol}: {len(cache.price_history[symbol])} точек")
                
        print(f"\n🔗 Анализ корреляций:")
        correlations = cache.get_all_correlations()
        
        for symbol, data in correlations.items():
            print(f"  {symbol}:")
            print(f"    BTC корреляция: {data['btc_correlation']:.3f}")
            print(f"    ETH корреляция: {data['eth_correlation']:.3f}")
            print(f"    Сила: {data['correlation_strength']}")
            print(f"    Точки данных: {data['data_points']}")
            
        # Проверяем достаточность данных
        sufficient_data = all(data['data_points'] >= 5 for data in correlations.values())
        
        if sufficient_data:
            print("\n✅ Достаточно данных для корреляций!")
            return True
        else:
            print("\n❌ Недостаточно данных для корреляций")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_correlation_cache()) 