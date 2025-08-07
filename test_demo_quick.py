#!/usr/bin/env python3
"""
Быстрый тест демо с исправлениями
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_data_manager import ComprehensiveDataManager

async def test_demo_quick():
    """Быстрый тест демо"""
    print("🚀 БЫСТРЫЙ ТЕСТ ДЕМО")
    print("=" * 30)
    
    try:
        manager = ComprehensiveDataManager()
        
        # Запуск
        await manager.start()
        print("✅ Менеджер запущен")
        
        # Подписка на один символ
        await manager.subscribe_multiple_symbols(['BTCUSDT'])
        print("✅ Подписка на BTCUSDT")
        
        # Ждем 10 секунд
        print("⏳ Ждем 10 секунд...")
        await asyncio.sleep(10)
        
        # Проверяем данные
        market_data = manager.get_market_data('BTCUSDT')
        orderbook = manager.get_orderbook_data('BTCUSDT')
        indicators = manager.get_technical_indicators('BTCUSDT', '1h')
        
        print(f"📊 Рыночные данные: {'✅' if market_data else '❌'}")
        print(f"📚 Ордербук: {'✅' if orderbook else '❌'}")
        print(f"📈 Индикаторы: {'✅' if indicators else '❌'}")
        
        # Остановка
        await manager.stop()
        print("✅ Менеджер остановлен")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_demo_quick()) 