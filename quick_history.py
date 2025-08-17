#!/usr/bin/env python3
"""
Быстрая проверка истории ордеров
"""

from datetime import datetime
from mex_api import MexAPI

def quick_history():
    """Быстрая проверка истории"""
    
    api = MexAPI()
    
    print("🔍 БЫСТРАЯ ПРОВЕРКА ИСТОРИИ")
    print("=" * 30)
    
    # Только основные пары
    symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT', 'DOGEUSDT', 'LTCUSDT']
    
    total_orders = 0
    
    for symbol in symbols:
        try:
            orders = api.get_order_history(symbol=symbol, limit=500)
            
            if isinstance(orders, list) and orders:
                print(f"📊 {symbol}: {len(orders)} ордеров")
                
                # Показываем последние 3 ордера
                for order in orders[-3:]:
                    order_time = datetime.fromtimestamp(order['time'] / 1000)
                    side = order['side']
                    status = order['status']
                    quantity = float(order['executedQty'])
                    price = float(order['price'])
                    
                    print(f"   📋 {order_time.strftime('%d.%m %H:%M')} | {side} | {quantity:.6f} @ ${price:.4f}")
                
                total_orders += len(orders)
            else:
                print(f"📊 {symbol}: 0 ордеров")
                
        except Exception as e:
            print(f"❌ {symbol}: {e}")
    
    print(f"\n📈 ВСЕГО ОРДЕРОВ: {total_orders}")

if __name__ == "__main__":
    quick_history()
