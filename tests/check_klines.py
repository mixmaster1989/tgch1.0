#!/usr/bin/env python3
"""
Проверка формата klines
"""

from mex_api import MexAPI

def main():
    api = MexAPI()
    
    print("Проверка формата klines...")
    
    klines = api.get_klines('BTCUSDT', '1h', 10)
    print(f"Тип данных: {type(klines)}")
    print(f"Количество: {len(klines)}")
    
    if len(klines) > 0:
        print(f"Первый элемент: {klines[0]}")
        print(f"Тип первого элемента: {type(klines[0])}")
        
        if isinstance(klines[0], list) and len(klines[0]) > 4:
            print(f"Цена закрытия: {klines[0][4]}")
        else:
            print("Неожиданный формат данных!")
            print(f"Содержимое: {klines}")

if __name__ == "__main__":
    main()