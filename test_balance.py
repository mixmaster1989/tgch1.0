#!/usr/bin/env python3
"""
Тест получения баланса аккаунта MEX
"""

from mex_api import MexAPI
import json

def test_balance():
    try:
        # Создаем экземпляр API
        mex = MexAPI()
        
        print("Получаю баланс аккаунта MEX...")
        
        # Получаем информацию об аккаунте
        account_info = mex.get_account_info()
        
        print("\nРезультат запроса:")
        print(json.dumps(account_info, indent=2))
        
        # Если есть балансы, показываем их
        if 'balances' in account_info:
            print("\nБаланс аккаунта:")
            balances = [b for b in account_info['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
            
            if balances:
                for balance in balances:
                    free = float(balance['free'])
                    locked = float(balance['locked'])
                    print(f"{balance['asset']}: {free:.8f} (заблокировано: {locked:.8f})")
            else:
                print("Нет активных балансов")
        else:
            print("Ошибка получения балансов")
            
    except Exception as e:
        print(f"Ошибка: {str(e)}")

if __name__ == "__main__":
    test_balance()