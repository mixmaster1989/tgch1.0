#!/usr/bin/env python3
"""
Тестирование WebSocket потока сделок
"""

import asyncio
import json
import time
from datetime import datetime
from mexc_websocket_client import MEXCWebSocketClient, StreamType

async def test_trades_stream():
    """Тестирование потока сделок"""
    print("🔍 ТЕСТИРОВАНИЕ WEB SOCKET ПОТОКА СДЕЛОК")
    print("=" * 60)
    print(f"Время: {datetime.now()}")
    print()
    
    # Создаем WebSocket клиент
    client = MEXCWebSocketClient()
    
    # Счетчики
    trade_count = 0
    orderbook_count = 0
    
    async def trade_callback(trade_data):
        """Callback для сделок"""
        nonlocal trade_count
        trade_count += 1
        print(f"💱 TRADE #{trade_count}: {trade_data}")
    
    async def orderbook_callback(orderbook):
        """Callback для ордербука"""
        nonlocal orderbook_count
        orderbook_count += 1
        if orderbook_count % 10 == 0:  # Показываем каждые 10 обновлений
            print(f"📚 ORDERBOOK #{orderbook_count}: Спред ${orderbook.get_spread():.4f}")
    
    try:
        # Подключаемся к WebSocket
        print("🚀 Подключение к WebSocket...")
        await client.connect()
        
        # Загружаем снапшот ордербука
        print("📡 Загрузка снапшота ордербука...")
        await client.load_order_book_snapshot("ETHUSDT")
        
        # Подписываемся на ордербук
        print("📚 Подписка на ордербук...")
        await client.subscribe(
            StreamType.DEPTH,
            "ETHUSDT",
            interval="100ms",
            callback=orderbook_callback
        )
        
        # Подписываемся на сделки
        print("💱 Подписка на сделки...")
        await client.subscribe(
            StreamType.TRADES,
            "ETHUSDT",
            interval="100ms",
            callback=trade_callback
        )
        
        # Показываем активные подписки
        print(f"📋 Активные подписки: {list(client.subscriptions.keys())}")
        
        # Запускаем listen цикл в отдельной задаче
        print("🎧 Запуск listen цикла...")
        listen_task = asyncio.create_task(client.listen())
        
        # Ждем и собираем данные
        print("⏳ Сбор данных (30 секунд)...")
        print("   (Ордербук обновления показываются каждые 10 раз)")
        print()
        
        start_time = time.time()
        while time.time() - start_time < 30:
            await asyncio.sleep(1)
            
            # Показываем статистику каждые 5 секунд
            elapsed = int(time.time() - start_time)
            if elapsed % 5 == 0:
                print(f"📊 {elapsed}с: Ордербук={orderbook_count}, Сделки={trade_count}")
        
        # Останавливаем listen цикл
        client.is_running = False
        listen_task.cancel()
        
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print("=" * 60)
        print(f"   Время тестирования: 30 секунд")
        print(f"   Обновлений ордербука: {orderbook_count}")
        print(f"   Получено сделок: {trade_count}")
        print(f"   Скорость ордербука: {orderbook_count/30:.1f} обновлений/сек")
        print(f"   Скорость сделок: {trade_count/30:.1f} сделок/сек")
        
        if trade_count == 0:
            print("\n❌ ПРОБЛЕМА: Сделки не приходят!")
            print("   Возможные причины:")
            print("   - MEXC не отправляет данные сделок в тестовом режиме")
            print("   - Неправильная подписка на поток сделок")
            print("   - Проблема с форматом данных")
        else:
            print(f"\n✅ УСПЕХ: Получено {trade_count} сделок!")
        
        # Останавливаем клиент
        print("\n🛑 Остановка WebSocket клиента...")
        await client.disconnect()
        print("✅ WebSocket клиент остановлен")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        
        # В случае ошибки тоже останавливаем клиент
        try:
            await client.disconnect()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_trades_stream()) 