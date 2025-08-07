#!/usr/bin/env python3
"""
Отладка данных свечей
"""

from mex_api import MexAPI
import json

def debug_klines():
    api = MexAPI()
    
    print("🔍 ОТЛАДКА ДАННЫХ СВЕЧЕЙ")
    print("=" * 40)
    
    # Получаем данные свечей
    klines = api.get_klines("ETHUSDT", interval='1h', limit=5)
    
    print(f"Тип данных: {type(klines)}")
    print(f"Количество элементов: {len(klines) if klines else 0}")
    print()
    
    print("Содержимое ответа:")
    print(json.dumps(klines, indent=2))
    
    # Проверяем структуру
    if isinstance(klines, dict):
        print(f"\nКлючи в ответе: {list(klines.keys())}")
        if 'data' in klines:
            data = klines['data']
            print(f"Тип data: {type(data)}")
            if isinstance(data, list) and len(data) > 0:
                print(f"Количество свечей: {len(data)}")
                print(f"Первая свеча: {data[0]}")

if __name__ == "__main__":
    debug_klines() 