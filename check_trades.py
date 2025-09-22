#!/usr/bin/env python3
"""
Проверка наличия сделок в аккаунте
"""

from mexc_advanced_api import MexAdvancedAPI
from mex_api import MexAPI
import json

def main():
    api = MexAPI()
    advanced_api = MexAdvancedAPI()
    
    print("🔍 Проверка аккаунта и сделок...")
    
    # Проверяем информацию об аккаунте
    print("\n1. Информация об аккаунте:")
    account_info = api.get_account_info()
    print(json.dumps(account_info, indent=2, ensure_ascii=False))
    
    # Проверяем баланс
    if isinstance(account_info, dict) and 'balances' in account_info:
        print("\n2. Балансы:")
        for balance in account_info['balances']:
            if float(balance.get('free', 0)) > 0 or float(balance.get('locked', 0)) > 0:
                print(f"  {balance['asset']}: {balance['free']} (свободно), {balance['locked']} (заблокировано)")
    
    # Проверяем несколько популярных пар на наличие сделок
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'USDCUSDT']
    
    print("\n3. Проверка сделок по популярным парам:")
    for symbol in test_symbols:
        print(f"\n{symbol}:")
        trades = advanced_api.get_my_trades(symbol, limit=10)
        if trades:
            print(f"  Найдено {len(trades)} сделок")
            for trade in trades[:3]:  # Показываем первые 3
                side = "BUY" if trade.get('isBuyer', False) else "SELL"
                print(f"    {trade['time']} - {side} {trade['qty']} @ {trade['price']}")
                print(f"      Детали: {json.dumps(trade, indent=6, ensure_ascii=False)}")
        else:
            print("  Сделок не найдено")

if __name__ == "__main__":
    main()
