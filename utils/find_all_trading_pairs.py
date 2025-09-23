#!/usr/bin/env python3
"""
Найти все пары, по которым есть сделки
"""

from mexc_advanced_api import MexAdvancedAPI
import time

def main():
    advanced_api = MexAdvancedAPI()
    
    print("🔍 Поиск всех пар с сделками...")
    
    # Получаем все спот пары
    from mex_api import MexAPI
    api = MexAPI()
    exchange_info = api.get_exchange_info()
    
    if not isinstance(exchange_info, dict) or 'symbols' not in exchange_info:
        print("❌ Не удалось получить список пар")
        return
    
    # Фильтруем только USDT пары
    usdt_pairs = []
    for symbol_info in exchange_info['symbols']:
        symbol = symbol_info.get('symbol', '')
        status = symbol_info.get('status', '')
        if symbol.endswith('USDT') and (status == 'TRADING' or status == '1'):
            usdt_pairs.append(symbol)
    
    print(f"📊 Найдено {len(usdt_pairs)} USDT пар")
    
    # Проверяем каждую пару на наличие сделок
    pairs_with_trades = []
    
    for i, symbol in enumerate(usdt_pairs):
        if i % 50 == 0:
            print(f"Проверено {i}/{len(usdt_pairs)} пар...")
        
        try:
            trades = advanced_api.get_my_trades(symbol, limit=1)
            if trades:
                pairs_with_trades.append(symbol)
                print(f"✅ {symbol}: {len(trades)} сделок")
        except Exception as e:
            print(f"❌ Ошибка для {symbol}: {e}")
            continue
        
        # Небольшая пауза чтобы не перегрузить API
        time.sleep(0.1)
    
    print(f"\n📈 Итого найдено {len(pairs_with_trades)} пар с сделками:")
    for pair in pairs_with_trades:
        print(f"  - {pair}")
    
    return pairs_with_trades

if __name__ == "__main__":
    main()
