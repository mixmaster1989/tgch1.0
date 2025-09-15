#!/usr/bin/env python3
"""
Проверка сделок ETH через advanced API
"""

from mexc_advanced_api import MexAdvancedAPI

def check_eth_trades():
    """Проверить сделки ETH"""
    try:
        api = MexAdvancedAPI()
        
        print("🔍 Проверяем сделки ETHUSDC...")
        
        # Получаем сделки
        trades = api.get_my_trades('ETHUSDC', limit=5)
        
        if not trades:
            print("❌ Нет сделок ETHUSDC")
            return
        
        print(f"📊 Найдено {len(trades)} сделок:")
        print("=" * 60)
        
        for i, trade in enumerate(trades):
            print(f"\nСделка {i+1}:")
            print(f"  ID: {trade.get('id', 'N/A')}")
            print(f"  Время: {trade.get('time', 'N/A')}")
            print(f"  Символ: {trade.get('symbol', 'N/A')}")
            print(f"  Сторона: {trade.get('side', 'N/A')}")
            print(f"  Количество: {trade.get('qty', 'N/A')}")
            print(f"  Цена: ${float(trade.get('price', 0)):.2f}")
            print(f"  Сумма: ${float(trade.get('quoteQty', 0)):.4f}")
            print(f"  Комиссия: {trade.get('commission', 'N/A')} {trade.get('commissionAsset', 'N/A')}")
            print(f"  Покупатель: {trade.get('isBuyer', 'N/A')}")
            
            # Анализ комиссии
            commission = float(trade.get('commission', 0))
            if commission > 0:
                print(f"  💸 КОМИССИЯ: {commission}")
            else:
                print(f"  ✅ БЕЗ КОМИССИИ")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    check_eth_trades()
