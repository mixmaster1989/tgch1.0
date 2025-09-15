#!/usr/bin/env python3
"""
Проверка текущих позиций и ордеров по BTCUSDC и ETHUSDC
"""

from mex_api import MexAPI
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_current_positions():
    api = MexAPI()

    symbols = ['BTCUSDC', 'ETHUSDC']

    print("ПРОВЕРКА ТЕКУЩИХ ПОЗИЦИЙ")
    print("=" * 60)
    print(f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")

    total_pnl = 0
    total_value = 0

    for symbol in symbols:
        print(f"\n🪙 {symbol}")
        print("-" * 40)

        try:
            # 1. Проверяем открытые ордера
            open_orders = api.get_open_orders(symbol)
            print(f"📋 Открытые ордера: {len(open_orders)}")

            if open_orders:
                for order in open_orders:
                    order_type = order.get('type', 'unknown')
                    side = order.get('side', 'unknown')
                    price = float(order.get('price', 0))
                    qty = float(order.get('origQty', 0))
                    status = order.get('status', 'unknown')

                    print(f"   {order_type.upper()} {side.upper()}: {qty:.6f} @ ${price:.2f} [{status}]")

            # 2. Проверяем баланс актива
            if symbol == 'BTCUSDC':
                asset = 'BTC'
            else:
                asset = 'ETH'

            account_info = api.get_account_info()
            asset_balance = 0
            usdc_balance = 0

            for balance in account_info.get('balances', []):
                if balance['asset'] == asset:
                    asset_balance = float(balance.get('free', 0)) + float(balance.get('locked', 0))
                elif balance['asset'] == 'USDC':
                    usdc_balance = float(balance.get('free', 0)) + float(balance.get('locked', 0))

            print(f"💰 Баланс {asset}: {asset_balance:.6f} ({asset_balance * get_current_price(api, symbol):.2f} USDC)")
            print(f"💵 Баланс USDC: ${usdc_balance:.2f}")

            # 3. Проверяем историю ордеров (последние 10)
            print("📜 Последние 10 ордеров:")
            order_history = api.get_order_history(symbol, limit=10)

            if order_history:
                for order in order_history:
                    order_type = order.get('type', 'unknown')
                    side = order.get('side', 'unknown')
                    price = float(order.get('price', 0))
                    qty = float(order.get('origQty', 0))
                    status = order.get('status', 'unknown')
                    time_str = datetime.fromtimestamp(order.get('time', 0)/1000).strftime('%H:%M:%S')

                    if side.upper() == 'BUY' and status == 'FILLED':
                        pnl = calculate_pnl_for_order(api, symbol, order)
                        pnl_str = ".2f" if pnl != 0 else "   -"
                        print(f"   [{time_str}] {order_type.upper()} {side.upper()}: {qty:.6f} @ ${price:.2f} {pnl_str}")
                    else:
                        print(f"   [{time_str}] {order_type.upper()} {side.upper()}: {qty:.6f} @ ${price:.2f} [{status}]")

            # 4. Расчет текущего PnL для позиции
            if asset_balance > 0:
                current_price = get_current_price(api, symbol)
                entry_price = get_average_entry_price(api, symbol, asset_balance)
                if entry_price > 0:
                    pnl = (current_price - entry_price) * asset_balance
                    pnl_percent = ((current_price - entry_price) / entry_price) * 100
                    total_pnl += pnl
                    total_value += asset_balance * current_price

                    print(f"   💰 Текущая цена: ${current_price:.2f}")
                    print(f"   📈 PnL: ${pnl:.2f} ({pnl_percent:.2f}%)")
                    print(f"   🔄 Стоимость позиции: ${asset_balance * current_price:.2f}")

        except Exception as e:
            print(f"❌ Ошибка проверки {symbol}: {e}")

    print("\n" + "=" * 60)
    print("📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"💰 Общий PnL: ${total_pnl:.2f}")
    print(f"💼 Общая стоимость позиций: ${total_value:.2f}")
def get_current_price(api, symbol):
    """Получить текущую цену"""
    try:
        ticker = api.get_ticker_price(symbol)
        return float(ticker.get('price', 0))
    except:
        return 0

def get_average_entry_price(api, symbol, current_balance):
    """Рассчитать среднюю цену входа на основе истории покупок"""
    try:
        # Получаем историю ордеров
        all_orders = api.get_order_history(symbol, limit=100)
        total_cost = 0
        total_qty = 0

        for order in all_orders:
            if order.get('side') == 'BUY' and order.get('status') == 'FILLED':
                price = float(order.get('price', 0))
                qty = float(order.get('origQty', 0))
                total_cost += price * qty
                total_qty += qty

        return total_cost / total_qty if total_qty > 0 else 0
    except:
        return 0

def calculate_pnl_for_order(api, symbol, order):
    """Рассчитать PnL для конкретного ордера"""
    try:
        if order.get('side') != 'BUY' or order.get('status') != 'FILLED':
            return 0

        buy_price = float(order.get('price', 0))
        buy_qty = float(order.get('origQty', 0))
        buy_time = order.get('time', 0)

        # Ищем соответствующий ордер продажи
        order_history = api.get_order_history(symbol, limit=50)
        for sell_order in order_history:
            if (sell_order.get('side') == 'SELL' and
                sell_order.get('status') == 'FILLED' and
                sell_order.get('time', 0) > buy_time):

                sell_price = float(sell_order.get('price', 0))
                sell_qty = float(sell_order.get('origQty', 0))

                if sell_qty >= buy_qty:
                    pnl = (sell_price - buy_price) * buy_qty
                    return pnl

        return 0
    except:
        return 0

if __name__ == "__main__":
    check_current_positions()
