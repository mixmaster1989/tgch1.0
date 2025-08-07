#!/usr/bin/env python3
"""
Тест MEX API
"""

from mex_api import MexAPI

def main():
    api = MexAPI()
    
    print("Тест получения klines...")
    
    # Тестируем разные символы
    symbols = ['BTCUSDT', 'ETHUSDT', 'BROCKUSDT']
    
    for symbol in symbols:
        print(f"\n=== {symbol} ===")
        try:
            klines = api.get_klines(symbol, '1h', 100)
            print(f"Получено: {len(klines)} свечей")
            if len(klines) > 0:
                print(f"Первая свеча: {klines[0]}")
                print(f"Последняя свеча: {klines[-1]}")
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()