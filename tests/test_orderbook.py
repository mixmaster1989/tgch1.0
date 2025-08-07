#!/usr/bin/env python3
"""
Тест Order Book функциональности
"""

import asyncio
import json
from datetime import datetime
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from comprehensive_data_manager import ComprehensiveDataManager, OrderBookData, TradeData, TradeHistoryData

async def test_orderbook_functionality():
    """Тест Order Book функциональности"""
    print("🧪 Тестирование Order Book функциональности...")
    
    # Создаем менеджер данных
    data_manager = ComprehensiveDataManager()
    
    # Тестовые данные Order Book
    test_orderbook_data = {
        'bids': [
            ['114000.00', '0.5'],
            ['113999.00', '1.2'],
            ['113998.00', '0.8']
        ],
        'asks': [
            ['114001.00', '0.8'],
            ['114002.00', '1.5'],
            ['114003.00', '0.6']
        ]
    }
    
    # Тестируем обработку Order Book данных
    print("📊 Тестирование обработки Order Book данных...")
    orderbook = data_manager._process_orderbook_data('BTCUSDT', test_orderbook_data)
    
    if orderbook:
        print(f"✅ Order Book создан успешно:")
        print(f"   Символ: {orderbook.symbol}")
        print(f"   Спред: ${orderbook.spread:.2f} ({orderbook.spread_percent:.4f}%)")
        print(f"   Объем bids: {orderbook.bid_volume}")
        print(f"   Объем asks: {orderbook.ask_volume}")
        print(f"   Соотношение объемов: {orderbook.volume_ratio:.2f}")
        print(f"   Оценка ликвидности: {orderbook.liquidity_score:.2f}")
        print(f"   Top 3 bids: {orderbook.bids[:3]}")
        print(f"   Top 3 asks: {orderbook.asks[:3]}")
    else:
        print("❌ Ошибка создания Order Book")
        return False
    
    # Тестируем кэширование Order Book
    print("\n💾 Тестирование кэширования Order Book...")
    cached_orderbook = data_manager.get_orderbook_data('BTCUSDT')
    if cached_orderbook:
        print(f"✅ Order Book найден в кэше: {cached_orderbook.symbol}")
    else:
        print("❌ Order Book не найден в кэше")
    
    # Тестовые данные сделки
    test_trade_data = {
        'price': '114000.50',
        'quantity': '0.1',
        'side': 'BUY',
        'timestamp': int(datetime.now().timestamp() * 1000)
    }
    
    # Тестируем обработку данных сделки
    print("\n💱 Тестирование обработки данных сделки...")
    trade = data_manager._process_trade_data('BTCUSDT', test_trade_data)
    
    if trade:
        print(f"✅ Сделка создана успешно:")
        print(f"   Символ: {trade.symbol}")
        print(f"   Цена: ${trade.price}")
        print(f"   Количество: {trade.quantity}")
        print(f"   Сторона: {trade.side}")
        print(f"   Время: {datetime.fromtimestamp(trade.timestamp / 1000)}")
    else:
        print("❌ Ошибка создания сделки")
        return False
    
    # Тестируем историю сделок
    print("\n📈 Тестирование истории сделок...")
    trade_history = data_manager.get_trade_history('BTCUSDT')
    if trade_history:
        print(f"✅ История сделок найдена:")
        print(f"   Символ: {trade_history.symbol}")
        print(f"   Количество сделок: {len(trade_history.trades)}")
        print(f"   Объем покупок: {trade_history.buy_volume}")
        print(f"   Объем продаж: {trade_history.sell_volume}")
        print(f"   Соотношение объемов: {trade_history.volume_ratio:.2f}")
        print(f"   Средний размер сделки: {trade_history.avg_trade_size:.4f}")
    else:
        print("❌ История сделок не найдена")
    
    # Тестируем callbacks
    print("\n🔄 Тестирование callbacks...")
    
    orderbook_callback_called = False
    trade_callback_called = False
    
    async def orderbook_callback(orderbook_data):
        nonlocal orderbook_callback_called
        orderbook_callback_called = True
        print(f"   📊 Order Book callback: {orderbook_data.symbol}")
    
    async def trade_callback(trade_data):
        nonlocal trade_callback_called
        trade_callback_called = True
        print(f"   💱 Trade callback: {trade_data.symbol}")
    
    # Подписываемся на обновления
    data_manager.subscribe_orderbook_updates(orderbook_callback)
    data_manager.subscribe_trade_updates(trade_callback)
    
    print(f"   Подписки на Order Book: {len(data_manager.orderbook_callbacks)}")
    print(f"   Подписки на Trade: {len(data_manager.trade_callbacks)}")
    
    # Тестируем Redis кэш
    print("\n🔴 Тестирование Redis кэша...")
    from cache.redis_manager import RedisCacheManager
    redis_cache = RedisCacheManager()
    
    # Сохраняем Order Book в Redis
    redis_cache.set_orderbook('BTCUSDT', orderbook.to_dict())
    
    # Получаем из Redis
    cached_data = redis_cache.get_orderbook('BTCUSDT')
    if cached_data:
        print(f"✅ Order Book сохранен в Redis: {cached_data['orderbook']['symbol']}")
    else:
        print("❌ Order Book не найден в Redis")
    
    # Сохраняем историю сделок в Redis
    if trade_history:
        redis_cache.set_trade_history('BTCUSDT', trade_history.to_dict())
        
        # Получаем из Redis
        cached_trades = redis_cache.get_trade_history('BTCUSDT')
        if cached_trades:
            print(f"✅ История сделок сохранена в Redis: {cached_trades['trades']['symbol']}")
        else:
            print("❌ История сделок не найдена в Redis")
    
    # Статистика кэша
    stats = redis_cache.get_cache_stats()
    print(f"\n📊 Статистика кэша:")
    print(f"   Всего ключей: {stats['total_keys']}")
    print(f"   Использование памяти: {stats['memory_usage']}")
    print(f"   Ключи по типам: {stats['keys_by_type']}")
    
    print("\n🎉 Тест Order Book функциональности завершен!")
    return True

