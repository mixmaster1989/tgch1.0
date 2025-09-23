#!/usr/bin/env python3
"""
Тест исправления интервалов
"""

from mex_api import MexAPI
import time

def test_intervals():
    """Тестируем различные интервалы"""
    api = MexAPI()
    
    print("🧪 ТЕСТ ИНТЕРВАЛОВ MEXC API")
    print("=" * 40)
    
    symbol = "BTCUSDT"
    intervals = ['1m', '5m', '15m', '30m', '60m', '240m', '1d']
    
    for interval in intervals:
        print(f"\n📊 Тестируем интервал: {interval}")
        try:
            start_time = time.time()
            klines = api.get_klines(symbol, interval, 10)
            end_time = time.time()
            
            if klines and len(klines) > 0:
                print(f"   ✅ Успешно! Получено {len(klines)} свечей за {end_time - start_time:.2f}с")
                print(f"   📈 Последняя цена: ${float(klines[-1][4]):.2f}")
            else:
                print(f"   ❌ Пустой ответ")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        time.sleep(0.5)  # Небольшая пауза между запросами
    
    print("\n" + "=" * 40)
    print("✅ Тест завершен!")

if __name__ == "__main__":
    test_intervals()
