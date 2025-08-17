#!/usr/bin/env python3
"""
Отладка корреляций
"""

import asyncio
import time
from advanced_correlation_analyzer import advanced_correlation_analyzer

async def debug_correlations():
    """Отладка корреляций"""
    print("🔍 ОТЛАДКА КОРРЕЛЯЦИЙ")
    print("=" * 40)
    
    try:
        # Добавляем тестовые данные
        timestamp = int(time.time() * 1000)
        
        print("📊 Добавление тестовых данных...")
        
        # ETHUSDT данные
        for i in range(20):
            eth_price = 3700.0 * (1 + (i * 0.001 - 0.01))
            advanced_correlation_analyzer.add_price_data('ETHUSDT', eth_price, timestamp + i * 1000)
        
        # BTCUSDT данные
        for i in range(20):
            btc_price = 45000.0 * (1 + (i * 0.002 - 0.02))
            advanced_correlation_analyzer.add_price_data('BTCUSDT', btc_price, timestamp + i * 1000)
        
        # ADAUSDT данные
        for i in range(20):
            ada_price = 0.5 * (1 + (i * 0.001 - 0.01))
            advanced_correlation_analyzer.add_price_data('ADAUSDT', ada_price, timestamp + i * 1000)
        
        print("✅ Тестовые данные добавлены")
        
        # Получаем анализ
        print("\n🔍 Получение анализа корреляций...")
        eth_analysis = advanced_correlation_analyzer.get_comprehensive_correlation_analysis('ETHUSDT')
        
        print(f"\n📊 СТРУКТУРА ДАННЫХ КОРРЕЛЯЦИЙ:")
        print(f"   Тип данных: {type(eth_analysis)}")
        print(f"   Ключи: {list(eth_analysis.keys())}")
        
        print(f"\n📊 ДЕТАЛЬНЫЙ АНАЛИЗ:")
        for key, value in eth_analysis.items():
            print(f"   {key}: {type(value)} = {value}")
        
        # Проверяем базовые корреляции
        if 'basic_correlations' in eth_analysis:
            print(f"\n📊 БАЗОВЫЕ КОРРЕЛЯЦИИ:")
            basic_corr = eth_analysis['basic_correlations']
            for asset, corr_data in basic_corr.items():
                print(f"   {asset}: {corr_data}")
        
        # Проверяем рыночный режим
        if 'market_regime' in eth_analysis:
            print(f"\n📊 РЫНОЧНЫЙ РЕЖИМ:")
            market_regime = eth_analysis['market_regime']
            for key, value in market_regime.items():
                print(f"   {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отладки: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(debug_correlations()) 