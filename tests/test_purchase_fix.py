#!/usr/bin/env python3
"""
Тест исправления ошибки покупки
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

async def test_purchase_fix():
    """Тест исправления ошибки покупки"""
    try:
        print("🔧 ТЕСТ ИСПРАВЛЕНИЯ ОШИБКИ ПОКУПКИ")
        print("=" * 60)
        print(f"Время: {datetime.now()}")
        print()
        
        # Создаем сканер
        scanner = MarketScanner()
        
        # Тестируем на конкретной монете
        test_symbol = "ADAUSDT"  # Популярная монета
        test_amount = 5.0  # $5 для теста
        
        print(f"🧪 ТЕСТИРУЕМ ПОКУПКУ:")
        print(f"   Символ: {test_symbol}")
        print(f"   Сумма: ${test_amount}")
        print()
        
        # Создаем тестовую возможность
        test_opportunity = {
            'symbol': test_symbol,
            'score': 5,
            'rsi': 30.0,
            'reasons': ['перепродано', 'низкий_rsi', 'macd_buy']
        }
        
        # Тестируем покупку (симуляция)
        print("🛒 Тестируем покупку...")
        result = await scanner.execute_purchase(test_symbol, test_amount, test_opportunity)
        
        if result['success']:
            print(f"✅ ПОКУПКА УСПЕШНА!")
            print(f"   Ордер ID: {result['order_id']}")
            print(f"   Количество: {result['quantity']}")
            print(f"   Цена: ${result['price']}")
        else:
            print(f"❌ ОШИБКА ПОКУПКИ:")
            print(f"   {result['error']}")
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        logger.error(f"Ошибка теста: {e}")

if __name__ == "__main__":
    asyncio.run(test_purchase_fix()) 