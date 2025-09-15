#!/usr/bin/env python3
"""
АНАЛИЗ АЛЬТКОИНОВ!
Цена покупки vs текущая цена - кто в плюсе?
"""

from mex_api import MexAPI
import json
from datetime import datetime

print("🔍 АНАЛИЗ АЛЬТКОИНОВ - КТО В ПЛЮСЕ?")
print("=" * 50)

try:
    # Создаем API объект
    api = MexAPI()
    print("✅ API инициализирован")
    
    # Получаем баланс аккаунта
    print("📊 Получаем баланс аккаунта...")
    account_info = api.get_account_info()
    
    if not account_info or 'balances' not in account_info:
        print("❌ Не удалось получить баланс")
        exit()
    
    balances = account_info['balances']
    
    # Ищем все ненулевые балансы (кроме USDT/USDC)
    altcoins = []
    
    for balance in balances:
        free = float(balance['free'])
        locked = float(balance['locked'])
        total = free + locked
        
        if total > 0:
            asset = balance['asset']
            if asset not in ['USDT', 'USDC']:
                altcoins.append({
                    'asset': asset,
                    'total': total
                })
    
    print(f"💰 Найдено альткоинов: {len(altcoins)}")
    
    # Анализируем каждый альткоин
    print(f"\n📈 АНАЛИЗ АЛЬТКОИНОВ:")
    print("=" * 80)
    
    profitable_coins = []
    loss_coins = []
    
    for alt in altcoins:
        asset = alt['asset']
        quantity = alt['total']
        
        print(f"\n🔸 {asset}: {quantity}")
        
        try:
            # 1. Получаем текущую цену
            symbol = f"{asset}USDT"
            ticker = api.get_ticker_price(symbol)
            
            if not ticker or 'price' not in ticker:
                print(f"   ❌ Не удалось получить цену {symbol}")
                continue
            
            current_price = float(ticker['price'])
            current_value = quantity * current_price
            
            print(f"   💰 Текущая цена: ${current_price}")
            print(f"   💵 Текущая стоимость: ${current_value:.4f}")
            
            # 2. Получаем историю ордеров для поиска цены покупки
            orders = api.get_order_history(symbol, limit=20)
            
            if not orders:
                print(f"   ❌ Нет истории ордеров")
                continue
            
            # Ищем последний BUY ордер
            last_buy = None
            for order in orders:
                if order.get('side') == 'BUY' and order.get('status') == 'FILLED':
                    last_buy = order
                    break
            
            if not last_buy:
                print(f"   ❌ Нет BUY ордеров")
                continue
            
            # 3. Анализируем покупку
            buy_price = float(last_buy.get('price', 0))
            buy_quantity = float(last_buy.get('executedQty', 0))
            buy_total = float(last_buy.get('cummulativeQuoteQty', 0))
            buy_time = last_buy.get('time', 0)
            
            if buy_time:
                buy_time_str = datetime.fromtimestamp(buy_time / 1000).strftime('%Y-%m-%d %H:%M:%S')
            else:
                buy_time_str = 'N/A'
            
            print(f"   📥 Последняя покупка:")
            print(f"      💰 Цена: ${buy_price}")
            print(f"      📊 Количество: {buy_quantity}")
            print(f"      💵 Сумма: ${buy_total}")
            print(f"      ⏰ Время: {buy_time_str}")
            
            # 4. Считаем PnL
            if buy_quantity > 0:
                # Приводим к общему количеству
                ratio = quantity / buy_quantity
                adjusted_buy_cost = buy_total * ratio
                
                pnl = current_value - adjusted_buy_cost
                pnl_percent = (pnl / adjusted_buy_cost) * 100 if adjusted_buy_cost > 0 else 0
                
                print(f"   📊 PnL: ${pnl:.4f} ({pnl_percent:+.2f}%)")
                
                # Сохраняем для итогов
                coin_data = {
                    'asset': asset,
                    'quantity': quantity,
                    'current_price': current_price,
                    'current_value': current_value,
                    'buy_price': buy_price,
                    'buy_cost': adjusted_buy_cost,
                    'pnl': pnl,
                    'pnl_percent': pnl_percent
                }
                
                if pnl > 0:
                    profitable_coins.append(coin_data)
                    print(f"   🟢 В ПЛЮСЕ!")
                else:
                    loss_coins.append(coin_data)
                    print(f"   🔴 В МИНУСЕ!")
            else:
                print(f"   ❌ Ошибка расчета PnL")
                
        except Exception as e:
            print(f"   ❌ Ошибка анализа: {e}")
    
    # Итоги
    print(f"\n📊 ИТОГИ АНАЛИЗА:")
    print("=" * 50)
    
    print(f"🟢 В ПЛЮСЕ: {len(profitable_coins)} монет")
    for coin in profitable_coins:
        print(f"   {coin['asset']}: +${coin['pnl']:.4f} ({coin['pnl_percent']:+.2f}%)")
    
    print(f"\n🔴 В МИНУСЕ: {len(loss_coins)} монет")
    for coin in loss_coins:
        print(f"   {coin['asset']}: ${coin['pnl']:.4f} ({coin['pnl_percent']:+.2f}%)")
    
    # Рекомендации для тестирования комиссии
    if profitable_coins:
        print(f"\n💡 РЕКОМЕНДАЦИИ ДЛЯ ТЕСТИРОВАНИЯ КОМИССИИ:")
        print("=" * 60)
        
        # Сортируем по проценту прибыли
        profitable_coins.sort(key=lambda x: x['pnl_percent'], reverse=True)
        
        best_coin = profitable_coins[0]
        print(f"🎯 Лучший кандидат: {best_coin['asset']}")
        print(f"   📈 Прибыль: +${best_coin['pnl']:.4f} ({best_coin['pnl_percent']:+.2f}%)")
        print(f"   💰 Текущая стоимость: ${best_coin['current_value']:.4f}")
        print(f"   📊 Количество: {best_coin['quantity']}")
        
        print(f"\n🚀 Можете продать {best_coin['asset']} для тестирования комиссии мейкера!")
        
except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    import traceback
    traceback.print_exc()

print("\n🏁 Анализ завершен") 