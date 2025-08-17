#!/usr/bin/env python3
"""
Тест мониторинга ордеров в PnL мониторе
"""

import logging
from pnl_monitor import PnLMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_orders_monitoring():
    """Тест мониторинга ордеров"""
    print("🔍 ТЕСТ МОНИТОРИНГА ОРДЕРОВ")
    print("=" * 50)
    
    monitor = PnLMonitor()
    
    # Тест получения ордеров
    print("📋 Получение открытых ордеров...")
    orders_info = monitor.get_open_orders_info()
    
    print(f"📊 Всего ордеров: {orders_info['total_orders']}")
    print(f"🟢 Покупки: {orders_info['buy_orders']}")
    print(f"🔴 Продажи: {orders_info['sell_orders']}")
    print(f"💰 Общая стоимость: ${orders_info['total_value']:.2f}")
    
    if orders_info['orders']:
        print(f"\n📋 Детали ордеров:")
        for i, order in enumerate(orders_info['orders'][:3], 1):
            side_emoji = "🟢" if order['side'] == 'BUY' else "🔴"
            print(f"{i}. {side_emoji} {order['symbol']} {order['side']}")
            print(f"   💰 {order['quantity']:.6f} @ ${order['price']:.4f}")
            print(f"   💵 Стоимость: ${order['value']:.2f}")
            print(f"   🆔 ID: {order['order_id']}")
    else:
        print("🚫 Нет открытых ордеров")
    
    # Тест статуса с ордерами
    print(f"\n📊 Тест обновленного статуса...")
    status = monitor.get_current_status()
    
    print(f"💰 PnL: ${status['total_pnl']:.4f}")
    print(f"📋 Ордеров в статусе: {status['orders']['total_orders']}")
    
    return orders_info

if __name__ == "__main__":
    test_orders_monitoring() 