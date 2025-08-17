#!/usr/bin/env python3
"""
Отладка ошибки quantity scale is invalid
"""

import asyncio
import logging
from datetime import datetime
from market_scanner import MarketScanner
from mexc_advanced_api import MexAdvancedAPI

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def debug_quantity_scale():
    """Отладка ошибки quantity scale"""
    try:
        print("🔧 ОТЛАДКА ОШИБКИ QUANTITY SCALE")
        print("=" * 60)
        print(f"Время: {datetime.now()}")
        print()
        
        # Тестируем на проблемной монете
        test_symbol = "COWUSDT"
        test_amount = 6.64  # Та же сумма что в ошибке
        
        print(f"🧪 ТЕСТИРУЕМ: {test_symbol}")
        print(f"💰 Сумма: ${test_amount}")
        print()
        
        # 1. Получаем правила торговли
        print("1️⃣ ПОЛУЧАЕМ ПРАВИЛА ТОРГОВЛИ:")
        print("-" * 30)
        
        advanced_api = MexAdvancedAPI()
        symbol_rules = advanced_api.get_symbol_rules(test_symbol)
        
        print(f"📊 Правила для {test_symbol}:")
        if symbol_rules:
            for key, value in symbol_rules.items():
                print(f"   {key}: {value}")
        else:
            print("   ❌ Правила не получены")
        print()
        
        # 2. Получаем текущую цену
        print("2️⃣ ПОЛУЧАЕМ ТЕКУЩУЮ ЦЕНУ:")
        print("-" * 30)
        
        from mex_api import MexAPI
        mex_api = MexAPI()
        ticker = mex_api.get_ticker_price(test_symbol)
        
        if ticker and 'price' in ticker:
            current_price = float(ticker['price'])
            print(f"💵 Текущая цена: ${current_price}")
            
            # 3. Рассчитываем количество
            print("3️⃣ РАССЧИТЫВАЕМ КОЛИЧЕСТВО:")
            print("-" * 30)
            
            raw_quantity = test_amount / current_price
            print(f"📊 Сырое количество: {raw_quantity}")
            
            # 4. Пробуем разные способы округления
            print("4️⃣ ПРОБУЕМ ОКРУГЛЕНИЕ:")
            print("-" * 30)
            
            # Старый способ
            if 'BTC' in test_symbol:
                old_quantity = round(raw_quantity, 6)
            elif 'ETH' in test_symbol:
                old_quantity = round(raw_quantity, 5)
            else:
                old_quantity = round(raw_quantity, 4)
            
            print(f"📊 Старый способ: {old_quantity}")
            
            # Новый способ с правилами
            if symbol_rules and 'min_qty' in symbol_rules:
                min_qty = symbol_rules['min_qty']
                step_size = symbol_rules.get('step_size', 0.0001)
                
                # Округляем до правильного шага
                new_quantity = round(raw_quantity / step_size) * step_size
                
                # Проверяем минимальное количество
                if new_quantity < min_qty:
                    print(f"⚠️ Количество {new_quantity} меньше минимального {min_qty}")
                    new_quantity = min_qty
                
                print(f"📊 Новый способ: {new_quantity}")
                print(f"📊 Минимум: {min_qty}")
                print(f"📊 Шаг: {step_size}")
            else:
                print("❌ Не удалось получить правила для нового способа")
                new_quantity = old_quantity
            
            # 5. Тестируем размещение ордера
            print("5️⃣ ТЕСТИРУЕМ РАЗМЕЩЕНИЕ ОРДЕРА:")
            print("-" * 30)
            
            # Тестируем старый способ
            print(f"🔄 Тестируем старый способ: {old_quantity}")
            try:
                old_order = mex_api.place_order(
                    symbol=test_symbol,
                    side='BUY',
                    quantity=old_quantity,
                    price=None
                )
                if 'orderId' in old_order:
                    print(f"✅ Старый способ РАБОТАЕТ: {old_order['orderId']}")
                else:
                    print(f"❌ Старый способ НЕ РАБОТАЕТ: {old_order}")
            except Exception as e:
                print(f"❌ Старый способ ОШИБКА: {e}")
            
            # Тестируем новый способ
            print(f"🔄 Тестируем новый способ: {new_quantity}")
            try:
                new_order = mex_api.place_order(
                    symbol=test_symbol,
                    side='BUY',
                    quantity=new_quantity,
                    price=None
                )
                if 'orderId' in new_order:
                    print(f"✅ Новый способ РАБОТАЕТ: {new_order['orderId']}")
                else:
                    print(f"❌ Новый способ НЕ РАБОТАЕТ: {new_order}")
            except Exception as e:
                print(f"❌ Новый способ ОШИБКА: {e}")
            
        else:
            print("❌ Не удалось получить цену")
            
    except Exception as e:
        print(f"❌ Ошибка отладки: {e}")
        logger.error(f"Ошибка отладки: {e}")

if __name__ == "__main__":
    asyncio.run(debug_quantity_scale()) 