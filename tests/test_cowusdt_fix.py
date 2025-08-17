#!/usr/bin/env python3
"""
Тест исправления ошибки с COWUSDT
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

async def test_cowusdt_fix():
    """Тест исправления COWUSDT"""
    try:
        print("🔧 ТЕСТ ИСПРАВЛЕНИЯ COWUSDT")
        print("=" * 60)
        print(f"Время: {datetime.now()}")
        print()
        
        # Создаем сканер
        scanner = MarketScanner()
        
        # Тестируем на проблемной монете
        test_symbol = "COWUSDT"
        test_amount = 6.64  # Та же сумма что в ошибке
        
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
            
            # Анализируем ошибку
            if 'quantity scale is invalid' in result['error']:
                print("\n🔍 АНАЛИЗ ОШИБКИ:")
                print("   Проблема: Неправильное округление количества")
                print("   Решение: Использовать fallback логику с 3 знаками")
            elif 'Insufficient balance' in result['error']:
                print("\n🔍 АНАЛИЗ ОШИБКИ:")
                print("   Проблема: Недостаточно средств")
                print("   Решение: Проверить баланс USDT")
            else:
                print("\n🔍 АНАЛИЗ ОШИБКИ:")
                print("   Проблема: Другая ошибка API")
                print("   Решение: Проверить логи")
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        logger.error(f"Ошибка теста: {e}")

if __name__ == "__main__":
    asyncio.run(test_cowusdt_fix()) 