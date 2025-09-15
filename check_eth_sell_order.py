#!/usr/bin/env python3
"""
Проверка исполнения ордера продажи ETH
"""

from mex_api import MexAPI
from datetime import datetime

def check_eth_sell_order():
    """Проверить исполнение ордера продажи ETH"""
    try:
        api = MexAPI()
        
        print("🔍 Проверяем последние ордера ETHUSDC...")
        
        # Получаем последние ордера
        orders = api.get_order_history('ETHUSDC', limit=5)
        
        if not orders:
            print("❌ Нет ордеров ETHUSDC")
            return
        
        print(f"📊 Найдено {len(orders)} ордеров:")
        print("=" * 80)
        
        for i, order in enumerate(orders):
            side = order.get('side', 'UNKNOWN')
            status = order.get('status', 'UNKNOWN')
            symbol = order.get('symbol', 'UNKNOWN')
            order_id = order.get('orderId', 'UNKNOWN')
            
            # Время ордера
            time_ms = order.get('time', 0)
            order_time = datetime.fromtimestamp(time_ms / 1000).strftime('%H:%M:%S')
            
            # Количество и цена
            orig_qty = float(order.get('origQty', 0))
            executed_qty = float(order.get('executedQty', 0))
            price = float(order.get('price', 0))
            
            # Сумма
            cummulative_quote_qty = float(order.get('cummulativeQuoteQty', 0))
            
            print(f"{i+1}. {side} {symbol}")
            print(f"   ID: {order_id}")
            print(f"   Время: {order_time}")
            print(f"   Статус: {status}")
            print(f"   Количество: {orig_qty} → {executed_qty}")
            print(f"   Цена: ${price:.2f}")
            print(f"   Сумма: ${cummulative_quote_qty:.4f}")
            
            # Если это SELL ордер, показываем детали
            if side == 'SELL':
                print(f"   💰 ПРОДАЖА ETH")
                if status == 'FILLED':
                    print(f"   ✅ ИСПОЛНЕН")
                    print(f"   📊 Получено: ${cummulative_quote_qty:.4f} USDC")
                else:
                    print(f"   ⏳ Статус: {status}")
            
            print("-" * 40)
        
        # Проверяем баланс USDC
        print("\n💰 Проверяем баланс USDC...")
        account_info = api.get_account_info()
        usdc_balance = 0.0
        
        for balance in account_info.get('balances', []):
            if balance['asset'] == 'USDC':
                usdc_balance = float(balance['free'])
                break
        
        print(f"💵 Текущий баланс USDC: ${usdc_balance:.4f}")
        
        # Анализ комиссий
        print("\n📊 АНАЛИЗ КОМИССИЙ:")
        print("=" * 40)
        
        if len(orders) >= 2:
            buy_order = None
            sell_order = None
            
            for order in orders:
                if order['side'] == 'BUY' and order['status'] == 'FILLED':
                    buy_order = order
                elif order['side'] == 'SELL' and order['status'] == 'FILLED':
                    sell_order = order
            
            if buy_order and sell_order:
                buy_amount = float(buy_order['cummulativeQuoteQty'])
                sell_amount = float(sell_order['cummulativeQuoteQty'])
                
                print(f"💸 Потрачено на покупку: ${buy_amount:.4f} USDC")
                print(f"💰 Получено от продажи: ${sell_amount:.4f} USDC")
                
                total_cost = buy_amount
                total_revenue = sell_amount
                net_result = total_revenue - total_cost
                
                print(f"📈 Чистый результат: ${net_result:.4f} USDC")
                
                if net_result > 0:
                    print(f"✅ ПРИБЫЛЬ: ${net_result:.4f} USDC")
                else:
                    print(f"📉 УБЫТОК: ${abs(net_result):.4f} USDC")
                
                # Комиссии
                buy_commission = 5.0 - buy_amount  # Ожидали $5, потратили buy_amount
                sell_commission = sell_amount - (sell_amount * 0.999)  # Примерная комиссия продажи
                
                print(f"💸 Комиссия покупки: ${buy_commission:.4f} USDC")
                print(f"💸 Комиссия продажи: ${sell_commission:.4f} USDC")
                print(f"💸 Общие комиссии: ${buy_commission + sell_commission:.4f} USDC")
                
                commission_percent = ((buy_commission + sell_commission) / 5.0) * 100
                print(f"📊 Комиссии в %: {commission_percent:.2f}%")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_eth_sell_order()
