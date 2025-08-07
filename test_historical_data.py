#!/usr/bin/env python3
"""
Быстрый тест загрузки исторических данных для корреляций
"""

import asyncio
from comprehensive_data_manager import ComprehensiveDataManager
from advanced_correlation_analyzer import advanced_correlation_analyzer

async def test_historical_data():
    """Тест загрузки исторических данных"""
    print("🚀 ТЕСТ ЗАГРУЗКИ ИСТОРИЧЕСКИХ ДАННЫХ")
    print("=" * 50)
    
    data_manager = ComprehensiveDataManager()
    
    try:
        # Загружаем исторические данные
        print("📚 Загрузка исторических данных...")
        await data_manager._load_historical_data_for_correlations()
        
        # Проверяем результат
        print("\n📊 РЕЗУЛЬТАТ ЗАГРУЗКИ:")
        print("-" * 30)
        
        if hasattr(advanced_correlation_analyzer, 'price_data'):
            total_points = sum(len(prices) for prices in advanced_correlation_analyzer.price_data.values())
            print(f"Всего точек данных: {total_points}")
            
            for asset, prices in advanced_correlation_analyzer.price_data.items():
                print(f"  {asset}: {len(prices)} точек")
                if len(prices) > 0:
                    latest = prices[-1]
                    oldest = prices[0]
                    print(f"    Последняя: ${latest['price']:.4f} (время: {latest['timestamp']})")
                    print(f"    Первая: ${oldest['price']:.4f} (время: {oldest['timestamp']})")
        
        # Тестируем корреляции
        print("\n🔗 ТЕСТ КОРРЕЛЯЦИЙ:")
        print("-" * 30)
        
        correlation_data = data_manager.get_correlation_data('ETHUSDT')
        if correlation_data and 'basic_correlations' in correlation_data:
            correlations = correlation_data['basic_correlations']
            for asset, corr_info in correlations.items():
                if isinstance(corr_info, dict) and 'correlation' in corr_info:
                    corr_value = corr_info['correlation']
                    strength = corr_info.get('strength', 'unknown')
                    print(f"  {asset}: {corr_value:.4f} ({strength})")
                    
                    if corr_value != 0.0:
                        print(f"    ✅ РЕАЛЬНЫЕ КОРРЕЛЯЦИИ РАБОТАЮТ!")
                    else:
                        print(f"    ⚠️ Корреляция = 0.0000")
        else:
            print("❌ Корреляции не найдены")
        
        print("\n✅ ТЕСТ ЗАВЕРШЕН")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_historical_data())
