#!/usr/bin/env python3
"""
Скрипт для проверки баланса через MEX API
"""

import json
from datetime import datetime
from mex_api import MexAPI

def check_balance():
    """Проверка баланса аккаунта"""
    try:
        print("🔍 ПРОВЕРКА БАЛАНСА MEXC")
        print("=" * 50)
        print(f"Время: {datetime.now()}")
        print()
        
        # Создаем API клиент
        api = MexAPI()
        
        # Получаем информацию об аккаунте
        print("📊 Запрос баланса...")
        account_info = api.get_account_info()
        
        if 'code' in account_info:
            print(f"❌ ОШИБКА API: {account_info}")
            return
        
        print("✅ Баланс получен успешно!")
        print()
        
        # Показываем общую информацию
        print("📋 ОБЩАЯ ИНФОРМАЦИЯ:")
        print(f"   Maker комиссия: {account_info.get('makerCommission', 'N/A')}")
        print(f"   Taker комиссия: {account_info.get('takerCommission', 'N/A')}")
        print(f"   Buyer комиссия: {account_info.get('buyerCommission', 'N/A')}")
        print(f"   Seller комиссия: {account_info.get('sellerCommission', 'N/A')}")
        print()
        
        # Показываем балансы
        balances = account_info.get('balances', [])
        print(f"💰 БАЛАНСЫ ({len(balances)} активов):")
        print("-" * 50)
        
        total_usdt_value = 0.0
        non_zero_balances = []
        
        for balance in balances:
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if total > 0:
                non_zero_balances.append({
                    'asset': balance['asset'],
                    'free': free,
                    'locked': locked,
                    'total': total
                })
        
        # Сортируем по общему балансу
        non_zero_balances.sort(key=lambda x: x['total'], reverse=True)
        
        for balance in non_zero_balances:
            asset = balance['asset']
            free = balance['free']
            locked = balance['locked']
            total = balance['total']
            
            # Получаем цену в USDT для расчета стоимости
            if asset == 'USDT':
                usdt_value = total
            else:
                try:
                    ticker = api.get_ticker_price(f"{asset}USDT")
                    if 'price' in ticker:
                        price = float(ticker['price'])
                        usdt_value = total * price
                    else:
                        usdt_value = 0
                except:
                    usdt_value = 0
            
            total_usdt_value += usdt_value
            
            print(f"   {asset:>8}: {total:>12.6f} (свободно: {free:>10.6f}, заблокировано: {locked:>10.6f})")
            if usdt_value > 0:
                print(f"            ${usdt_value:>12.2f} USDT")
            print()
        
        print("=" * 50)
        print(f"💎 ОБЩАЯ СТОИМОСТЬ: ${total_usdt_value:.2f} USDT")
        print()
        
        # Показываем открытые ордера
        print("📋 ОТКРЫТЫЕ ОРДЕРА:")
        try:
            open_orders = api.get_open_orders()
            if isinstance(open_orders, list) and len(open_orders) > 0:
                for order in open_orders:
                    print(f"   {order['symbol']}: {order['side']} {order['origQty']} по цене {order['price']}")
            else:
                print("   Нет открытых ордеров")
        except Exception as e:
            print(f"   Ошибка получения ордеров: {e}")
        
        print()
        print("✅ Проверка завершена!")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_balance() 