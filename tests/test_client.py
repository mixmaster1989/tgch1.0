#!/usr/bin/env python3
"""
Простой тест WebSocket клиента MEXC
"""

import asyncio
import logging
from mexc_websocket_client import MEXCWebSocketClient, StreamType

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def simple_trade_callback(trade_data):
    """Простой callback для сделок"""
    print(f"💱 {trade_data['symbol']}: {trade_data['price']} x {trade_data['quantity']} ({trade_data['trade_type']})")

async def simple_orderbook_callback(order_book):
    """Простой callback для ордербука"""
    best_bid = order_book.get_best_bid()
    best_ask = order_book.get_best_ask()
    
    if best_bid and best_ask:
        spread = float(best_ask[0]) - float(best_bid[0])
        print(f"📚 {order_book.symbol}: Bid {best_bid[0]} | Ask {best_ask[0]} | Spread {spread:.2f}")

async def test_basic_connection():
    """Тест базового подключения"""
    print("🔌 Тест базового подключения...")
    
    client = MEXCWebSocketClient()
    
    try:
        await client.connect()
        print("✅ Подключение успешно")
        
        # Простой ping
        await client.ping()
        print("✅ Ping отправлен")
        
        await client.disconnect()
        print("✅ Отключение успешно")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def test_trades_stream():
    """Тест потока сделок"""
    print("\n💱 Тест потока сделок...")
    
    client = MEXCWebSocketClient()
    
    try:
        await client.connect()
        
        # Подписка на сделки
        await client.subscribe(
            StreamType.TRADES,
            "BTCUSDT",
            interval="100ms",
            callback=simple_trade_callback
        )
        
        print("📡 Ожидание сделок (10 секунд)...")
        await asyncio.sleep(10)
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def test_orderbook():
    """Тест ордербука"""
    print("\n📚 Тест ордербука...")
    
    client = MEXCWebSocketClient()
    
    try:
        await client.connect()
        
        # Загрузка снапшота
        print("📥 Загрузка снапшота...")
        await client.load_order_book_snapshot("BTCUSDT")
        
        # Подписка на глубину
        await client.subscribe(
            StreamType.DEPTH,
            "BTCUSDT",
            interval="100ms",
            callback=simple_orderbook_callback
        )
        
        print("📡 Ожидание обновлений ордербука (10 секунд)...")
        await asyncio.sleep(10)
        
        # Показать текущее состояние
        order_book = client.get_order_book("BTCUSDT")
        if order_book:
            print(f"\n📊 Текущий ордербук {order_book.symbol}:")
            print(f"  Уровней покупки: {len(order_book.bids)}")
            print(f"  Уровней продажи: {len(order_book.asks)}")
            
            best_bid = order_book.get_best_bid()
            best_ask = order_book.get_best_ask()
            
            if best_bid and best_ask:
                print(f"  Лучшая покупка: {best_bid[0]} ({best_bid[1]})")
                print(f"  Лучшая продажа: {best_ask[0]} ({best_ask[1]})")
                print(f"  Спред: {float(best_ask[0]) - float(best_bid[0]):.2f}")
        
        await client.disconnect()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def main():
    """Основная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ MEXC WEB SOCKET CLIENT")
    print("=" * 50)
    
    # Тест 1: Базовое подключение
    await test_basic_connection()
    
    # Тест 2: Поток сделок
    await test_trades_stream()
    
    # Тест 3: Ордербук
    await test_orderbook()
    
    print("\n✅ Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(main()) 