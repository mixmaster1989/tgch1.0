#!/usr/bin/env python3
"""
Тестовый скрипт для проверки API MEX
"""

from mex_api import MexAPI
import json

def main():
    api = MexAPI()
    
    print("🔍 Тестирование API MEX...")
    
    try:
        # 1. Тест получения информации об аккаунте
        print("\n1. Тест получения информации об аккаунте:")
        account_info = api.get_account_info()
        print(f"Результат: {account_info}")
        
        # 2. Тест получения цены
        print("\n2. Тест получения цены BTCUSDT:")
        price_info = api.get_ticker_price('BTCUSDT')
        print(f"Результат: {price_info}")
        
        # 3. Тест получения стакана
        print("\n3. Тест получения стакана BTCUSDT:")
        depth_info = api.get_depth('BTCUSDT', 5)
        print(f"Результат: {depth_info}")
        
        # 4. Тест размещения тестового ордера (с очень маленькой суммой)
        print("\n4. Тест размещения ордера BTCUSDT:")
        test_order = api.place_order(
            symbol='BTCUSDT',
            side='BUY',
            quantity=0.0001,  # Очень маленькое количество
            price=100000  # Низкая цена, чтобы ордер не исполнился
        )
        print(f"Результат: {test_order}")
        
        # 5. Тест с другими символами
        test_symbols = ['ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'BROCKUSDT']
        for symbol in test_symbols:
            print(f"\n5. Тест размещения ордера {symbol}:")
            try:
                test_order = api.place_order(
                    symbol=symbol,
                    side='BUY',
                    quantity=0.001,
                    price=1  # Очень низкая цена
                )
                print(f"Результат: {test_order}")
            except Exception as e:
                print(f"Ошибка: {e}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main() 