#!/usr/bin/env python3
"""
Тест fallback стратегии - работа только через REST API
"""

import asyncio
import aiohttp
import ssl
import json
import time
from datetime import datetime
from typing import Dict, List, Optional

class FallbackDataManager:
    def __init__(self):
        self.market_data = {}
        self.orderbook_data = {}
        self.kline_data = {}
        self.trade_history = {}
        self.update_interval = 5  # секунды
        self.is_running = False
        
        # SSL контекст
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        
    async def fetch_market_data(self, symbol: str) -> Optional[Dict]:
        """Получение рыночных данных через REST API"""
        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = "https://api.mexc.com/api/v3/ticker/24hr"
                params = {'symbol': symbol}
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'symbol': symbol,
                            'price': float(data['lastPrice']),
                            'change_24h': float(data['priceChangePercent']),
                            'volume_24h': float(data['volume']),
                            'high_24h': float(data['highPrice']),
                            'low_24h': float(data['lowPrice']),
                            'timestamp': datetime.now(),
                            'source': 'REST_API'
                        }
                    else:
                        print(f"❌ HTTP {response.status} для {symbol}")
                        return None
        except Exception as e:
            print(f"❌ Ошибка получения рыночных данных {symbol}: {e}")
            return None
            
    async def fetch_orderbook(self, symbol: str) -> Optional[Dict]:
        """Получение ордербука через REST API"""
        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = "https://api.mexc.com/api/v3/depth"
                params = {'symbol': symbol, 'limit': 100}
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
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
                            'source': 'REST_API'
                        }
                    else:
                        print(f"❌ HTTP {response.status} для ордербука {symbol}")
                        return None
        except Exception as e:
            print(f"❌ Ошибка получения ордербука {symbol}: {e}")
            return None
            
    async def fetch_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> Optional[List[Dict]]:
        """Получение свечей через REST API"""
        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = "https://api.mexc.com/api/v3/klines"
                params = {'symbol': symbol, 'interval': interval, 'limit': limit}
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
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
                                'source': 'REST_API'
                            })
                        
                        return klines
                    else:
                        print(f"❌ HTTP {response.status} для свечей {symbol}")
                        return None
        except Exception as e:
            print(f"❌ Ошибка получения свечей {symbol}: {e}")
            return None
            
    async def fetch_recent_trades(self, symbol: str, limit: int = 100) -> Optional[List[Dict]]:
        """Получение последних сделок через REST API"""
        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(connector=connector) as session:
                url = "https://api.mexc.com/api/v3/trades"
                params = {'symbol': symbol, 'limit': limit}
                
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        trades = []
                        
                        for trade in data:
                            trades.append({
                                'symbol': symbol,
                                'price': float(trade['price']),
                                'quantity': float(trade['qty']),
                                'side': trade['isBuyerMaker'],
                                'timestamp': int(trade['time']),
                                'source': 'REST_API'
                            })
                        
                        return trades
                    else:
                        print(f"❌ HTTP {response.status} для сделок {symbol}")
                        return None
        except Exception as e:
            print(f"❌ Ошибка получения сделок {symbol}: {e}")
            return None
            
    async def update_all_data(self, symbols: List[str]):
        """Обновление всех данных для символов"""
        print(f"🔄 Обновление данных для {len(symbols)} символов...")
        
        for symbol in symbols:
            try:
                # Рыночные данные
                market_data = await self.fetch_market_data(symbol)
                if market_data:
                    self.market_data[symbol] = market_data
                    print(f"💰 {symbol}: ${market_data['price']:.2f}")
                    
                # Ордербук
                orderbook = await self.fetch_orderbook(symbol)
                if orderbook:
                    self.orderbook_data[symbol] = orderbook
                    print(f"📚 {symbol}: спред {orderbook['spread_percent']:.3f}%")
                    
                # Свечи
                klines = await self.fetch_klines(symbol, '60m', 100)
                if klines:
                    self.kline_data[symbol] = klines
                    print(f"📊 {symbol}: {len(klines)} свечей")
                    
                # Сделки
                trades = await self.fetch_recent_trades(symbol, 100)
                if trades:
                    self.trade_history[symbol] = trades
                    print(f"💱 {symbol}: {len(trades)} сделок")
                    
            except Exception as e:
                print(f"❌ Ошибка обновления {symbol}: {e}")
                
    async def run_fallback_loop(self, symbols: List[str], duration: int = 60):
        """Запуск fallback цикла обновления данных"""
        print(f"🚀 Запуск fallback стратегии на {duration} секунд...")
        print(f"📡 Символы: {', '.join(symbols)}")
        
        self.is_running = True
        start_time = time.time()
        update_count = 0
        
        while time.time() - start_time < duration and self.is_running:
            try:
                await self.update_all_data(symbols)
                update_count += 1
                
                print(f"✅ Обновление #{update_count} завершено")
                
                # Пауза между обновлениями
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                print(f"❌ Ошибка в fallback цикле: {e}")
                await asyncio.sleep(5)
                
        print(f"📊 Fallback завершен: {update_count} обновлений")
        
    def get_summary(self) -> Dict:
        """Получение сводки данных"""
        summary = {
            'market_data_count': len(self.market_data),
            'orderbook_count': len(self.orderbook_data),
            'kline_count': len(self.kline_data),
            'trade_count': len(self.trade_history),
            'symbols': list(self.market_data.keys())
        }
        
        # Добавляем примеры данных
        if self.market_data:
            symbol = list(self.market_data.keys())[0]
            summary['example_market'] = self.market_data[symbol]
            
        if self.orderbook_data:
            symbol = list(self.orderbook_data.keys())[0]
            summary['example_orderbook'] = {
                'symbol': self.orderbook_data[symbol]['symbol'],
                'spread': self.orderbook_data[symbol]['spread'],
                'spread_percent': self.orderbook_data[symbol]['spread_percent']
            }
            
        return summary

async def test_fallback_strategy():
    """Тест fallback стратегии"""
    print("🔄 ТЕСТ FALLBACK СТРАТЕГИИ")
    print("=" * 50)
    
    manager = FallbackDataManager()
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
    
    try:
        # Запускаем fallback цикл на 30 секунд
        await manager.run_fallback_loop(symbols, duration=30)
        
        # Получаем сводку
        summary = manager.get_summary()
        
        print(f"\n📊 СВОДКА:")
        print(f"  Рыночные данные: {summary['market_data_count']} символов")
        print(f"  Ордербуки: {summary['orderbook_count']} символов")
        print(f"  Свечи: {summary['kline_count']} символов")
        print(f"  Сделки: {summary['trade_count']} символов")
        
        if 'example_market' in summary:
            example = summary['example_market']
            print(f"  Пример: {example['symbol']} = ${example['price']:.2f}")
            
        if 'example_orderbook' in summary:
            example = summary['example_orderbook']
            print(f"  Спред: {example['spread_percent']:.3f}%")
            
        # Проверяем полноту данных
        complete_data = (
            summary['market_data_count'] > 0 and
            summary['orderbook_count'] > 0 and
            summary['kline_count'] > 0
        )
        
        if complete_data:
            print("\n✅ Fallback стратегия работает!")
            return True
        else:
            print("\n❌ Неполные данные в fallback")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_fallback_strategy()) 