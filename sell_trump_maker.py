#!/usr/bin/env python3
"""
ПРОДАЖА TRUMP МЕЙКЕРНЫМ ОРДЕРОМ!
Проверяем комиссию мейкера
"""

from mex_api import MexAPI
import json
from datetime import datetime

print("🚀 ПРОДАЖА TRUMP МЕЙКЕРНЫМ ОРДЕРОМ!")
print("=" * 50)

try:
    # Создаем API объект
    api = MexAPI()
    print("✅ API инициализирован")
    
    # 1. Проверяем баланс TRUMP
    print("🔍 Проверяем баланс TRUMP...")
    account_info = api.get_account_info()
    
    trump_balance = 0.0
    for balance in account_info['balances']:
        if balance['asset'] == 'TRUMP':
            trump_balance = float(balance['free'])
            break
    
    if trump_balance <= 0:
        print("❌ TRUMP не найден в балансе")
        exit()
    
    print(f"💰 Найден TRUMP: {trump_balance}")
    
    # 2. Получаем текущую цену TRUMP
    print("📊 Получаем цену TRUMP...")
    ticker = api.get_ticker_price('TRUMPUSDT')
    
    if not ticker or 'price' not in ticker:
        print("❌ Не удалось получить цену TRUMP")
        exit()
    
    current_price = float(ticker['price'])
    current_value = trump_balance * current_price
    
    print(f"💵 Текущая цена: ${current_price}")
    print(f"💰 Текущая стоимость: ${current_value:.4f}")
    
    # 3. Получаем лучшие bid/ask для мейкерного ордера
    print("🔍 Получаем лучшие bid/ask...")
    
    # Для мейкерного ордера используем цену чуть ниже текущей
    print("📊 Используем текущую цену для мейкерного ордера")
    maker_price = current_price * 0.999  # На 0.1% ниже текущей цены
    
    print(f"🎯 Цена мейкерного ордера: ${maker_price:.6f}")
    
    # 4. Рассчитываем ожидаемую выручку
    expected_revenue = trump_balance * maker_price
    print(f"💵 Ожидаемая выручка: ${expected_revenue:.4f}")
    
    # 5. ПОДТВЕРЖДЕНИЕ ПРОДАЖИ
    print(f"\n🚨 ПРОДАЕМ {trump_balance} TRUMP по ${maker_price:.6f}?")
    print(f"💵 Ожидаемая выручка: ${expected_revenue:.4f}")
    
    confirm = input("\nПРОДАТЬ TRUMP мейкерным ордером? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ Продажа отменена")
        exit()
    
    # 6. ПРОДАЕМ TRUMP МЕЙКЕРНЫМ ОРДЕРОМ
    print(f"🔥 ВЫПОЛНЯЕМ ПРОДАЖУ TRUMP...")
    
    # Округляем количество до 6 знаков
    quantity = round(trump_balance, 6)
    
    # Размещаем ЛИМИТНЫЙ ордер (мейкер)
    order = api.place_order(
        symbol='TRUMPUSDT',
        side='SELL',
        quantity=quantity,
        price=maker_price  # ЛИМИТНЫЙ ОРДЕР!
    )
    
    if order and 'orderId' in order:
        print(f"✅ TRUMP ПРОДАН МЕЙКЕРНЫМ ОРДЕРОМ!")
        print(f"🆔 Ордер: {order['orderId']}")
        print(f"📊 Количество: {quantity}")
        print(f"💰 Цена: ${maker_price:.6f}")
        print(f"💵 Ожидаемая выручка: ${expected_revenue:.4f}")
        print(f"📈 Тип: ЛИМИТНЫЙ (мейкер)")
        
        # 7. ЖДЕМ ИСПОЛНЕНИЯ И ПРОВЕРЯЕМ КОМИССИЮ
        print(f"\n⏳ Ждем исполнения ордера...")
        print(f"🔍 После исполнения проверим комиссию мейкера!")
        
        # Сохраняем данные для анализа
        order_data = {
            'order_id': order['orderId'],
            'symbol': 'TRUMPUSDT',
            'side': 'SELL',
            'quantity': quantity,
            'price': maker_price,
            'expected_revenue': expected_revenue,
            'timestamp': datetime.now().isoformat()
        }
        
        with open('trump_maker_order.json', 'w') as f:
            json.dump(order_data, f, indent=2)
        
        print(f"💾 Данные ордера сохранены в trump_maker_order.json")
        
    else:
        print(f"❌ Ошибка продажи: {order}")
        
except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Скрипт завершен")
print("\n💡 После исполнения ордера запустите:")
print("   python3 check_maker_fee.py") 