#!/usr/bin/env python3
"""
Простой тест корреляций
"""

import asyncio
import time
from advanced_correlation_analyzer import advanced_correlation_analyzer

async def test_correlations_simple():
    """Простой тест корреляций"""
    print("🔗 ПРОСТОЙ ТЕСТ КОРРЕЛЯЦИЙ")
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
        
        # Проверяем корреляции
        print("\n🔍 Проверка корреляций...")
        
        eth_corr = advanced_correlation_analyzer.get_comprehensive_correlation_analysis('ETHUSDT')
        btc_corr = advanced_correlation_analyzer.get_comprehensive_correlation_analysis('BTCUSDT')
        
        print(f"\n📊 ETHUSDT корреляции:")
        print(f"   BTC корреляция: {eth_corr.get('btc_correlation', 0):.4f}")
        print(f"   Ранг волатильности: {eth_corr.get('volatility_rank', 0)}")
        print(f"   Сила корреляции: {eth_corr.get('correlation_strength', 'unknown')}")
        
        print(f"\n📊 BTCUSDT корреляции:")
        print(f"   ETH корреляция: {btc_corr.get('eth_correlation', 0):.4f}")
        print(f"   Ранг волатильности: {btc_corr.get('volatility_rank', 0)}")
        print(f"   Сила корреляции: {btc_corr.get('correlation_strength', 'unknown')}")
        
        # Проверяем базовый анализатор
        from correlation_analyzer import CorrelationAnalyzer
        basic_analyzer = CorrelationAnalyzer()
        
        # Добавляем данные в базовый анализатор
        for i in range(20):
            eth_price = 3700.0 * (1 + (i * 0.001 - 0.01))
            btc_price = 45000.0 * (1 + (i * 0.002 - 0.02))
            basic_analyzer.add_price_data('ETHUSDT', eth_price, timestamp + i * 1000)
            basic_analyzer.add_price_data('BTCUSDT', btc_price, timestamp + i * 1000)
        
        basic_corr = basic_analyzer.calculate_correlations('ETHUSDT')
        print(f"\n📊 Базовый анализатор:")
        print(f"   Корреляции: {basic_corr}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_correlations_simple()) 