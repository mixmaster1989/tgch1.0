#!/usr/bin/env python3
"""
Тест антихайп фильтров с РЕАЛЬНЫМИ данными биржи MEXC
"""

import sys
import logging
from anti_hype_filter import AntiHypeFilter
from rebalancer_anti_hype_filter import RebalancerAntiHypeFilter

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_filters():
    """Тестируем фильтры с реальными данными"""
    
    print("🧪 ТЕСТ АНТИХАЙП ФИЛЬТРОВ С РЕАЛЬНЫМИ ДАННЫМИ MEXC")
    print("=" * 60)
    
    # Создаем фильтры
    anti_hype = AntiHypeFilter()
    rebalancer = RebalancerAntiHypeFilter()
    
    symbols = ['BTCUSDC', 'ETHUSDC']
    
    for symbol in symbols:
        print(f"\n🔍 ТЕСТ {symbol}:")
        print("-" * 30)
        
        # Тест обычного антихайп фильтра
        print("📊 ОБЫЧНЫЙ АНТИХАЙП ФИЛЬТР:")
        try:
            result = anti_hype.check_buy_permission(symbol)
            print(f"   Разрешено: {result['allowed']}")
            print(f"   Причина: {result['reason']}")
            print(f"   Множитель: {result['multiplier']}")
            
            # Если есть данные о дневном максимуме
            if 'daily_high' in result:
                print(f"   📈 Дневной максимум: ${result['daily_high']:.2f}")
                print(f"   💰 Текущая цена: ${result['current_price']:.2f}")
                print(f"   📏 Расстояние от хая: {result['distance_percent']:.2f}%")
                if result.get('block_type'):
                    print(f"   🚫 Тип блокировки: {result['block_type']}")
        except Exception as e:
            print(f"   ❌ ОШИБКА: {e}")
        
        # Тест ребалансировочного фильтра
        print("\n📊 РЕБАЛАНСИРОВОЧНЫЙ ФИЛЬТР:")
        try:
            result = rebalancer.check_buy_permission(symbol)
            print(f"   Разрешено: {result['allowed']}")
            print(f"   Причина: {result['reason']}")
            print(f"   Множитель: {result['multiplier']}")
            
            # Если есть данные о дневном максимуме
            if 'daily_high' in result:
                print(f"   📈 Дневной максимум: ${result['daily_high']:.2f}")
                print(f"   💰 Текущая цена: ${result['current_price']:.2f}")
                print(f"   📏 Расстояние от хая: {result['distance_percent']:.2f}%")
                if result.get('block_type'):
                    print(f"   🚫 Тип блокировки: {result['block_type']}")
        except Exception as e:
            print(f"   ❌ ОШИБКА: {e}")
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТ ЗАВЕРШЕН!")

if __name__ == "__main__":
    test_filters() 