#!/usr/bin/env python3
"""
ПРОВЕРКА КОМИССИИ МЕЙКЕРА!
После продажи TRUMP
"""

from mex_api import MexAPI
import json
from datetime import datetime

print("🔍 ПРОВЕРКА КОМИССИИ МЕЙКЕРА!")
print("=" * 40)

try:
    # Создаем API объект
    api = MexAPI()
    print("✅ API инициализирован")
    
    # 1. Загружаем данные ордера
    print("📋 Загружаем данные ордера...")
    try:
        with open('trump_maker_order.json', 'r') as f:
            order_data = json.load(f)
        
        print("✅ Данные ордера загружены")
        print(f"   🆔 Ордер: {order_data['order_id']}")
        print(f"   📊 Количество: {order_data['quantity']}")
        print(f"   💰 Цена: ${order_data['price']}")
        print(f"   💵 Ожидаемая выручка: ${order_data['expected_revenue']}")
        
    except FileNotFoundError:
        print("❌ Файл trump_maker_order.json не найден")
        print("🔍 Проверяем последние ордера TRUMP...")
        order_data = None
    
    # 2. Получаем детали исполненного ордера
    print(f"\n📊 Получаем детали ордера...")
    
    if order_data:
        order_id = order_data['order_id']
        orders = api.get_order_history('TRUMPUSDT', limit=10)
    else:
        # Ищем последние ордера TRUMP
        orders = api.get_order_history('TRUMPUSDT', limit=10)
        order_id = None
    
    if not orders:
        print("❌ Нет истории ордеров TRUMP")
        exit()
    
    # Ищем исполненный SELL ордер
    executed_sell = None
    for order in orders:
        if (order.get('side') == 'SELL' and 
            order.get('status') == 'FILLED' and
            (order_id is None or order.get('orderId') == order_id)):
            executed_sell = order
            break
    
    if not executed_sell:
        print("❌ Не найден исполненный SELL ордер")
        exit()
    
    print(f"✅ Найден исполненный ордер:")
    print(f"   🆔 ID: {executed_sell.get('orderId', 'N/A')}")
    print(f"   📊 Сторона: {executed_sell.get('side', 'N/A')}")
    print(f"   📈 Статус: {executed_sell.get('status', 'N/A')}")
    print(f"   📊 Количество: {executed_sell.get('executedQty', 'N/A')}")
    print(f"   💰 Цена: ${executed_sell.get('price', 'N/A')}")
    
    # 3. АНАЛИЗ КОМИССИИ МЕЙКЕРА
    print(f"\n💰 АНАЛИЗ КОМИССИИ МЕЙКЕРА:")
    print("=" * 50)
    
    # Данные ордера
    executed_qty = float(executed_sell.get('executedQty', 0))
    executed_price = float(executed_sell.get('price', 0))
    cummulative_quote_qty = float(executed_sell.get('cummulativeQuoteQty', 0))
    
    # Расчеты
    expected_revenue = executed_qty * executed_price
    actual_revenue = cummulative_quote_qty
    
    print(f"📊 Количество: {executed_qty}")
    print(f"💰 Цена исполнения: ${executed_price}")
    print(f"💵 Ожидаемая выручка: ${expected_revenue:.6f}")
    print(f"💵 Фактическая выручка: ${actual_revenue:.6f}")
    
    # Разница (комиссия)
    difference = expected_revenue - actual_revenue
    if difference > 0:
        print(f"📉 Разница (комиссия): ${difference:.6f}")
    else:
        print(f"📈 Разница (бонус): ${abs(difference):.6f}")
    
    # Процент комиссии
    if expected_revenue > 0:
        fee_percent = (difference / expected_revenue) * 100
        print(f"📊 Комиссия: {fee_percent:.4f}%")
    
    # 4. СРАВНЕНИЕ С РЫНОЧНЫМИ ОРДЕРАМИ
    print(f"\n🔍 СРАВНЕНИЕ С РЫНОЧНЫМИ ОРДЕРАМИ:")
    print("=" * 50)
    
    # Ищем рыночные ордера для сравнения
    market_orders = []
    for order in orders:
        if (order.get('type') == 'MARKET' and 
            order.get('side') == 'SELL' and
            order.get('status') == 'FILLED'):
            market_orders.append(order)
    
    if market_orders:
        print(f"📝 Найдено рыночных ордеров: {len(market_orders)}")
        
        for i, market_order in enumerate(market_orders[:3], 1):  # Берем первые 3
            mqty = float(market_order.get('executedQty', 0))
            mprice = float(market_order.get('price', 0))
            mrevenue = float(market_order.get('cummulativeQuoteQty', 0))
            
            expected_market = mqty * mprice
            market_fee = expected_market - mrevenue
            
            print(f"\n🔸 Рыночный ордер {i}:")
            print(f"   📊 Количество: {mqty}")
            print(f"   💰 Цена: ${mprice}")
            print(f"   💵 Ожидаемая: ${expected_market:.6f}")
            print(f"   💵 Фактическая: ${mrevenue:.6f}")
            print(f"   📉 Комиссия: ${market_fee:.6f}")
            
            if expected_market > 0:
                market_fee_percent = (market_fee / expected_market) * 100
                print(f"   📊 Комиссия: {market_fee_percent:.4f}%")
    else:
        print("❌ Нет рыночных ордеров для сравнения")
    
    # 5. ИТОГИ
    print(f"\n📊 ИТОГИ АНАЛИЗА КОМИССИИ:")
    print("=" * 50)
    
    if 'fee_percent' in locals():
        if fee_percent < 0.05:
            print(f"🟢 МЕЙКЕР ОРДЕР: Низкая комиссия {fee_percent:.4f}%")
        elif fee_percent < 0.1:
            print(f"🟡 МЕЙКЕР ОРДЕР: Средняя комиссия {fee_percent:.4f}%")
        else:
            print(f"🔴 МЕЙКЕР ОРДЕР: Высокая комиссия {fee_percent:.4f}%")
    
    print(f"💡 Рекомендация: {'Используйте мейкер ордера' if 'fee_percent' in locals() and fee_percent < 0.1 else 'Проверьте настройки комиссий'}")
    
except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Анализ комиссии завершен") 