#!/usr/bin/env python3
"""
Тест комплексного менеджера данных
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Добавляем корневую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from comprehensive_data_manager import ComprehensiveDataManager

async def test_comprehensive_data_manager():
    """Тест комплексного менеджера данных"""
    print("🚀 ТЕСТ КОМПЛЕКСНОГО МЕНЕДЖЕРА ДАННЫХ")
    print("=" * 60)
    
    manager = ComprehensiveDataManager()
    
    # Счетчики обновлений
    market_updates = 0
    account_updates = 0
    news_updates = 0
    
    # Callbacks для отслеживания обновлений
    async def market_callback(data):
        nonlocal market_updates
        market_updates += 1
        # Показываем обновления только каждые 10 раз
        if market_updates % 10 == 0:
            print(f"📊 Обновление рыночных данных #{market_updates}: {len(data)} символов")
            
            # Показываем топ-3 по объему только каждые 30 обновлений
            if market_updates % 30 == 0 and data:
                top_symbols = sorted(data.items(), 
                                   key=lambda x: x[1].quote_volume_24h if hasattr(x[1], 'quote_volume_24h') else 0, 
                                   reverse=True)[:3]
                for symbol, market_data in top_symbols:
                    print(f"  {symbol}: ${market_data.price:.6f} (объем: ${market_data.quote_volume_24h:,.0f})")
    
    async def account_callback(data):
        nonlocal account_updates
        account_updates += 1
        # Показываем обновления аккаунта только каждые 5 раз
        if account_updates % 5 == 0:
            print(f"💰 Обновление аккаунта #{account_updates}: ${data.total_usdt:.2f} USDT")
            print(f"  Позиций: {len(data.positions)}")
            for pos in data.positions[:3]:  # Показываем первые 3
                print(f"    {pos['asset']}: {pos['quantity']:.6f}")
    
    async def news_callback(data):
        nonlocal news_updates
        news_updates += 1
        # Показываем обновления новостей только каждые 3 раза
        if news_updates % 3 == 0:
            print(f"📰 Обновление новостей #{news_updates}: {data.symbol}")
            print(f"  Настроения: {data.sentiment}, Влияние: {data.impact_score:.2f}")
            if data.news:
                print(f"  Последняя новость: {data.news[0].get('title', 'N/A')[:50]}...")
    
    # Подписываемся на обновления
    manager.subscribe_market_updates(market_callback)
    manager.subscribe_account_updates(account_callback)
    manager.subscribe_news_updates(news_callback)
    
    try:
        print("🔌 Запуск менеджера данных...")
        await manager.start()
        
        print("📡 Подписка на символы...")
        await manager.subscribe_multiple_symbols(['BTCUSDT', 'ETHUSDT', 'ADAUSDT'])
        
        print("⏳ Ожидание данных (90 секунд)...")
        print("=" * 60)
        
        # Ждем и собираем статистику
        start_time = datetime.now()
        await asyncio.sleep(90)
        end_time = datetime.now()
        
        print("=" * 60)
        print("📈 СТАТИСТИКА РАБОТЫ:")
        print(f"  Время работы: {(end_time - start_time).total_seconds():.1f} секунд")
        print(f"  Обновлений рыночных данных: {market_updates}")
        print(f"  Обновлений аккаунта: {account_updates}")
        print(f"  Обновлений новостей: {news_updates}")
        
        # Получаем финальные данные
        print("\n📊 ФИНАЛЬНЫЕ ДАННЫЕ:")
        
        # Рыночные данные
        market_data = manager.get_market_data()
        print(f"  Рыночных символов: {len(market_data)}")
        
        # Кандидаты для торговли
        candidates = manager.get_trading_candidates(min_volume=50000)
        print(f"  Кандидатов для торговли: {len(candidates)}")
        if candidates:
            print("  Топ-3 кандидата:")
            for i, candidate in enumerate(candidates[:3], 1):
                print(f"    {i}. {candidate['symbol']}: ${candidate['price']:.6f} (скор: {candidate['score']:.1f})")
        
        # Данные аккаунта
        account_data = manager.get_account_data()
        if account_data:
            print(f"  Баланс USDT: ${account_data.total_usdt:.2f}")
            print(f"  Активных позиций: {len(account_data.positions)}")
        
        # Сводка портфеля
        portfolio = manager.get_portfolio_summary()
        if portfolio:
            print(f"  Портфель: ${portfolio.get('total_usdt', 0):.2f} USDT")
            print(f"  Позиций в портфеле: {portfolio.get('positions_count', 0)}")
        
        # Новостные данные
        news_data = manager.get_news_data()
        print(f"  Новостных символов: {len(news_data)}")
        
        print("\n✅ Тест завершен успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        print("🛑 Остановка менеджера...")
        await manager.stop()

async def test_data_quality():
    """Тест качества данных"""
    print("\n🔍 ТЕСТ КАЧЕСТВА ДАННЫХ")
    print("=" * 40)
    
    manager = ComprehensiveDataManager()
    
    try:
        await manager.start()
        await asyncio.sleep(10)  # Ждем первые данные
        
        # Проверяем рыночные данные
        market_data = manager.get_market_data()
        if market_data:
            print("✅ Рыночные данные получены")
            
            # Проверяем структуру данных
            sample_data = next(iter(market_data.values()))
            required_fields = ['symbol', 'price', 'change_24h', 'volume_24h', 'quote_volume_24h']
            
            for field in required_fields:
                if hasattr(sample_data, field):
                    print(f"  ✅ Поле {field}: OK")
                else:
                    print(f"  ❌ Поле {field}: MISSING")
        else:
            print("❌ Рыночные данные не получены")
        
        # Проверяем данные аккаунта
        account_data = manager.get_account_data()
        if account_data:
            print("✅ Данные аккаунта получены")
            print(f"  Баланс USDT: ${account_data.total_usdt:.2f}")
        else:
            print("❌ Данные аккаунта не получены")
        
        # Проверяем источники данных
        print("\n📡 ИСТОЧНИКИ ДАННЫХ:")
        if market_data:
            sources = set(data.source.value for data in market_data.values())
            print(f"  Рыночные данные: {', '.join(sources)}")
        
        if account_data:
            print(f"  Данные аккаунта: {account_data.source.value}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте качества: {e}")
        return False
        
    finally:
        await manager.stop()

async def main():
    """Основная функция тестирования"""
    print("🧪 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ДАННЫХ")
    print("=" * 60)
    
    # Тест 1: Основной функционал
    test1_ok = await test_comprehensive_data_manager()
    
    # Тест 2: Качество данных
    test2_ok = await test_data_quality()
    
    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"  Основной функционал: {'✅ OK' if test1_ok else '❌ FAIL'}")
    print(f"  Качество данных: {'✅ OK' if test2_ok else '❌ FAIL'}")
    
    if test1_ok and test2_ok:
        print("\n🎉 Все тесты прошли успешно!")
        print("Комплексный менеджер данных готов к использованию")
    else:
        print("\n⚠️ Некоторые тесты не прошли")
        print("Проверьте подключение и настройки")

if __name__ == "__main__":
    asyncio.run(main()) 