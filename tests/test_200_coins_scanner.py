#!/usr/bin/env python3
"""
Тест сканера с 200 монетами
"""

import asyncio
import logging
from datetime import datetime
from market_scanner import MarketScanner

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_200_coins_scanner():
    """Тест сканера с 200 монетами"""
    try:
        print("🚀 ТЕСТ СКАНЕРА С 200 МОНЕТАМИ")
        print("=" * 60)
        print(f"Время: {datetime.now()}")
        print()
        
        # Создаем сканер
        scanner = MarketScanner()
        
        # Проверяем получение торговых пар
        print("📊 ПОЛУЧЕНИЕ ТОРГОВЫХ ПАР:")
        print("-" * 30)
        pairs = scanner.get_top_trading_pairs(200)
        print(f"✅ Получено пар: {len(pairs)}")
        print(f"📋 Первые 10 пар: {pairs[:10]}")
        print(f"📋 Последние 10 пар: {pairs[-10:]}")
        print()
        
        # Проверяем обновление списка
        print("🔄 ОБНОВЛЕНИЕ СПИСКА ПАР:")
        print("-" * 30)
        scanner.update_trading_pairs()
        print(f"✅ Обновлено пар: {len(scanner.trading_pairs)}")
        print()
        
        # Тестируем сканирование (ограниченное количество для теста)
        print("🔍 ТЕСТОВОЕ СКАНИРОВАНИЕ (первые 10 пар):")
        print("-" * 30)
        
        # Временно ограничиваем список для быстрого теста
        test_pairs = scanner.trading_pairs[:10]
        scanner.trading_pairs = test_pairs
        
        scan_results = scanner.scan_market()
        
        if scan_results:
            print(f"✅ Сканирование завершено!")
            print(f"📊 Проанализировано: {scan_results['analyzed_pairs']}/{scan_results['total_pairs']}")
            print(f"🎯 Возможности покупки: {len(scan_results['buy_opportunities'])}")
            print(f"⚠️ Нейтральные: {len(scan_results['neutral_pairs'])}")
            print(f"🚫 Заблокированные: {len(scan_results['blocked_pairs'])}")
            print(f"❌ Ошибки: {len(scan_results['errors'])}")
            
            # Показываем лучшие возможности
            if scan_results['buy_opportunities']:
                print(f"\n🎯 ЛУЧШИЕ ВОЗМОЖНОСТИ:")
                for i, opp in enumerate(scan_results['buy_opportunities'][:3], 1):
                    print(f"   {i}. {opp['symbol']} - Скор: {opp['score']}, RSI: {opp['rsi']:.1f}")
            
            # Форматируем отчет
            print(f"\n📋 ОТЧЕТ:")
            print("-" * 30)
            report = scanner.format_scan_report(scan_results)
            print(report)
            
        else:
            print("❌ Ошибка сканирования")
            
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        logger.error(f"Ошибка теста: {e}")

if __name__ == "__main__":
    asyncio.run(test_200_coins_scanner()) 