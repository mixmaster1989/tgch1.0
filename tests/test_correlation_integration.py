#!/usr/bin/env python3
"""
Тест интеграции расширенного анализатора корреляций с реальными данными
Проверяет получение данных других активов через REST API
"""

import asyncio
import time
from comprehensive_data_manager import ComprehensiveDataManager
from advanced_correlation_analyzer import advanced_correlation_analyzer

async def test_correlation_integration():
    """Тест интеграции корреляций с реальными данными"""
    print("🚀 ТЕСТ ИНТЕГРАЦИИ КОРРЕЛЯЦИЙ С РЕАЛЬНЫМИ ДАННЫМИ")
    print("=" * 60)
    
    # Создаем менеджер данных
    data_manager = ComprehensiveDataManager()
    
    try:
        # Запускаем менеджер
        print("📡 Запуск менеджера данных...")
        await data_manager.start()
        
        # Ждем немного для накопления данных
        print("⏳ Ожидание накопления данных (30 секунд)...")
        await asyncio.sleep(30)
        
        # Проверяем данные в расширенном анализаторе
        print("\n📊 ПРОВЕРКА ДАННЫХ В РАСШИРЕННОМ АНАЛИЗАТОРЕ:")
        print("-" * 40)
        
        if hasattr(advanced_correlation_analyzer, 'price_data'):
            total_points = sum(len(prices) for prices in advanced_correlation_analyzer.price_data.values())
            print(f"Всего точек данных: {total_points}")
            
            for asset, prices in advanced_correlation_analyzer.price_data.items():
                print(f"  {asset}: {len(prices)} точек")
                if len(prices) > 0:
                    latest_price = prices[-1]['price']
                    print(f"    Последняя цена: ${latest_price:.4f}")
        else:
            print("❌ Данные не найдены в анализаторе")
        
        # Получаем корреляции для ETH
        print("\n🔗 КОРРЕЛЯЦИИ ETH:")
        print("-" * 40)
        
        correlation_data = data_manager.get_correlation_data('ETHUSDT')
        
        if correlation_data and 'basic_correlations' in correlation_data:
            correlations = correlation_data['basic_correlations']
            for asset, corr_info in correlations.items():
                if isinstance(corr_info, dict) and 'correlation' in corr_info:
                    corr_value = corr_info['correlation']
                    strength = corr_info.get('strength', 'unknown')
                    direction = corr_info.get('direction', 'unknown')
                    print(f"  {asset}: {corr_value:.4f} ({strength}, {direction})")
        else:
            print("❌ Корреляции не найдены")
        
        # Получаем полный анализ
        print("\n📈 ПОЛНЫЙ АНАЛИЗ КОРРЕЛЯЦИЙ:")
        print("-" * 40)
        
        if correlation_data:
            # Рыночный режим
            if 'market_regime' in correlation_data:
                regime = correlation_data['market_regime']
                print(f"Рыночный режим: {regime.get('regime', 'unknown')}")
                print(f"Корреляция с BTC: {regime.get('btc_correlation', 0):.4f}")
            
            # Анализ волатильности
            if 'volatility_analysis' in correlation_data:
                vol = correlation_data['volatility_analysis']
                print(f"Волатильность: {vol.get('current_volatility', 0):.2%}")
                print(f"Ранг волатильности: {vol.get('volatility_rank', 0)}")
            
            # Торговые сигналы
            if 'trading_signals' in correlation_data:
                signals = correlation_data['trading_signals']
                if signals:
                    print(f"Торговые сигналы: {len(signals)} активных")
                    for signal in signals[:2]:  # Показываем первые 2
                        print(f"  {signal.signal_type}: {signal.reason}")
                else:
                    print("Торговые сигналы: нет активных")
            
            # Оценка рисков
            if 'risk_assessment' in correlation_data:
                risks = correlation_data['risk_assessment']
                print(f"Общий риск: {risks.get('overall_risk_score', 0):.3f}")
        
        # Ждем еще немного для дополнительных данных
        print("\n⏳ Ожидание дополнительных данных (60 секунд)...")
        await asyncio.sleep(60)
        
        # Финальная проверка
        print("\n📊 ФИНАЛЬНАЯ ПРОВЕРКА:")
        print("-" * 40)
        
        final_correlation = data_manager.get_correlation_data('ETHUSDT')
        if final_correlation and 'basic_correlations' in final_correlation:
            correlations = final_correlation['basic_correlations']
            for asset, corr_info in correlations.items():
                if isinstance(corr_info, dict) and 'correlation' in corr_info:
                    corr_value = corr_info['correlation']
                    if corr_value != 0.0:
                        print(f"✅ {asset}: {corr_value:.4f} - РЕАЛЬНЫЕ КОРРЕЛЯЦИИ РАБОТАЮТ!")
                    else:
                        print(f"⚠️ {asset}: {corr_value:.4f} - нужны дополнительные данные")
        
        print("\n✅ ТЕСТ ЗАВЕРШЕН")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Останавливаем менеджер
        print("\n🛑 Остановка менеджера данных...")
        await data_manager.stop()

async def test_rest_api_data_fetch():
    """Тест получения данных через REST API"""
    print("\n🔧 ТЕСТ ПОЛУЧЕНИЯ ДАННЫХ ЧЕРЕЗ REST API")
    print("=" * 50)
    
    data_manager = ComprehensiveDataManager()
    
    try:
        # Тестируем получение данных других активов
        print("📡 Получение данных активов для корреляций...")
        await data_manager._fetch_other_assets_data()
        
        # Проверяем результат
        print("\n📊 РЕЗУЛЬТАТ ПОЛУЧЕНИЯ ДАННЫХ:")
        print("-" * 30)
        
        if hasattr(advanced_correlation_analyzer, 'price_data'):
            for asset, prices in advanced_correlation_analyzer.price_data.items():
                if len(prices) > 0:
                    latest = prices[-1]
                    print(f"✅ {asset}: ${latest['price']:.4f} (время: {latest['timestamp']})")
                else:
                    print(f"❌ {asset}: нет данных")
        
        print("\n✅ ТЕСТ REST API ЗАВЕРШЕН")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте REST API: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Главная функция"""
    print("🎯 ТЕСТ ИНТЕГРАЦИИ КОРРЕЛЯЦИЙ")
    print("=" * 50)
    
    # Запускаем тесты
    asyncio.run(test_rest_api_data_fetch())
    asyncio.run(test_correlation_integration())

if __name__ == "__main__":
    main() 