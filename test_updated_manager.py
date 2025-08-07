#!/usr/bin/env python3
"""
Тест обновленного комплексного менеджера данных с твоим WebSocket клиентом
"""

import asyncio
import logging
from comprehensive_data_manager import ComprehensiveDataManager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def orderbook_callback(orderbook_data):
    """Callback для ордербука"""
    print(f"📚 OrderBook {orderbook_data.symbol}:")
    print(f"  Спред: {orderbook_data.spread:.2f} ({orderbook_data.spread_percent:.4f}%)")
    print(f"  Bid объем: {orderbook_data.bid_volume:.2f}")
    print(f"  Ask объем: {orderbook_data.ask_volume:.2f}")
    print(f"  Уровней покупки: {len(orderbook_data.bids)}")
    print(f"  Уровней продажи: {len(orderbook_data.asks)}")

async def trade_callback(trade_data):
    """Callback для сделок"""
    print(f"💱 Trade {trade_data.symbol}: {trade_data.side} {trade_data.quantity} @ {trade_data.price}")

async def market_callback(market_data):
    """Callback для рыночных данных"""
    print(f"📊 Market update: {len(market_data)} символов")
    for symbol, data in list(market_data.items())[:3]:  # Показываем первые 3
        print(f"  {symbol}: ${data.price:.6f}")

async def test_updated_manager():
    """Тест обновленного менеджера"""
    print("🧪 ТЕСТ ОБНОВЛЕННОГО КОМПЛЕКСНОГО МЕНЕДЖЕРА")
    print("=" * 60)
    
    manager = ComprehensiveDataManager()
    
    # Подписываемся на callbacks
    manager.subscribe_orderbook_updates(orderbook_callback)
    manager.subscribe_trade_updates(trade_callback)
    manager.subscribe_market_updates(market_callback)
    
    try:
        # Запускаем менеджер
        print("🚀 Запуск менеджера...")
        await manager.start()
        
        # Подписываемся на символы
        print("📡 Подписка на символы...")
        await manager.subscribe_multiple_symbols(['BTCUSDT', 'ETHUSDT'])
        
        # Ждем данные
        print("⏳ Ожидание данных (30 секунд)...")
        await asyncio.sleep(30)
        
        # Получаем данные
        print("\n📊 ПОЛУЧЕННЫЕ ДАННЫЕ:")
        
        # Рыночные данные
        market_data = manager.get_market_data()
        print(f"  Рыночных символов: {len(market_data)}")
        
        # Ордербук
        btc_orderbook = manager.get_orderbook_data('BTCUSDT')
        if btc_orderbook:
            print(f"  BTC OrderBook: {len(btc_orderbook.bids)} bids, {len(btc_orderbook.asks)} asks")
            print(f"  Спред: {btc_orderbook.spread:.2f} ({btc_orderbook.spread_percent:.4f}%)")
        
        # Сделки
        btc_trades = manager.get_trade_history('BTCUSDT')
        if btc_trades:
            print(f"  BTC сделок: {len(btc_trades.trades)}")
        
        # Кандидаты для торговли
        candidates = manager.get_trading_candidates()
        print(f"  Кандидатов для торговли: {len(candidates)}")
        
        print("\n✅ Тест завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("🛑 Остановка менеджера...")
        await manager.stop()

if __name__ == "__main__":
    asyncio.run(test_updated_manager()) 