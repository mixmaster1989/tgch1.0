#!/usr/bin/env python3
"""
Простой тест фьючерсного API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mex_api import MexAPI
import time

def simple_test():
    """Простой тест"""
    print("🔍 Простой тест фьючерсного API...")
    
    try:
        api = MexAPI()
        print("✅ API инициализирован")
        
        # Тест спотового баланса для сравнения
        print("\n📊 Тест спотового баланса (для сравнения):")
        spot_info = api.get_account_info()
        print(f"Спотовый баланс получен: {type(spot_info)}")
        if isinstance(spot_info, dict):
            print(f"Ключи: {list(spot_info.keys())}")
        
        # Тест фьючерсного баланса с таймаутом
        print("\n📊 Тест фьючерсного баланса:")
        print("Попытка 1: get_futures_account_info()")
        
        # Устанавливаем короткий таймаута
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Таймаут запроса")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)  # 10 секунд таймаут
        
        try:
            futures_info = api.get_futures_account_info()
            signal.alarm(0)  # Отключаем таймаут
            print(f"✅ Фьючерсный баланс получен: {type(futures_info)}")
            if isinstance(futures_info, dict):
                print(f"Ключи: {list(futures_info.keys())}")
                if 'error' in futures_info:
                    print(f"❌ Ошибка: {futures_info['error']}")
                else:
                    print(f"✅ Успех: {futures_info}")
        except TimeoutError:
            print("⏰ Таймаут запроса (10 сек)")
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        finally:
            signal.alarm(0)  # Отключаем таймаут
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simple_test()
