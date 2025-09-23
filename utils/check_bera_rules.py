#!/usr/bin/env python3
"""
Проверка правил торговли для BERAUSDT
"""

from mexc_advanced_api import MexAdvancedAPI
import json

def check_bera_rules():
    """Проверяем правила торговли BERA"""
    try:
        print("🔍 ПРОВЕРКА ПРАВИЛ BERAUSDT")
        print("=" * 50)
        
        api = MexAdvancedAPI()
        
        # Получаем правила
        rules = api.get_symbol_rules("BERAUSDT")
        
        print(f"📊 Правила BERAUSDT:")
        print(json.dumps(rules, indent=2, ensure_ascii=False))
        
        if rules:
            print(f"\n📈 min_qty: {rules.get('min_qty', 'НЕТ')}")
            print(f"📊 step_size: {rules.get('step_size', 'НЕТ')}")
            print(f"💰 min_notional: {rules.get('min_notional', 'НЕТ')}")
        else:
            print("❌ Правила не найдены")
            
        # Проверяем текущую цену
        ticker = api.get_ticker_price("BERAUSDT")
        if ticker:
            price = float(ticker['price'])
            print(f"\n💵 Текущая цена BERA: ${price}")
            
            # Рассчитываем количество для $6.68
            amount = 6.68
            raw_quantity = amount / price
            print(f"📊 Сырое количество для ${amount}: {raw_quantity}")
            
            # Пробуем разные округления
            print(f"\n🔄 РАЗНЫЕ МЕТОДЫ ОКРУГЛЕНИЯ:")
            print(f"2 знака: {round(raw_quantity, 2)}")
            print(f"3 знака: {round(raw_quantity, 3)}")
            print(f"4 знака: {round(raw_quantity, 4)}")
            print(f"5 знаков: {round(raw_quantity, 5)}")
            print(f"6 знаков: {round(raw_quantity, 6)}")
            print(f"8 знаков: {round(raw_quantity, 8)}")
            
            # Пробуем с правилами биржи
            if rules:
                quantity_precision = rules.get('quantityPrecision', 8)
                step_size = rules.get('stepSize', 1e-08)
                print(f"\n📊 ПО ПРАВИЛАМ БИРЖИ:")
                print(f"Точность: {quantity_precision} знаков")
                print(f"Шаг: {step_size}")
                print(f"Округление: {round(raw_quantity, quantity_precision)}")
                if step_size > 0:
                    step_rounded = round(raw_quantity / step_size) * step_size
                    print(f"По шагу: {step_rounded}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_bera_rules() 