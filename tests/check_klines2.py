#!/usr/bin/env python3
"""
Проверка формата klines v2
"""

from mex_api import MexAPI

def main():
    api = MexAPI()
    
    print("Проверка формата klines...")
    
    klines = api.get_klines('BTCUSDT', '1h', 10)
    print(f"Тип данных: {type(klines)}")
    print(f"Содержимое: {klines}")

if __name__ == "__main__":
    main()