#!/usr/bin/env python3
"""
Детальный анализ ордера ETH с поиском комиссии
"""

from mex_api import MexAPI
import json

def check_eth_order_details():
    """Проверить детали ордера ETH"""
    try:
        api = MexAPI()
        
        print("🔍 Проверяем детали последнего ордера ETHUSDC...")
        
        # Получаем последний ордер
        orders = api.get_order_history('ETHUSDC', limit=1)
        
        if not orders:
            print("❌ Нет ордеров ETHUSDC")
            return
        
        order = orders[0]
        
        print("📊 ПОЛНЫЕ ДАННЫЕ ОРДЕРА:")
        print("=" * 60)
        print(json.dumps(order, indent=2))
        
        print("\n🔍 АНАЛИЗ КОМИССИИ:")
        print("=" * 40)
        
        # Ищем поля, которые могут содержать комиссию
        commission_fields = ['commission', 'commissionAsset', 'fee', 'feeAsset']
        
        for field in commission_fields:
            if field in order:
                print(f"✅ Найдено поле {field}: {order[field]}")
            else:
                print(f"❌ Поле {field} не найдено")
        
        # Проверяем все поля ордера
        print(f"\n📋 ВСЕ ПОЛЯ ОРДЕРА:")
        for key, value in order.items():
            print(f"  {key}: {value}")
        
        # Проверяем сделки (trades) для этого ордера
        print(f"\n🔍 Проверяем сделки для ордера {order['orderId']}...")
        
        # Получаем сделки
        trades = api.get_my_trades('ETHUSDC', limit=10)
        
        if trades:
            print(f"📊 Найдено {len(trades)} сделок:")
            for i, trade in enumerate(trades[:3]):  # Показываем первые 3
                print(f"\nСделка {i+1}:")
                print(json.dumps(trade, indent=2))
                
                # Ищем комиссию в сделке
                if 'commission' in trade:
                    print(f"💰 КОМИССИЯ В СДЕЛКЕ: {trade['commission']} {trade.get('commissionAsset', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_eth_order_details()
