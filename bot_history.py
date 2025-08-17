#!/usr/bin/env python3
"""
Полная история работы бота через API
"""

from datetime import datetime
from mex_api import MexAPI
import json

def get_bot_history():
    """Получить полную историю работы бота"""
    
    api = MexAPI()
    
    print("🤖 ПОЛНАЯ ИСТОРИЯ РАБОТЫ БОТА")
    print("=" * 50)
    
    try:
        # 1. Получаем все ордера по всем символам
        print("📋 Получение истории ордеров...")
        
        # Список основных торговых пар (расширенный)
        symbols = [
            'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT', 'DOGEUSDT', 'BNBUSDT', 'LTCUSDT', 'TRXUSDT', 'LINKUSDT',
            'AVAXUSDT', 'DOTUSDT', 'MATICUSDT', 'UNIUSDT', 'ATOMUSDT', 'NEARUSDT', 'FTMUSDT', 'ALGOUSDT', 'VETUSDT', 'ICPUSDT',
            'FILUSDT', 'THETAUSDT', 'XLMUSDT', 'HBARUSDT', 'MANAUSDT', 'SANDUSDT', 'AXSUSDT', 'GALAUSDT', 'ENJUSDT', 'CHZUSDT',
            'HOTUSDT', 'BTTUSDT', 'WINUSDT', 'CAKEUSDT', 'RUNEUSDT', 'EGLDUSDT', 'ONEUSDT', 'ZILUSDT', 'IOTAUSDT', 'NEOUSDT',
            'QTUMUSDT', 'ONTUSDT', 'ZECUSDT', 'DASHUSDT', 'XMRUSDT', 'BCHUSDT', 'ETCUSDT', 'LTCUSDT', 'BTGUSDT', 'BTSUSDT'
        ]
        
        all_orders = []
        
        for symbol in symbols:
            try:
                print(f"📊 Получение ордеров для {symbol}...")
                # Получаем больше ордеров и с начала времени
                orders = api.get_order_history(symbol=symbol, limit=1000)
                
                if isinstance(orders, list):
                    all_orders.extend(orders)
                    print(f"   ✅ {symbol}: {len(orders)} ордеров")
                else:
                    print(f"   ❌ {symbol}: ошибка API")
                    
            except Exception as e:
                print(f"   ❌ {symbol}: {e}")
                continue
        
        print(f"📊 Ответ API: {type(all_orders)}")
        if isinstance(all_orders, dict):
            print(f"📊 Ключи: {list(all_orders.keys())}")
            if 'msg' in all_orders:
                print(f"❌ Ошибка API: {all_orders['msg']}")
                return
        
        if not all_orders or not isinstance(all_orders, list):
            print("❌ Ордера не найдены или неверный формат")
            return
        
        print(f"✅ Найдено ордеров: {len(all_orders)}")
        
        # 2. Анализируем ордера
        buy_orders = []
        sell_orders = []
        total_buy_value = 0
        total_sell_value = 0
        
        print("\n📊 АНАЛИЗ ОРДЕРОВ:")
        print("-" * 30)
        
        for order in all_orders:
            order_time = datetime.fromtimestamp(order['time'] / 1000)
            side = order['side']
            status = order['status']
            symbol = order['symbol']
            
            if status == 'FILLED':
                quantity = float(order['executedQty'])
                price = float(order['price'])
                value = quantity * price
                
                print(f"📋 {order_time.strftime('%d.%m %H:%M:%S')} | {symbol} | {side}")
                print(f"   💰 Цена: ${price:.4f} | Количество: {quantity:.6f}")
                print(f"   💵 Сумма: ${value:.2f}")
                print()
                
                if side == 'BUY':
                    buy_orders.append({
                        'time': order_time,
                        'symbol': symbol,
                        'price': price,
                        'quantity': quantity,
                        'value': value
                    })
                    total_buy_value += value
                elif side == 'SELL':
                    sell_orders.append({
                        'time': order_time,
                        'symbol': symbol,
                        'price': price,
                        'quantity': quantity,
                        'value': value
                    })
                    total_sell_value += value
        
        # 3. Получаем текущие балансы
        print("💰 ТЕКУЩИЕ БАЛАНСЫ:")
        print("-" * 30)
        
        account_info = api.get_account_info()
        balances = account_info.get('balances', [])
        
        current_portfolio = {}
        total_portfolio_value = 0
        
        for balance in balances:
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if total > 0:
                asset = balance['asset']
                current_portfolio[asset] = total
                
                # Получаем текущую цену для расчета стоимости
                if asset != 'USDT':
                    try:
                        ticker = api.get_ticker_price(f"{asset}USDT")
                        if ticker and 'price' in ticker:
                            price = float(ticker['price'])
                            value = total * price
                            total_portfolio_value += value
                            print(f"📊 {asset}: {total:.6f} @ ${price:.4f} = ${value:.2f}")
                        else:
                            print(f"📊 {asset}: {total:.6f} (цена не найдена)")
                    except:
                        print(f"📊 {asset}: {total:.6f} (ошибка получения цены)")
                else:
                    total_portfolio_value += total
                    print(f"📊 {asset}: {total:.2f}")
        
        # 4. Итоговая статистика
        print("\n📈 ИТОГОВАЯ СТАТИСТИКА:")
        print("=" * 30)
        print(f"🟢 Покупок: {len(buy_orders)}")
        print(f"🔴 Продаж: {len(sell_orders)}")
        print(f"💰 Общая сумма покупок: ${total_buy_value:.2f}")
        print(f"💰 Общая сумма продаж: ${total_sell_value:.2f}")
        print(f"💼 Текущая стоимость портфеля: ${total_portfolio_value:.2f}")
        
        # 5. Расчет PnL
        realized_pnl = total_sell_value - total_buy_value
        unrealized_pnl = total_portfolio_value - total_buy_value
        total_pnl = realized_pnl + unrealized_pnl
        
        print(f"📊 Реализованный PnL: ${realized_pnl:.2f}")
        print(f"📊 Нереализованный PnL: ${unrealized_pnl:.2f}")
        print(f"📊 Общий PnL: ${total_pnl:.2f}")
        
        # 6. Сохраняем в файл
        history_data = {
            'orders': {
                'buy': [order for order in buy_orders],
                'sell': [order for order in sell_orders]
            },
            'statistics': {
                'total_buy_value': total_buy_value,
                'total_sell_value': total_sell_value,
                'current_portfolio_value': total_portfolio_value,
                'realized_pnl': realized_pnl,
                'unrealized_pnl': unrealized_pnl,
                'total_pnl': total_pnl
            },
            'current_portfolio': current_portfolio,
            'generated_at': datetime.now().isoformat()
        }
        
        with open('bot_history.json', 'w', encoding='utf-8') as f:
            json.dump(history_data, f, indent=2, default=str)
        
        print(f"\n💾 История сохранена в файл: bot_history.json")
        
    except Exception as e:
        print(f"❌ Ошибка получения истории: {e}")

if __name__ == "__main__":
    get_bot_history()
