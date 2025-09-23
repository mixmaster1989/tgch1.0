#!/usr/bin/env python3
"""
Отладка exchange_info
"""

from mex_api import MexAPI
import json

def main():
    api = MexAPI()
    
    print("🔍 Получение exchange_info...")
    
    exchange_info = api.get_exchange_info()
    
    print("Тип ответа:", type(exchange_info))
    print("Содержимое:")
    print(json.dumps(exchange_info, indent=2, ensure_ascii=False)[:1000])
    
    if isinstance(exchange_info, dict):
        print("\nКлючи:", list(exchange_info.keys()))
        
        if 'symbols' in exchange_info:
            symbols = exchange_info['symbols']
            print(f"\nКоличество символов: {len(symbols)}")
            
            # Показываем первые несколько символов
            for i, symbol in enumerate(symbols[:5]):
                print(f"  {i+1}. {symbol}")
        else:
            print("❌ Ключ 'symbols' не найден")

if __name__ == "__main__":
    main()

