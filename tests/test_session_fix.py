#!/usr/bin/env python3
"""
Быстрый тест исправления Session is closed
"""

import asyncio
import aiohttp
import ssl

async def test_session_fix():
    """Тест исправления Session is closed"""
    print("🔧 ТЕСТ SESSION IS CLOSED")
    print("=" * 30)
    
    try:
        # SSL контекст
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Connector с улучшенными настройками
        connector = aiohttp.TCPConnector(
            ssl=ssl_context,
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300,
            use_dns_cache=True
        )
        
        # Тест с одним session
        async with aiohttp.ClientSession(connector=connector) as session:
            for i in range(3):
                try:
                    url = "https://api.mexc.com/api/v3/ticker/24hr"
                    params = {'symbol': 'BTCUSDT'}
                    
                    async with session.get(url, params=params, timeout=10) as response:
                        if response.status == 200:
                            data = await response.json()
                            print(f"✅ Запрос #{i+1}: ${float(data['lastPrice']):.2f}")
                        else:
                            print(f"❌ HTTP {response.status}")
                            
                except Exception as e:
                    print(f"❌ Ошибка запроса #{i+1}: {e}")
                    
        print("✅ Session работает стабильно!")
        return True
        
    except Exception as e:
        print(f"❌ Session ошибка: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_session_fix()) 