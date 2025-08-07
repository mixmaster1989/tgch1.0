#!/usr/bin/env python3
"""
Пример использования MEXC WebSocket Client
Демонстрация работы с ордербуком и другими потоками данных
"""

import asyncio
import json
from datetime import datetime
from mexc_websocket_client import MEXCWebSocketClient, WebSocketConfig, StreamType

async def trade_callback(trade_data):
    """Callback для обработки сделок"""
    print(f"💱 СДЕЛКА: {trade_data['symbol']} | "
          f"Цена: {trade_data['price']} | "
          f"Объем: {trade_data['quantity']} | "
          f"Тип: {trade_data['trade_type']}")

async def kline_callback(kline_data):
    """Callback для обработки свечей"""
    print(f"📊 СВЕЧА: {kline_data['symbol']} | "
          f"Интервал: {kline_data['interval']} | "
          f"Цена: {kline_data['close']} | "
          f"Объем: {kline_data['volume']}")

async def orderbook_callback(order_book):
    """Callback для обработки ордербука"""
    best_bid = order_book.get_best_bid()
    best_ask = order_book.get_best_ask()
    spread = order_book.get_spread()
    
    if best_bid and best_ask:
        print(f"📚 ОРДЕРБУК: {order_book.symbol} | "
              f"Лучшая покупка: {best_bid[0]} ({best_bid[1]}) | "
              f"Лучшая продажа: {best_ask[0]} ({best_ask[1]}) | "
              f"Спред: {spread:.2f}")

async def book_ticker_callback(ticker_data):
    """Callback для обработки лучших цен"""
    print(f"🎯 BOOK TICKER: {ticker_data['symbol']} | "
          f"Bid: {ticker_data['bid_price']} ({ticker_data['bid_quantity']}) | "
          f"Ask: {ticker_data['ask_price']} ({ticker_data['ask_quantity']})")

async def limit_depth_callback(depth_data):
    """Callback для обработки ограниченной глубины"""
    print(f"📖 LIMIT DEPTH: {depth_data['symbol']} | "
          f"Bids: {len(depth_data['bids'])} | "
          f"Asks: {len(depth_data['asks'])} | "
          f"Version: {depth_data['version']}")

async def main():
    """Основная функция примера"""
    print("🚀 ЗАПУСК ПРИМЕРА MEXC WEB SOCKET CLIENT")
    print("=" * 60)
    
    # Конфигурация
    config = WebSocketConfig(
        url="wss://wbs-api.mexc.com/ws",
        ping_interval=30,
        reconnect_delay=5,
        max_reconnect_attempts=10
    )
    
    # Создание клиента
    client = MEXCWebSocketClient(config)
    
    try:
        # Подключение
        print("🔌 Подключение к WebSocket...")
        await client.connect()
        
        # Загрузка снапшота ордербука для BTCUSDT
        print("📥 Загрузка снапшота ордербука...")
        await client.load_order_book_snapshot("BTCUSDT")
        
        # Подписки на различные потоки данных
        symbol = "BTCUSDT"
        
        print(f"📡 Подписка на потоки данных для {symbol}...")
        
        # Подписка на сделки
        await client.subscribe(
            StreamType.TRADES, 
            symbol, 
            interval="100ms",
            callback=trade_callback
        )
        
        # Подписка на свечи
        await client.subscribe(
            StreamType.KLINES, 
            symbol, 
            interval="Min1",
            callback=kline_callback
        )
        
        # Подписка на глубину рынка (для ордербука)
        await client.subscribe(
            StreamType.DEPTH, 
            symbol, 
            interval="100ms",
            callback=orderbook_callback
        )
        
        # Подписка на лучшие цены
        await client.subscribe(
            StreamType.BOOK_TICKER, 
            symbol, 
            interval="100ms",
            callback=book_ticker_callback
        )
        
        # Подписка на ограниченную глубину
        await client.subscribe(
            StreamType.DEPTH_LIMIT, 
            symbol, 
            levels=5,
            callback=limit_depth_callback
        )
        
        print("✅ Все подписки активны")
        print("📊 Ожидание данных... (Ctrl+C для остановки)")
        print("=" * 60)
        
        # Прослушивание сообщений
        await client.listen()
        
    except KeyboardInterrupt:
        print("\n⏹️ Остановка по запросу пользователя")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        # Отключение
        print("🔌 Отключение...")
        await client.disconnect()
        print("✅ Отключено")

async def orderbook_example():
    """Пример работы только с ордербуком"""
    print("\n📚 ПРИМЕР РАБОТЫ С ОРДЕРБУКОМ")
    print("=" * 60)
    
    config = WebSocketConfig()
    client = MEXCWebSocketClient(config)
    
    try:
        await client.connect()
        
        symbol = "BTCUSDT"
        
        # Загрузка снапшота
        await client.load_order_book_snapshot(symbol)
        
        # Подписка на глубину рынка
        await client.subscribe(
            StreamType.DEPTH, 
            symbol, 
            interval="100ms"
        )
        
        print(f"📊 Мониторинг ордербука {symbol}...")
        print("=" * 60)
        
        # Мониторинг ордербука каждые 5 секунд
        for i in range(12):  # 1 минута
            await asyncio.sleep(5)
            
            order_book = client.get_order_book(symbol)
            if order_book and order_book.snapshot_loaded:
                best_bid = order_book.get_best_bid()
                best_ask = order_book.get_best_ask()
                spread = order_book.get_spread()
                
                print(f"⏰ {datetime.now().strftime('%H:%M:%S')} | "
                      f"Bid: {best_bid[0] if best_bid else 'N/A'} | "
                      f"Ask: {best_ask[0] if best_ask else 'N/A'} | "
                      f"Spread: {spread:.2f if spread else 'N/A'}")
                
                # Показать топ-5 уровней
                print("  Top 5 Bids:")
                sorted_bids = sorted(order_book.bids.items(), key=lambda x: float(x[0]), reverse=True)[:5]
                for price, qty in sorted_bids:
                    print(f"    {price}: {qty}")
                    
                print("  Top 5 Asks:")
                sorted_asks = sorted(order_book.asks.items(), key=lambda x: float(x[0]))[:5]
                for price, qty in sorted_asks:
                    print(f"    {price}: {qty}")
                print("-" * 40)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    # Запуск основного примера
    asyncio.run(main())
    
    # Запуск примера с ордербуком
    # asyncio.run(orderbook_example()) 