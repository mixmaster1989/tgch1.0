#!/usr/bin/env python3
"""
Проверка истории ордеров ETH за последние 10 минут
"""

from datetime import datetime, timedelta
from mex_api import MexAPI
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_eth_orders():
    """Проверить историю ордеров ETH за последние 10 минут"""
    
    api = MexAPI()
    symbol = "ETHUSDT"
    
    # Время 10 минут назад
    start_time = datetime.now() - timedelta(minutes=10)
    start_timestamp = int(start_time.timestamp() * 1000)
    
    print(f"🔍 ПРОВЕРКА ОРДЕРОВ ETH ЗА ПОСЛЕДНИЕ 10 МИНУТ")
    print(f"⏰ Время начала: {start_time.strftime('%H:%M:%S')}")
    print(f"⏰ Текущее время: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 50)
    
    try:
        # Получаем историю ордеров (последние 100 ордеров)
        orders = api.get_order_history(symbol, limit=100)
        
        if not orders:
            print("📋 Ордеров за последние 10 минут не найдено")
            return
        
        print(f"📊 Найдено ордеров: {len(orders)}")
        print()
        
        # Анализируем каждый ордер
        buy_orders = []
        sell_orders = []
        
        # Фильтруем ордера за сегодня
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_timestamp = int(today_start.timestamp() * 1000)
        
        for order in orders:
            order_time = datetime.fromtimestamp(order['time'] / 1000)
            
            # Пропускаем ордера не за сегодня
            if order['time'] < today_timestamp:
                continue
            order_time = datetime.fromtimestamp(order['time'] / 1000)
            side = order['side']
            status = order['status']
            quantity = float(order['executedQty'])
            price = float(order['price'])
            
            print(f"📋 {order_time.strftime('%H:%M:%S')} | {side} | {status}")
            print(f"   💰 Цена: ${price:.2f} | Количество: {quantity:.6f} ETH")
            print(f"   💵 Сумма: ${quantity * price:.2f}")
            print()
            
            if side == 'BUY' and status == 'FILLED':
                buy_orders.append(order)
            elif side == 'SELL' and status == 'FILLED':
                sell_orders.append(order)
        
        # Итоговая статистика
        print("📈 ИТОГОВАЯ СТАТИСТИКА:")
        print("=" * 30)
        print(f"🟢 Покупки: {len(buy_orders)}")
        print(f"🔴 Продажи: {len(sell_orders)}")
        
        if buy_orders and sell_orders:
            print("✅ БЫЛИ И ПОКУПКИ, И ПРОДАЖИ!")
        elif buy_orders:
            print("🟢 ТОЛЬКО ПОКУПКИ")
        elif sell_orders:
            print("🔴 ТОЛЬКО ПРОДАЖИ")
        else:
            print("⚪ НЕТ ИСПОЛНЕННЫХ ОРДЕРОВ")
            
    except Exception as e:
        print(f"❌ Ошибка получения истории ордеров: {e}")

if __name__ == "__main__":
    check_eth_orders()
