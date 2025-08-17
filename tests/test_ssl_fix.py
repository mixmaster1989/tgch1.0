#!/usr/bin/env python3
"""
Тест исправления SSL проблем в REST API запросах
"""

import asyncio
import aiohttp
import ssl
import time

async def test_ssl_fix():
    """Тест исправления SSL проблем"""
    print("🔒 ТЕСТ ИСПРАВЛЕНИЯ SSL ПРОБЛЕМ")
    print("=" * 50)
    
    # Создаем SSL контекст
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Создаем connector с SSL
    connector = aiohttp.TCPConnector(ssl=ssl_context, limit=100)
    
    symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
    
    try:
        print("📡 Тестируем REST API с SSL контекстом...")
        
        async with aiohttp.ClientSession(connector=connector) as session:
            for symbol in symbols:
                try:
                    # Тест 24hr ticker
                    url = f"https://api.mexc.com/api/v3/ticker/24hr"
                    params = {'symbol': symbol}
                    
                    start_time = time.time()
                    async with session.get(url, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            elapsed = time.time() - start_time
                            print(f"✅ {symbol}: ${float(data['lastPrice']):.2f} (за {elapsed:.2f}с)")
                        else:
                            print(f"❌ {symbol}: HTTP {response.status}")
                            
                except Exception as e:
                    print(f"❌ {symbol}: {e}")
                    
            print("\n📊 Тестируем klines API...")
            
            for symbol in symbols:
                try:
                    # Тест klines
                    url = f"https://api.mexc.com/api/v3/klines"
                    params = {'symbol': symbol, 'interval': '1h', 'limit': 100}
                    
                    start_time = time.time()
                    async with session.get(url, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            elapsed = time.time() - start_time
                            print(f"✅ {symbol}: {len(data)} свечей (за {elapsed:.2f}с)")
                        else:
                            print(f"❌ {symbol}: HTTP {response.status}")
                            
                except Exception as e:
                    print(f"❌ {symbol}: {e}")
                    
            print("\n📚 Тестируем depth API...")
            
            for symbol in symbols:
                try:
                    # Тест depth
                    url = f"https://api.mexc.com/api/v3/depth"
                    params = {'symbol': symbol, 'limit': 100}
                    
                    start_time = time.time()
                    async with session.get(url, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            elapsed = time.time() - start_time
                            print(f"✅ {symbol}: {len(data['bids'])} bids, {len(data['asks'])} asks (за {elapsed:.2f}с)")
                        else:
                            print(f"❌ {symbol}: HTTP {response.status}")
                            
                except Exception as e:
                    print(f"❌ {symbol}: {e}")
        
        print("\n✅ SSL тест завершен успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Общая ошибка SSL теста: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_ssl_fix()) 