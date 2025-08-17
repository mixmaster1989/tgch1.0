#!/usr/bin/env python3
"""
Тест WebSocket MEXC с правильными форматами каналов
"""

import asyncio
import websockets
import json
import time

async def test_mexc_websocket():
    """Тест WebSocket MEXC с правильными каналами"""
    print("🔍 ТЕСТ WEB SOCKET MEXC")
    print("=" * 60)
    
    url = "wss://wbs-api.mexc.com/ws"
    
    try:
        print(f"📡 Подключение к {url}...")
        websocket = await websockets.connect(url, timeout=10)
        print("✅ Подключение успешно!")
        
        # Тест ping/pong
        print("\n🏓 Тест ping/pong...")
        ping_msg = {"method": "PING"}
        await websocket.send(json.dumps(ping_msg))
        
        try:
            pong = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"📨 PONG: {pong}")
        except asyncio.TimeoutError:
            print("⏰ PONG не получен")
        
        # Тест подписки на сделки (правильный формат)
        print("\n📊 Тест подписки на сделки...")
        deals_subscription = {
            "method": "SUBSCRIPTION",
            "params": ["spot@public.aggre.deals.v3.api.pb@100ms@BTCUSDT"]
        }
        
        await websocket.send(json.dumps(deals_subscription))
        
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"📨 Ответ на сделки: {response}")
        except asyncio.TimeoutError:
            print("⏰ Нет ответа на сделки")
        
        # Тест подписки на свечи (правильный формат)
        print("\n📈 Тест подписки на свечи...")
        kline_subscription = {
            "method": "SUBSCRIPTION",
            "params": ["spot@public.kline.v3.api.pb@BTCUSDT@Min1"]
        }
        
        await websocket.send(json.dumps(kline_subscription))
        
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"📨 Ответ на свечи: {response}")
        except asyncio.TimeoutError:
            print("⏰ Нет ответа на свечи")
        
        # Тест подписки на глубину (правильный формат)
        print("\n📚 Тест подписки на глубину...")
        depth_subscription = {
            "method": "SUBSCRIPTION",
            "params": ["spot@public.aggre.depth.v3.api.pb@100ms@BTCUSDT"]
        }
        
        await websocket.send(json.dumps(depth_subscription))
        
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            print(f"📨 Ответ на глубину: {response}")
        except asyncio.TimeoutError:
            print("⏰ Нет ответа на глубину")
        
        # Ждем данные
        print("\n⏳ Ждем данные (10 секунд)...")
        start_time = time.time()
        data_count = 0
        
        while time.time() - start_time < 10:
            try:
                data = await asyncio.wait_for(websocket.recv(), timeout=2)
                data_count += 1
                print(f"📨 Данные #{data_count}: {data[:200]}...")
            except asyncio.TimeoutError:
                print("⏰ Нет данных...")
                break
        
        print(f"\n📊 Получено данных: {data_count}")
        
        await websocket.close()
        print("✅ WebSocket закрыт")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_mexc_websocket()) 