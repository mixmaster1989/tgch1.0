#!/usr/bin/env python3
"""
Тест улучшенной обработки ошибок с retry механизмом
"""

import asyncio
import aiohttp
import ssl
import json
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Callable
from functools import wraps

def async_retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Декоратор для retry механизма"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff ** attempt)
                        print(f"⚠️ Попытка {attempt + 1} неудачна: {e}")
                        print(f"⏳ Ожидание {wait_time:.1f}с перед повторной попыткой...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"❌ Все {max_attempts} попыток неудачны: {e}")
                        
            raise last_exception
        return wrapper
    return decorator

class RobustDataManager:
    def __init__(self):
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
        self.connector = aiohttp.TCPConnector(
            ssl=self.ssl_context,
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        self.session = None
        self.error_count = 0
        self.success_count = 0
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(connector=self.connector)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
            
    @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
    async def safe_api_call(self, url: str, params: Dict = None) -> Optional[Dict]:
        """Безопасный вызов API с retry"""
        if not self.session:
            raise RuntimeError("Session не инициализирована")
            
        try:
            async with self.session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    self.success_count += 1
                    return data
                elif response.status == 429:  # Rate limit
                    retry_after = int(response.headers.get('Retry-After', 5))
                    print(f"⚠️ Rate limit, ожидание {retry_after}с...")
                    await asyncio.sleep(retry_after)
                    raise Exception("Rate limit exceeded")
                else:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                    
        except asyncio.TimeoutError:
            raise Exception("Timeout")
        except Exception as e:
            self.error_count += 1
            raise e
            
    async def fetch_market_data_robust(self, symbol: str) -> Optional[Dict]:
        """Получение рыночных данных с улучшенной обработкой ошибок"""
        try:
            url = "https://api.mexc.com/api/v3/ticker/24hr"
            params = {'symbol': symbol}
            
            data = await self.safe_api_call(url, params)
            
            if data:
                return {
                    'symbol': symbol,
                    'price': float(data['lastPrice']),
                    'change_24h': float(data['priceChangePercent']),
                    'volume_24h': float(data['volume']),
                    'high_24h': float(data['highPrice']),
                    'low_24h': float(data['lowPrice']),
                    'timestamp': datetime.now(),
                    'source': 'REST_API_ROBUST'
                }
            return None
            
        except Exception as e:
            print(f"❌ Ошибка получения рыночных данных {symbol}: {e}")
            return None
            
    async def fetch_orderbook_robust(self, symbol: str) -> Optional[Dict]:
        """Получение ордербука с улучшенной обработкой ошибок"""
        try:
            url = "https://api.mexc.com/api/v3/depth"
            params = {'symbol': symbol, 'limit': 100}
            
            data = await self.safe_api_call(url, params)
            
            if data and 'bids' in data and 'asks' in data:
                # Расчет спреда
                best_bid = float(data['bids'][0][0]) if data['bids'] else 0
                best_ask = float(data['asks'][0][0]) if data['asks'] else 0
                spread = best_ask - best_bid
                spread_percent = (spread / best_bid * 100) if best_bid > 0 else 0
                
                # Расчет объемов
                bid_volume = sum(float(bid[1]) for bid in data['bids'][:10])
                ask_volume = sum(float(ask[1]) for ask in data['asks'][:10])
                volume_ratio = bid_volume / ask_volume if ask_volume > 0 else 1.0
                
                return {
                    'symbol': symbol,
                    'bids': [[float(price), float(qty)] for price, qty in data['bids'][:10]],
                    'asks': [[float(price), float(qty)] for price, qty in data['asks'][:10]],
                    'spread': spread,
                    'spread_percent': spread_percent,
                    'bid_volume': bid_volume,
                    'ask_volume': ask_volume,
                    'volume_ratio': volume_ratio,
                    'liquidity_score': 0.8,
                    'timestamp': datetime.now(),
                    'source': 'REST_API_ROBUST'
                }
            return None
            
        except Exception as e:
            print(f"❌ Ошибка получения ордербука {symbol}: {e}")
            return None
            
    async def fetch_klines_robust(self, symbol: str, interval: str = '1h', limit: int = 100) -> Optional[List[Dict]]:
        """Получение свечей с улучшенной обработкой ошибок"""
        try:
            url = "https://api.mexc.com/api/v3/klines"
            params = {'symbol': symbol, 'interval': interval, 'limit': limit}
            
            data = await self.safe_api_call(url, params)
            
            if data:
                klines = []
                for kline in data:
                    klines.append({
                        'symbol': symbol,
                        'interval': interval,
                        'open': float(kline[1]),
                        'high': float(kline[2]),
                        'low': float(kline[3]),
                        'close': float(kline[4]),
                        'volume': float(kline[5]),
                        'timestamp': int(kline[0]),
                        'source': 'REST_API_ROBUST'
                    })
                return klines
            return None
            
        except Exception as e:
            print(f"❌ Ошибка получения свечей {symbol}: {e}")
            return None
            
    async def simulate_network_issues(self):
        """Симуляция сетевых проблем для тестирования"""
        if random.random() < 0.1:  # 10% вероятность ошибки
            raise Exception("Simulated network error")
            
    async def test_robust_data_fetching(self, symbols: List[str]):
        """Тест надежного получения данных"""
        print(f"🛡️ Тестируем надежное получение данных для {len(symbols)} символов...")
        
        results = {
            'market_data': {},
            'orderbooks': {},
            'klines': {},
            'errors': []
        }
        
        for symbol in symbols:
            try:
                # Симулируем сетевые проблемы
                await self.simulate_network_issues()
                
                # Получаем данные
                market_data = await self.fetch_market_data_robust(symbol)
                if market_data:
                    results['market_data'][symbol] = market_data
                    print(f"✅ {symbol}: ${market_data['price']:.2f}")
                    
                orderbook = await self.fetch_orderbook_robust(symbol)
                if orderbook:
                    results['orderbooks'][symbol] = orderbook
                    print(f"📚 {symbol}: спред {orderbook['spread_percent']:.3f}%")
                    
                klines = await self.fetch_klines_robust(symbol, '60m', 50)
                if klines:
                    results['klines'][symbol] = klines
                    print(f"📊 {symbol}: {len(klines)} свечей")
                    
            except Exception as e:
                error_msg = f"Ошибка для {symbol}: {e}"
                results['errors'].append(error_msg)
                print(f"❌ {error_msg}")
                
        return results

async def test_error_handling():
    """Тест обработки ошибок"""
    print("🛡️ ТЕСТ ОБРАБОТКИ ОШИБОК")
    print("=" * 50)
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
    
    async with RobustDataManager() as manager:
        try:
            # Тестируем надежное получение данных
            results = await manager.test_robust_data_fetching(symbols)
            
            print(f"\n📊 РЕЗУЛЬТАТЫ:")
            print(f"  Успешных запросов: {manager.success_count}")
            print(f"  Ошибок: {manager.error_count}")
            print(f"  Рыночные данные: {len(results['market_data'])}/{len(symbols)}")
            print(f"  Ордербуки: {len(results['orderbooks'])}/{len(symbols)}")
            print(f"  Свечи: {len(results['klines'])}/{len(symbols)}")
            print(f"  Ошибки: {len(results['errors'])}")
            
            # Проверяем успешность
            success_rate = manager.success_count / (manager.success_count + manager.error_count) if (manager.success_count + manager.error_count) > 0 else 0
            
            if success_rate > 0.7:  # 70% успешность
                print(f"\n✅ Обработка ошибок работает! Успешность: {success_rate:.1%}")
                return True
            else:
                print(f"\n❌ Низкая успешность: {success_rate:.1%}")
                return False
                
        except Exception as e:
            print(f"❌ Критическая ошибка теста: {e}")
            return False

if __name__ == "__main__":
    asyncio.run(test_error_handling()) 