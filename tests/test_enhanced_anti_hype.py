#!/usr/bin/env python3
"""
Тест усиленного анти-хайп фильтра
Проверяем новые функции защиты от покупок на хайпах
"""

import asyncio
import logging
from anti_hype_filter import AntiHypeFilter

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_enhanced_anti_hype_filter():
    """Тест усиленного анти-хайп фильтра"""
    
    filter = AntiHypeFilter()
    
    # Тестовые символы
    test_symbols = [
        'BTCUSDT',  # Основной
        'ETHUSDT',  # Основной
        'BNBUSDT',  # Альт
        'SOLUSDT',  # Альт
        'DOTUSDT',  # Альт
    ]
    
    print("🔍 ТЕСТИРОВАНИЕ УСИЛЕННОГО АНТИ-ХАЙП ФИЛЬТРА")
    print("=" * 60)
    
    for symbol in test_symbols:
        print(f"\n📊 Проверка {symbol}:")
        print("-" * 40)
        
        try:
            result = filter.check_buy_permission(symbol)
            
            status = "✅ РАЗРЕШЕНО" if result['allowed'] else "🚫 ЗАБЛОКИРОВАНО"
            multiplier = result['multiplier']
            reason = result['reason']
            
            print(f"Статус: {status}")
            print(f"Множитель: {multiplier}")
            print(f"Причина: {reason}")
            
            # Анализ множителя
            if multiplier == 0.0:
                print("💀 ПОЛНАЯ БЛОКИРОВКА - НЕ ПОКУПАТЬ!")
            elif multiplier == 0.3:
                print("⚠️ СИЛЬНОЕ ОГРАНИЧЕНИЕ - 70% снижение")
            elif multiplier == 0.5:
                print("⚠️ ОГРАНИЧЕНИЕ - 50% снижение")
            elif multiplier == 1.0:
                print("✅ НОРМАЛЬНАЯ ПОКУПКА")
            elif multiplier == 2.0:
                print("🚀 DCA УСИЛЕНИЕ - 2x покупка!")
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        # Пауза между запросами
        await asyncio.sleep(1)
    
    print("\n" + "=" * 60)
    print("🎯 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("✅ Фильтр усилен против хайпов")
    print("✅ Добавлена проверка исторических максимумов")
    print("✅ Добавлена проверка объемов хайпа")
    print("✅ Снижены пороги RSI для ранней блокировки")
    print("✅ Усилены ограничения в нейтральной зоне")

if __name__ == "__main__":
    asyncio.run(test_enhanced_anti_hype_filter())
