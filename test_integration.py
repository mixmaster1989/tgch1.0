#!/usr/bin/env python3
"""
Тест интеграции БД в comprehensive_data_manager
"""

import asyncio
import time
from comprehensive_data_manager import ComprehensiveDataManager

async def test_integration():
    """Тест интеграции БД"""
    print("🧪 Тест интеграции БД в comprehensive_data_manager...")
    
    # Создаем менеджер
    manager = ComprehensiveDataManager()
    
    try:
        # Запускаем менеджер
        await manager.start()
        
        # Подписываемся на символы в WebSocket
        await manager.subscribe_multiple_symbols(['BTCUSDT', 'ETHUSDT'])
        
        # Ждем немного чтобы WebSocket подключился
        await asyncio.sleep(5)
        
        print("⏳ Собираем данные 60 секунд...")
        await asyncio.sleep(60)
        
        # Проверяем что данные сохраняются в БД
        print("📊 Проверяем сохранение данных в БД...")
        
        # Загружаем исторические цены
        btc_prices = manager.load_historical_prices('BTCUSDT', 10)
        eth_prices = manager.load_historical_prices('ETHUSDT', 10)
        
        print(f"💰 BTC цены в БД: {len(btc_prices)} записей")
        print(f"💰 ETH цены в БД: {len(eth_prices)} записей")
        
        # Загружаем исторические свечи
        btc_klines = manager.load_historical_klines('BTCUSDT', '1h', 10)
        eth_klines = manager.load_historical_klines('ETHUSDT', '1h', 10)
        
        print(f"📈 BTC свечи в БД: {len(btc_klines)} записей")
        print(f"📈 ETH свечи в БД: {len(eth_klines)} записей")
        
        # Проверяем кэш
        print("⚡ Проверяем Redis кэш...")
        btc_cached_price = manager.redis_cache.get_price('BTCUSDT')
        eth_cached_price = manager.redis_cache.get_price('ETHUSDT')
        
        print(f"💰 BTC цена в кэше: {btc_cached_price}")
        print(f"💰 ETH цена в кэше: {eth_cached_price}")
        
        # Получаем текущие данные
        market_data = manager.get_market_data()
        print(f"📊 Текущие рыночные данные: {len(market_data)} символов")
        
        # Получаем кандидатов для торговли
        candidates = manager.get_trading_candidates()
        print(f"🎯 Кандидаты для торговли: {len(candidates)} символов")
        
        print("✅ Тест интеграции завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        
    finally:
        # Останавливаем менеджер
        await manager.stop()

if __name__ == "__main__":
    asyncio.run(test_integration()) 