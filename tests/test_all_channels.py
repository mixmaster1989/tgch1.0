#!/usr/bin/env python3
"""
Тест всех возможных каналов WebSocket MEX
"""

import asyncio
import websockets
import json

async def test_channel(channel: str):
    """Тест одного канала"""
    print(f"\n🔌 Тест канала: {channel}")
    
    try:
        websocket = await websockets.connect("wss://wbs.mexc.com/ws", timeout=10)
        
        subscription = {
            "method": "SUBSCRIPTION",
            "params": [channel]
        }
        
        await websocket.send(json.dumps(subscription))
        
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            
            if 'msg' in data and 'Blocked' in data['msg']:
                print(f"  🚫 ЗАБЛОКИРОВАН: {data['msg']}")
                return False
            else:
                print(f"  ✅ РАБОТАЕТ: {data}")
                return True
                
        except asyncio.TimeoutError:
            print(f"  ⏰ ТАЙМАУТ")
            return False
            
    except Exception as e:
        print(f"  ❌ ОШИБКА: {e}")
        return False
    finally:
        try:
            await websocket.close()
        except:
            pass

async def main():
    """Тест всех каналов"""
    print("🔍 ТЕСТ ВСЕХ КАНАЛОВ WEB SOCKET MEX")
    print("=" * 60)
    
    # Все возможные каналы
    channels = [
        # Спот рынок
        "spot@public.ticker.v3.api@BTCUSDT",
        "spot@public.depth.v3.api@BTCUSDT", 
        "spot@public.kline.v3.api@BTCUSDT@1m",
        "spot@public.deals.v3.api@BTCUSDT",
        
        # Фьючерсы
        "contract@public.ticker.v3.api@BTC_USDT",
        "contract@public.depth.v3.api@BTC_USDT",
        "contract@public.kline.v3.api@BTC_USDT@1m",
        "contract@public.deals.v3.api@BTC_USDT",
        
        # Без версии API
        "spot@public.ticker.api@BTCUSDT",
        "spot@public.depth.api@BTCUSDT",
        "spot@public.kline.api@BTCUSDT@1m",
        "spot@public.deals.api@BTCUSDT",
        
        # Без .api
        "spot@public.ticker.v3@BTCUSDT",
        "spot@public.depth.v3@BTCUSDT",
        "spot@public.kline.v3@BTCUSDT@1m",
        "spot@public.deals.v3@BTCUSDT",
        
        # Старые форматы
        "spot@public.ticker@BTCUSDT",
        "spot@public.depth@BTCUSDT", 
        "spot@public.kline@BTCUSDT@1m",
        "spot@public.deals@BTCUSDT",
        
        # Общие каналы
        "public.ticker@BTCUSDT",
        "public.depth@BTCUSDT",
        "public.kline@BTCUSDT@1m",
        "public.deals@BTCUSDT",
        
        # Без символа
        "spot@public.ticker.v3.api",
        "spot@public.depth.v3.api",
        "spot@public.kline.v3.api",
        "spot@public.deals.v3.api"
    ]
    
    results = {}
    
    for channel in channels:
        success = await test_channel(channel)
        results[channel] = success
        
        if success:
            print(f"  🎉 НАЙДЕН РАБОТАЮЩИЙ КАНАЛ: {channel}")
            break
    
    # Итоговый отчет
    print(f"\n📋 ИТОГОВЫЙ ОТЧЕТ:")
    print("=" * 60)
    
    working = [ch for ch, result in results.items() if result]
    blocked = [ch for ch, result in results.items() if not result]
    
    print(f"✅ Работающие каналы: {len(working)}")
    print(f"🚫 Заблокированные каналы: {len(blocked)}")
    
    if working:
        print(f"\n🎉 РАБОТАЮЩИЕ КАНАЛЫ:")
        for channel in working:
            print(f"  ✅ {channel}")
    else:
        print(f"\n❌ ВСЕ КАНАЛЫ ЗАБЛОКИРОВАНЫ!")
        print(f"🔍 MEX действительно блокирует WebSocket подписки")
        print(f"🔄 Нужно использовать REST API")

if __name__ == "__main__":
    asyncio.run(main()) 