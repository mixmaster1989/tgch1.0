#!/usr/bin/env python3
"""
Тест системы ретраев с разными методами округления
"""

import asyncio
import logging
from datetime import datetime
from market_scanner import MarketScanner

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_retry_system():
    """Тест системы ретраев"""
    try:
        print("🔄 ТЕСТ СИСТЕМЫ РЕТРАЕВ")
        print("=" * 60)
        print(f"Время: {datetime.now()}")
        print()
        
        # Создаем сканер
        scanner = MarketScanner()
        
        # Тестируем на проблемной монете
        test_symbol = "BERAUSDT"  # Та же монета что в ошибке
        test_amount = 6.68  # Та же сумма
        
        print(f"🧪 ТЕСТИРУЕМ: {test_symbol}")
        print(f"💰 Сумма: ${test_amount}")
        print()
        
        # Создаем тестовую возможность
        test_opportunity = {
            'symbol': test_symbol,
            'score': 4,
            'rsi': 50.0,
            'reasons': ['высокий_объем', 'bb_нижняя']
        }
        
        print("🔄 Запускаем покупку с ретраями...")
        print("📱 Все попытки будут отправлены в Telegram")
        print()
        
        # Тестируем покупку с ретраями
        result = await scanner.execute_purchase(test_symbol, test_amount, test_opportunity)
        
        if result['success']:
            print(f"✅ ПОКУПКА УСПЕШНА!")
            print(f"   Ордер ID: {result['order_id']}")
            print(f"   Метод: {result['method']}")
            print(f"   Попытка: {result['attempt']}/6")
            print(f"   Количество: {result['quantity']}")
            print(f"   Цена: ${result['price']}")
        else:
            print(f"❌ ПОКУПКА НЕ УДАЛАСЬ:")
            print(f"   {result['error']}")
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        logger.error(f"Ошибка теста: {e}")

if __name__ == "__main__":
    asyncio.run(test_retry_system()) 