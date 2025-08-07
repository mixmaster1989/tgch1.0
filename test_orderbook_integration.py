#!/usr/bin/env python3
"""
Тест интеграции Order Book
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_data_manager import ComprehensiveDataManager

async def test_orderbook_integration():
    """Тест интеграции Order Book"""
    print("🧪 ТЕСТ ИНТЕГРАЦИИ ORDER BOOK")
    print("=" * 50)
    
    manager = ComprehensiveDataManager()
    
    # Счетчики
    orderbook_updates = 0
    trade_updates = 0
    
    # Callbacks
    async def orderbook_callback(data):
        nonlocal orderbook_updates
        orderbook_updates += 1
        print(f"📊 Order Book #{orderbook_updates}: {data.symbol}")
        print(f"   Спред: ${data.spread:.4f} ({data.spread_percent:.4f}%)")
        print(f"   Ликвидность: {data.liquidity_score:.2f}")
        print(f"   Top bid: ${data.bids[0][0]:.6f} ({data.bids[0][1]:.4f})")
        print(f"   Top ask: ${data.asks[0][0]:.6f} ({data.asks[0][1]:.4f})")
    
    async def trade_callback(data):
        nonlocal trade_updates
        trade_updates += 1
        print(f"💱 Trade #{trade_updates}: {data.symbol} {data.side}")
        print(f"   Цена: ${data.price:.6f}, Количество: {data.quantity:.4f}")
    
    # Подписываемся
    manager.subscribe_orderbook_updates(orderbook_callback)
    manager.subscribe_trade_updates(trade_callback)
    
    try:
        print("🚀 Запуск менеджера...")
        await manager.start()
        
        print("📡 Подписка на символы...")
        await manager.subscribe_multiple_symbols(['BTCUSDT', 'ETHUSDT'])
        
        print("⏳ Ожидание данных (30 секунд)...")
        await asyncio.sleep(30)
        
        print("\n📊 РЕЗУЛЬТАТЫ:")
        print(f"  Order Book обновлений: {orderbook_updates}")
        print(f"  Trade обновлений: {trade_updates}")
        
        # Проверяем данные
        btc_orderbook = manager.get_orderbook_data('BTCUSDT')
        if btc_orderbook:
            print(f"✅ BTC Order Book найден:")
            print(f"   Спред: {btc_orderbook.spread_percent:.4f}%")
            print(f"   Ликвидность: {btc_orderbook.liquidity_score:.2f}")
        else:
            print("❌ BTC Order Book не найден")
        
        eth_orderbook = manager.get_orderbook_data('ETHUSDT')
        if eth_orderbook:
            print(f"✅ ETH Order Book найден:")
            print(f"   Спред: {eth_orderbook.spread_percent:.4f}%")
            print(f"   Ликвидность: {eth_orderbook.liquidity_score:.2f}")
        else:
            print("❌ ETH Order Book не найден")
        
        print("\n✅ Тест завершен!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        await manager.stop()

if __name__ == "__main__":
    asyncio.run(test_orderbook_integration()) 