#!/usr/bin/env python3
"""
Быстрый тест WebSocket стабильности
"""

import asyncio
import websockets
import json
import time

async def test_websocket_quick():
    """Быстрый тест WebSocket"""
    print("🔌 БЫСТРЫЙ ТЕСТ WEB SOCKET")
    print("=" * 30)
    
    try:
        # Подключение
        websocket = await websockets.connect("wss://wbs-api.mexc.com/ws", timeout=10)
        print("✅ Подключение успешно")
        
        # Подписка на BTCUSDT
        subscription = {
            "method": "SUBSCRIPTION",
            "params": ["spot@public.aggre.deals.v3.api.pb@100ms@BTCUSDT"]
        }
        
        await websocket.send(json.dumps(subscription))
        
        # Ждем ответ
        response = await asyncio.wait_for(websocket.recv(), timeout=5)
        print(f"📨 Ответ: {response}")
        
        # Ждем данные (5 секунд)
        start_time = time.time()
        message_count = 0
        
        while time.time() - start_time < 5:
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1)
                message_count += 1
                if message_count <= 3:  # Показываем первые 3 сообщения
                    print(f"📨 Данные #{message_count}: {message[:100]}...")
            except asyncio.TimeoutError:
                break
                
        print(f"📊 Получено сообщений: {message_count}")
        
        await websocket.close()
        
        if message_count > 0:
            print("✅ WebSocket работает стабильно!")
            return True
        else:
            print("❌ Нет данных от WebSocket")
            return False
            
    except Exception as e:
        print(f"❌ WebSocket ошибка: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_websocket_quick()) 