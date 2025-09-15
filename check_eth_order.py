#!/usr/bin/env python3
"""
Проверка последнего ордера ETH
"""

from mex_api import MexAPI

def check_eth_order():
    """Проверить последний ордер ETH"""
    try:
        api = MexAPI()
        
        print("🔍 Проверяем последний ордер ETHUSDC...")
        
        # Получаем последний ордер
        orders = api.get_order_history('ETHUSDC', limit=1)
        
        if not orders:
            print("❌ Нет ордеров ETHUSDC")
            return
        
        order = orders[0]
        
        print("📊 ДЕТАЛИ ОРДЕРА:")
        print("=" * 50)
        print(f"ID: {order['orderId']}")
        print(f"Тип: {order['type']}")
        print(f"Сторона: {order['side']}")
        print(f"Количество: {order['executedQty']}")
        print(f"Цена: ${float(order['price']):.2f}")
        print(f"Сумма: ${float(order['cummulativeQuoteQty']):.4f}")
        print(f"Статус: {order['status']}")
        
        # Проверяем, был ли это мейкер
        if order['type'] == 'LIMIT':
            print("✅ ЛИМИТНЫЙ ОРДЕР (мейкер)")
        else:
            print("❌ НЕ лимитный ордер")
        
        # Анализ комиссии
        expected_amount = 4.9  # Ожидаемая сумма
        actual_amount = float(order['cummulativeQuoteQty'])
        commission = expected_amount - actual_amount
        
        print(f"\n💰 АНАЛИЗ КОМИССИИ:")
        print(f"Ожидалось: ${expected_amount:.2f} USDC")
        print(f"Потрачено: ${actual_amount:.4f} USDC")
        print(f"Комиссия: ${commission:.4f} USDC")
        print(f"Комиссия в %: {(commission/expected_amount)*100:.2f}%")
        
        if commission > 0:
            print("💸 Есть комиссия")
        else:
            print("✅ Нет комиссии (мейкер)")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_eth_order()
