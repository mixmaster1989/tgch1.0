#!/usr/bin/env python3
"""
РАБОЧАЯ ПРОДАЖА LUMAUSDT!
Используем существующий API класс
"""

from mex_api import MexAPI
import json

print("🚨 РАБОЧАЯ ПРОДАЖА LUMAUSDT!")
print("=" * 40)

try:
    # Создаем API объект
    api = MexAPI()
    print("✅ API инициализирован")
    
    # 1. Получаем баланс LUMA
    print("🔍 Получаем баланс LUMA...")
    account_info = api.get_account_info()
    
    luma_balance = 0.0
    for balance in account_info.get('balances', []):
        if balance['asset'] == 'LUMA':
            luma_balance = float(balance['free'])
            break
    
    if luma_balance <= 0:
        print("❌ LUMA не найден в балансе")
        exit()
    
    print(f"💰 Найден LUMA: {luma_balance}")
    
    # 2. Получаем цену LUMA
    print("📊 Получаем цену LUMA...")
    ticker = api.get_ticker_price('LUMAUSDT')
    current_price = float(ticker['price']) if ticker and 'price' in ticker else 0
    estimated_value = luma_balance * current_price
    
    print(f"💵 Цена LUMA: ${current_price}")
    print(f"💰 Примерная стоимость: ${estimated_value:.2f}")
    
    # 3. ПРОДАЕМ LUMA
    print(f"\n🔥 ПРОДАЕМ {luma_balance} LUMA...")
    print("🚨 ИСПОЛЬЗУЕМ РЫНОЧНЫЙ ОРДЕР (price=None)")
    
    # Округляем количество
    quantity = round(luma_balance, 2)
    print(f"📊 Количество для продажи: {quantity}")
    
    # ПРОДАЕМ КАК В sell_all.py - price=None для рыночного ордера!
    result = api.place_order(
        symbol='LUMAUSDT',
        side='SELL', 
        quantity=quantity,
        price=None  # РЫНОЧНЫЙ ОРДЕР!
    )
    
    if result and 'orderId' in result:
        print(f"✅ LUMA ПРОДАН УСПЕШНО!")
        print(f"🆔 Ордер: {result['orderId']}")
        print(f"📊 Количество: {quantity}")
        print(f"💰 Символ: LUMAUSDT")
        print(f"📈 Статус: {result.get('status', 'N/A')}")
        print(f"💵 Примерная выручка: ${estimated_value:.2f}")
        
        # Проверяем новый баланс USDT
        print("\n🔍 Проверяем новый баланс...")
        new_account = api.get_account_info()
        for balance in new_account.get('balances', []):
            if balance['asset'] == 'USDT':
                usdt_balance = float(balance['free'])
                print(f"💵 Новый баланс USDT: ${usdt_balance:.2f}")
                break
                
    else:
        print(f"❌ Ошибка продажи: {result}")
        
except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Скрипт завершен") 