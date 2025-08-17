#!/usr/bin/env python3
"""
Тест правил торговли для COWUSDT
"""

import requests
import json

def test_symbol_rules():
    """Тест правил торговли"""
    try:
        print("🔧 ТЕСТ ПРАВИЛ ТОРГОВЛИ COWUSDT")
        print("=" * 60)
        
        # Получаем информацию о бирже
        url = "https://api.mexc.com/api/v3/exchangeInfo"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Ищем COWUSDT
            cowusdt_info = None
            for symbol in data.get('symbols', []):
                if symbol.get('symbol') == 'COWUSDT':
                    cowusdt_info = symbol
                    break
            
            if cowusdt_info:
                print("✅ COWUSDT найден в exchange info")
                print(f"📊 Статус: {cowusdt_info.get('status')}")
                print(f"📊 Базовая валюта: {cowusdt_info.get('baseAsset')}")
                print(f"📊 Котируемая валюта: {cowusdt_info.get('quoteAsset')}")
                
                # Получаем фильтры
                filters = cowusdt_info.get('filters', [])
                print(f"\n📋 Фильтры ({len(filters)}):")
                
                for filter_info in filters:
                    filter_type = filter_info.get('filterType')
                    print(f"   {filter_type}: {filter_info}")
                
                # Ищем LOT_SIZE фильтр
                lot_size_filter = None
                for filter_info in filters:
                    if filter_info.get('filterType') == 'LOT_SIZE':
                        lot_size_filter = filter_info
                        break
                
                if lot_size_filter:
                    print(f"\n🎯 LOT_SIZE фильтр:")
                    print(f"   minQty: {lot_size_filter.get('minQty')}")
                    print(f"   maxQty: {lot_size_filter.get('maxQty')}")
                    print(f"   stepSize: {lot_size_filter.get('stepSize')}")
                    
                    # Тестируем расчет количества
                    test_amount = 6.64
                    current_price = 0.3898  # Примерная цена COWUSDT
                    raw_quantity = test_amount / current_price
                    
                    print(f"\n🧮 РАСЧЕТ КОЛИЧЕСТВА:")
                    print(f"   Сумма: ${test_amount}")
                    print(f"   Цена: ${current_price}")
                    print(f"   Сырое количество: {raw_quantity}")
                    
                    # Пробуем разные способы округления
                    min_qty = float(lot_size_filter.get('minQty', 0))
                    step_size = float(lot_size_filter.get('stepSize', 0.0001))
                    
                    print(f"\n📊 ПРАВИЛА:")
                    print(f"   minQty: {min_qty}")
                    print(f"   stepSize: {step_size}")
                    
                    # Округляем до правильного шага
                    new_quantity = round(raw_quantity / step_size) * step_size
                    
                    if new_quantity < min_qty:
                        print(f"⚠️ Количество {new_quantity} меньше минимального {min_qty}")
                        new_quantity = min_qty
                    
                    print(f"\n✅ ИТОГОВОЕ КОЛИЧЕСТВО: {new_quantity}")
                    
                else:
                    print("❌ LOT_SIZE фильтр не найден")
                    
            else:
                print("❌ COWUSDT не найден в exchange info")
                
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")

if __name__ == "__main__":
    test_symbol_rules() 