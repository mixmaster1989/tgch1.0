#!/usr/bin/env python3
"""
Продажа ETH для получения 20 USDC
"""

from mex_api import MexAPI
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def sell_eth_for_usdc():
    api = MexAPI()

    try:
        # Получаем текущие данные
        account_info = api.get_account_info()
        eth_balance = 0
        current_usdc = 0

        for balance in account_info.get('balances', []):
            if balance['asset'] == 'ETH':
                eth_balance = float(balance.get('free', 0))
            elif balance['asset'] == 'USDC':
                current_usdc = float(balance.get('free', 0))

        print("ПРОДАЖА ETH ДЛЯ ПОЛУЧЕНИЯ 20 USDC")
        print("=" * 50)
        print(f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}")
        print(f"🪙 Баланс ETH: {eth_balance:.6f}")
        print(f"💰 Текущий USDC: ${current_usdc:.2f}")

        target_usdc = 20.0
        print(f"🎯 Нужно USDC: ${target_usdc:.2f}")
        # Получаем текущую цену ETH
        ticker = api.get_ticker_price('ETHUSDC')
        current_price = float(ticker.get('price', 0))
        print(f"💵 Текущая цена ETH: ${current_price:.2f}")
        # Расчет сколько нужно продать
        needed_usdc = target_usdc - current_usdc
        eth_to_sell = needed_usdc / current_price

        print(f"💸 Недостаёт USDC: ${needed_usdc:.2f}")
        print(f"🔄 Нужно продать ETH: {eth_to_sell:.6f}")
        # Проверяем достаточно ли ETH
        if eth_to_sell > eth_balance:
            print(f"❌ Недостаточно ETH! Нужно: {eth_to_sell:.6f}, есть: {eth_balance:.6f}")
            return False

        # Продаем с небольшим запасом (чтобы учесть комиссии)
        eth_to_sell_adjusted = eth_to_sell * 1.002  # +0.2% запас
        eth_to_sell_adjusted = min(eth_to_sell_adjusted, eth_balance)  # не больше чем есть

        print(f"🔄 С запасом на комиссии: {eth_to_sell_adjusted:.6f} ETH")
        # Округляем до 6 знаков (стандарт для ETH)
        eth_to_sell_rounded = round(eth_to_sell_adjusted, 6)

        print(f"🎯 Будет продано: {eth_to_sell_rounded:.6f} ETH")
        print(f"💰 Ожидаемый доход: ${(eth_to_sell_rounded * current_price):.2f}")

        # Проверяем минимальный объем
        min_eth = 0.01  # Минимальный объем для ETH на MEXC (увеличен для надежности)
        if eth_to_sell_rounded < min_eth:
            print(f"⚠️ Количество слишком маленькое! Минимум: {min_eth:.6f} ETH")
            eth_to_sell_rounded = min_eth
            print(f"🔄 Устанавливаю минимальное количество: {eth_to_sell_rounded:.6f} ETH")
            print(f"💰 Новый ожидаемый доход: ${(eth_to_sell_rounded * current_price):.2f}")
        else:
            print(f"✅ Количество подходит: {eth_to_sell_rounded:.6f} ETH")

        # Автоматическое выполнение (пользователь уже подтвердил)
        print("🚀 Выполняю продажу ETH...")

        # Размещаем ордер на продажу
        print("📊 Размещаю ордер на продажу...")

        # Используем LIMIT ордер с текущей ценой
        order_result = api.place_order(
            symbol='ETHUSDC',
            side='SELL',
            price=current_price,
            quantity=eth_to_sell_rounded
        )

        if order_result and 'orderId' in order_result:
            order_id = order_result.get('orderId')
            order_status = order_result.get('status', 'NEW')

            print(f"✅ Ордер размещен успешно!")
            print(f"📋 Order ID: {order_id}")
            print(f"📊 Статус: {order_status}")
            print(f"🔄 Количество: {order_result.get('origQty', 0)} ETH")
            print(f"💰 Цена: ${order_result.get('price', 0)}")

            # Если ордер исполнен, показываем результаты
            if order_status == 'FILLED':
                executed_qty = float(order_result.get('executedQty', 0))
                executed_price = float(order_result.get('price', 0))
                usdc_received = executed_qty * executed_price

                print("🎉 Ордер полностью исполнен!")
                print(f"🔄 Продано ETH: {executed_qty:.6f}")
                print(f"💰 Получено USDC: ${usdc_received:.2f}")

            # Проверяем финальный баланс
            final_check()
            return True
        else:
            print(f"❌ Ошибка размещения ордера: {order_result}")
            return False

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def final_check():
    """Финальная проверка баланса"""
    api = MexAPI()

    try:
        account_info = api.get_account_info()
        for balance in account_info.get('balances', []):
            if balance['asset'] == 'USDC':
                final_usdc = float(balance.get('free', 0))
                print(f"\n🎉 ФИНАЛЬНЫЙ БАЛАНС USDC: ${final_usdc:.2f}")
                return final_usdc
    except Exception as e:
        print(f"❌ Ошибка проверки финального баланса: {e}")

    return 0

if __name__ == "__main__":
    sell_eth_for_usdc()
