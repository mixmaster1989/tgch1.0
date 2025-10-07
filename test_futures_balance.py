#!/usr/bin/env python3
"""
Тест получения баланса фьючерсного счета MEXC
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mex_api import MexAPI
from api.futures_api import FuturesAPI
import json

def test_futures_balance():
    """Тест получения фьючерсного баланса"""
    print("🔍 Тестирование получения фьючерсного баланса...")
    
    try:
        api = MexAPI()
        fapi = FuturesAPI()
        
        # Тест 1: Получение информации о фьючерсном аккаунте
        print("\n📊 Тест 1: get_futures_account_info()")
        futures_info = api.get_futures_account_info()
        print(f"Результат: {json.dumps(futures_info, indent=2, ensure_ascii=False)}")
        
        # Тест 2: Альтернативный метод получения баланса
        print("\n📊 Тест 2: get_futures_balance()")
        futures_balance = api.get_futures_balance()
        print(f"Результат: {json.dumps(futures_balance, indent=2, ensure_ascii=False)}")
        
        # Тест 3: Новый клиент FuturesAPI
        print("\n📊 Тест 3: FuturesAPI.get_account_asset()")
        futures_asset = fapi.get_account_asset()
        print(f"Результат: {json.dumps(futures_asset, indent=2, ensure_ascii=False)}")
        
        print("\n📊 Тест 4: FuturesAPI.get_account_info()")
        futures_info2 = fapi.get_account_info()
        print(f"Результат: {json.dumps(futures_info2, indent=2, ensure_ascii=False)}")
        
        # Анализ результатов
        print("\n🔍 Анализ результатов:")
        
        if 'error' in futures_info:
            print(f"❌ Ошибка в get_futures_account_info: {futures_info['error']}")
        else:
            print("✅ get_futures_account_info выполнен успешно")
            
        if 'error' in futures_balance:
            print(f"❌ Ошибка в get_futures_balance: {futures_balance['error']}")
        else:
            print("✅ get_futures_balance выполнен успешно")
            
        # Попытка извлечь баланс из результатов
        if 'data' in futures_info:
            print(f"\n💰 Данные фьючерсного аккаунта: {futures_info['data']}")
        elif 'assets' in futures_info:
            print(f"\n💰 Активы фьючерсного счета: {futures_info['assets']}")
        elif 'balance' in futures_info:
            print(f"\n💰 Баланс фьючерсного счета: {futures_info['balance']}")
            
        if 'data' in futures_balance:
            print(f"\n💰 Данные баланса: {futures_balance['data']}")
        elif 'assets' in futures_balance:
            print(f"\n💰 Активы: {futures_balance['assets']}")
        elif 'balance' in futures_balance:
            print(f"\n💰 Баланс: {futures_balance['balance']}")
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_futures_balance()
