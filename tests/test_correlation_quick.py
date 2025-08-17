#!/usr/bin/env python3
"""
Быстрый тест корреляций
"""

import asyncio
import time
from correlation_analyzer import CorrelationAnalyzer

def test_correlation_quick():
    """Быстрый тест корреляций"""
    print("🔗 БЫСТРЫЙ ТЕСТ КОРРЕЛЯЦИЙ")
    print("=" * 30)
    
    try:
        analyzer = CorrelationAnalyzer()
        
        # Добавляем данные
        timestamp = int(time.time() * 1000)
        
        # BTCUSDT
        analyzer.add_price_data('BTCUSDT', 115000.0, timestamp)
        analyzer.add_price_data('BTCUSDT', 115100.0, timestamp + 1000)
        analyzer.add_price_data('BTCUSDT', 115200.0, timestamp + 2000)
        
        # ETHUSDT
        analyzer.add_price_data('ETHUSDT', 3670.0, timestamp)
        analyzer.add_price_data('ETHUSDT', 3675.0, timestamp + 1000)
        analyzer.add_price_data('ETHUSDT', 3680.0, timestamp + 2000)
        
        # Проверяем корреляции
        btc_corr = analyzer.calculate_correlations('BTCUSDT')
        eth_corr = analyzer.calculate_correlations('ETHUSDT')
        
        print(f"📊 BTCUSDT данные: {len(analyzer.price_data['BTCUSDT'])} точек")
        print(f"📊 ETHUSDT данные: {len(analyzer.price_data['ETHUSDT'])} точек")
        
        if btc_corr and eth_corr:
            print("✅ Корреляции работают!")
            return True
        else:
            print("❌ Корреляции не работают")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        return False

if __name__ == "__main__":
    test_correlation_quick() 