async def test_orderbook_integration():
    """Тест интеграции Order Book с основным менеджером"""
    print("\n🔗 Тестирование интеграции Order Book...")
    
    # Создаем менеджер данных
    data_manager = ComprehensiveDataManager()
    
    # Запускаем менеджер
    print("🚀 Запуск комплексного менеджера данных...")
    await data_manager.start()
    
    # Ждем немного для сбора данных
    print("⏳ Ожидание сбора данных...")
    await asyncio.sleep(5)
    
    # Проверяем данные
    print("📊 Проверка собранных данных...")
    
    # Получаем данные для основных активов
    major_assets = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    
    for symbol in major_assets:
        print(f"\n🔍 Проверка {symbol}:")
        
        # Рыночные данные
        market_data = data_manager.get_market_data(symbol)
        if market_data:
            print(f"   ✅ Рыночные данные: ${market_data.price}")
        
        # Order Book данные
        orderbook_data = data_manager.get_orderbook_data(symbol)
        if orderbook_data:
            print(f"   ✅ Order Book: спред {orderbook_data.spread_percent:.4f}%")
        else:
            print(f"   ⚠️ Order Book: нет данных")
        
        # История сделок
        trade_history = data_manager.get_trade_history(symbol)
        if trade_history:
            print(f"   ✅ История сделок: {len(trade_history.trades)} сделок")
        else:
            print(f"   ⚠️ История сделок: нет данных")
    
    # Останавливаем менеджер
    print("\n🛑 Остановка менеджера...")
    await data_manager.stop()
    
    print("✅ Тест интеграции завершен!")

if __name__ == "__main__":
    # Запускаем тесты
    asyncio.run(test_orderbook_functionality())
    asyncio.run(test_orderbook_integration()) 