#!/usr/bin/env python3
"""
Отладка ордербука
"""

import asyncio
from datetime import datetime
from mexc_websocket_client import MEXCWebSocketClient, StreamType

async def debug_orderbook():
    """Отладка ордербука"""
    try:
        print("🔍 ОТЛАДКА ORDERBOOK")
        print("=" * 40)
        print(f"Время: {datetime.now()}")
        print()
        
        # Создаем WebSocket клиент
        client = MEXCWebSocketClient()
        
        # Подключаемся
        print("🔌 Подключение к WebSocket...")
        await client.connect()
        
        # Загружаем снапшот ордербука
        print("📚 Загрузка снапшота ордербука ETHUSDT...")
        await client.load_order_book_snapshot("ETHUSDT")
        
        # Получаем ордербук
        print("📊 Получение ордербука...")
        order_book = client.get_order_book("ETHUSDT")
        
        if order_book:
            print("✅ Ордербук получен!")
            print(f"   Символ: {order_book.symbol}")
            print(f"   Снапшот загружен: {order_book.snapshot_loaded}")
            print(f"   Количество bids: {len(order_book.bids)}")
            print(f"   Количество asks: {len(order_book.asks)}")
            
            # Получаем лучшие цены
            best_bid = order_book.get_best_bid()
            best_ask = order_book.get_best_ask()
            
            if best_bid and best_ask:
                bid_price = float(best_bid[0])
                ask_price = float(best_ask[0])
                print(f"   Лучшая покупка: ${bid_price} ({best_bid[1]})")
                print(f"   Лучшая продажа: ${ask_price} ({best_ask[1]})")
                
                spread = ask_price - bid_price
                spread_percent = (spread / bid_price) * 100
                print(f"   Спред: ${spread:.4f} ({spread_percent:.4f}%)")
                
                # Показываем топ-5 уровней
                print("\n   Топ-5 покупок:")
                sorted_bids = sorted(order_book.bids.items(), key=lambda x: float(x[0]), reverse=True)
                for i, (price, qty) in enumerate(sorted_bids[:5]):
                    print(f"     {i+1}. ${float(price):.2f} - {qty}")
                
                print("\n   Топ-5 продаж:")
                sorted_asks = sorted(order_book.asks.items(), key=lambda x: float(x[0]))
                for i, (price, qty) in enumerate(sorted_asks[:5]):
                    print(f"     {i+1}. ${float(price):.2f} - {qty}")
            else:
                print("   ❌ Нет лучших цен")
        else:
            print("   ❌ Ордербук не получен")
        
        # Подписываемся на обновления
        print("\n📡 Подписка на обновления ордербука...")
        
        async def orderbook_callback(order_book):
            print(f"🔄 Обновление ордербука: {order_book.symbol}")
            best_bid = order_book.get_best_bid()
            best_ask = order_book.get_best_ask()
            if best_bid and best_ask:
                bid_price = float(best_bid[0])
                ask_price = float(best_ask[0])
                spread = ask_price - bid_price
                print(f"   Спред: ${spread:.4f}")
        
        await client.subscribe(
            StreamType.DEPTH,
            "ETHUSDT",
            interval="100ms",
            callback=orderbook_callback
        )
        
        # Ждем обновлений
        print("⏳ Ожидание обновлений (10 секунд)...")
        await asyncio.sleep(10)
        
        # Отключаемся
        await client.disconnect()
        print("✅ Отладка завершена!")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_orderbook()) 