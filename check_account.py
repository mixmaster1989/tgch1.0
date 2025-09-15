#!/usr/bin/env python3
"""
ПРОВЕРКА АККАУНТА!
Найдем все монеты и LUMA
"""

from mex_api import MexAPI
import json

print("🔍 ПРОВЕРКА АККАУНТА MEXC")
print("=" * 40)

try:
    # Создаем API объект
    api = MexAPI()
    print("✅ API инициализирован")
    
    # Получаем информацию об аккаунте
    print("📊 Получаем баланс аккаунта...")
    account_info = api.get_account_info()
    
    if not account_info or 'balances' not in account_info:
        print("❌ Не удалось получить баланс")
        exit()
    
    balances = account_info['balances']
    print(f"💰 Всего активов: {len(balances)}")
    
    # Ищем все ненулевые балансы
    non_zero_balances = []
    total_usdt_value = 0.0
    
    for balance in balances:
        free = float(balance['free'])
        locked = float(balance['locked'])
        total = free + locked
        
        if total > 0:
            asset = balance['asset']
            non_zero_balances.append({
                'asset': asset,
                'free': free,
                'locked': locked,
                'total': total
            })
    
    print(f"\n📈 Ненулевые балансы ({len(non_zero_balances)}):")
    print("-" * 60)
    
    # Сортируем по убыванию
    non_zero_balances.sort(key=lambda x: x['total'], reverse=True)
    
    for balance in non_zero_balances:
        asset = balance['asset']
        free = balance['free']
        locked = balance['locked']
        total = balance['total']
        
        # Получаем цену в USDT
        if asset == 'USDT':
            price = 1.0
            usdt_value = total
        elif asset == 'USDC':
            price = 1.0
            usdt_value = total
        else:
            try:
                symbol = f"{asset}USDT"
                ticker = api.get_ticker_price(symbol)
                if ticker and 'price' in ticker:
                    price = float(ticker['price'])
                    usdt_value = total * price
                else:
                    price = 0
                    usdt_value = 0
            except:
                price = 0
                usdt_value = 0
        
        total_usdt_value += usdt_value
        
        print(f"💰 {asset:>8}: {total:>15.8f} (${usdt_value:>10.2f})")
        if locked > 0:
            print(f"   🔒 Заблокировано: {locked:>15.8f}")
    
    print("-" * 60)
    print(f"💵 ОБЩАЯ СТОИМОСТЬ: ${total_usdt_value:.2f}")
    
    # Ищем LUMA отдельно
    print(f"\n🔍 ПОИСК LUMA:")
    luma_found = False
    
    for balance in non_zero_balances:
        if balance['asset'] == 'LUMA':
            luma_found = True
            luma_total = balance['total']
            
            # Получаем цену LUMA
            ticker = api.get_ticker_price('LUMAUSDT')
            if ticker and 'price' in ticker:
                luma_price = float(ticker['price'])
                luma_usdt_value = luma_total * luma_price
                
                print(f"🚨 LUMA НАЙДЕН!")
                print(f"   📊 Количество: {luma_total}")
                print(f"   💰 Цена: ${luma_price}")
                print(f"   💵 Стоимость: ${luma_usdt_value:.4f}")
                
                # Проверяем историю ордеров
                print(f"\n📋 Проверяем историю ордеров LUMAUSDT...")
                try:
                    orders = api.get_order_history('LUMAUSDT', limit=10)
                    if orders:
                        print(f"   📝 Найдено ордеров: {len(orders)}")
                        
                        # Ищем последний BUY ордер
                        for order in orders:
                            if order.get('side') == 'BUY':
                                print(f"   🟢 ПОСЛЕДНИЙ ПОКУПКА:")
                                print(f"      🆔 Ордер: {order.get('orderId', 'N/A')}")
                                print(f"      📊 Количество: {order.get('executedQty', 'N/A')}")
                                print(f"      💰 Цена: ${order.get('price', 'N/A')}")
                                print(f"      💵 Сумма: ${order.get('cummulativeQuoteQty', 'N/A')}")
                                print(f"      ⏰ Время: {order.get('time', 'N/A')}")
                                break
                    else:
                        print(f"   ❌ История ордеров пуста")
                except Exception as e:
                    print(f"   ❌ Ошибка получения истории: {e}")
            else:
                print(f"   ❌ Не удалось получить цену LUMA")
    
    if not luma_found:
        print("❌ LUMA не найден в балансе")
        
except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Проверка завершена") 