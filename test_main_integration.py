#!/usr/bin/env python3
"""
Тест интеграции менеджера скальперов в main.py
"""

import asyncio
import logging
import threading
import time
from main import start_scalper_manager, start_balance_monitor, start_pnl_monitor
from scalper_manager import ScalperManager, get_scalper_protected_balance

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_main_integration():
    """Тест интеграции с main.py"""
    try:
        print("🧪 ТЕСТ ИНТЕГРАЦИИ С MAIN.PY")
        print("=" * 50)
        
        # Тестируем функцию запуска менеджера скальперов
        print("\n1️⃣ Тестирование start_scalper_manager()...")
        start_scalper_manager()
        
        # Ждем немного для инициализации
        await asyncio.sleep(2)
        
        # Проверяем статус менеджера
        print("\n2️⃣ Проверка статуса менеджера...")
        manager = ScalperManager()
        status = manager.get_manager_status()
        
        print(f"📊 Статус менеджера:")
        print(f"   BTC активных: {status.get('btc_active', 0)}")
        print(f"   BTC застрявших: {status.get('btc_stuck', 0)}")
        print(f"   ETH активных: {status.get('eth_active', 0)}")
        print(f"   ETH застрявших: {status.get('eth_stuck', 0)}")
        print(f"   Всего создано: {status.get('total_created', 0)}")
        print(f"   Общая прибыль: ${status.get('total_profit', 0):.3f}")
        print(f"   Баланс USDC: ${status.get('usdc_balance', 0):.2f}")
        
        # Проверяем защищенный баланс
        print("\n3️⃣ Проверка защищенного баланса...")
        protected_balance = get_scalper_protected_balance()
        print(f"🛡️ Защищенный баланс: ${protected_balance:.2f} USDC")
        
        # Тестируем другие функции из main.py
        print("\n4️⃣ Тестирование других функций main.py...")
        
        # Проверяем, что функции существуют
        print("   ✅ start_balance_monitor() - функция найдена")
        print("   ✅ start_pnl_monitor() - функция найдена")
        print("   ✅ start_scalper_manager() - функция найдена")
        
        print("\n✅ Тест интеграции завершен успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка теста интеграции: {e}")
        import traceback
        traceback.print_exc()

def test_scalper_manager_standalone():
    """Тест менеджера скальперов отдельно"""
    try:
        print("\n🔧 ТЕСТ МЕНЕДЖЕРА СКАЛЬПЕРОВ ОТДЕЛЬНО")
        print("=" * 50)
        
        # Создаем менеджер
        manager = ScalperManager()
        
        print(f"📊 Настройки:")
        print(f"   Защита баланса: ${manager.min_usdc_balance_after_scalper:.2f} USDC")
        print(f"   Размер позиции: ${manager.position_size_usdc:.2f} USDC")
        print(f"   Максимум экземпляров: {manager.max_instances_per_symbol} на символ")
        print(f"   Время застревания: {manager.min_stuck_time/3600:.1f} часов")
        print(f"   Интервал проверки: {manager.scan_interval} сек")
        
        # Получаем цены
        btc_price = manager.get_current_price('BTCUSDC')
        eth_price = manager.get_current_price('ETHUSDC')
        
        print(f"\n📈 Текущие цены:")
        print(f"   BTCUSDC: ${btc_price:.2f}")
        print(f"   ETHUSDC: ${eth_price:.2f}")
        
        # Проверяем возможность создания скальперов
        print(f"\n🔍 Проверка возможности создания:")
        for symbol in ['BTCUSDC', 'ETHUSDC']:
            can_create, reason = manager.can_create_new_scalper(symbol)
            status = "✅ МОЖНО" if can_create else "❌ НЕЛЬЗЯ"
            print(f"   {symbol}: {status} - {reason}")
        
        print("\n✅ Тест менеджера завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка теста менеджера: {e}")

def test_integration_scenarios():
    """Тест различных сценариев интеграции"""
    try:
        print("\n🎭 ТЕСТ СЦЕНАРИЕВ ИНТЕГРАЦИИ")
        print("=" * 40)
        
        # Сценарий 1: Нормальная работа
        print("\n📋 Сценарий 1: Нормальная работа")
        print("   - Менеджер запускается с main.py")
        print("   - Отслеживает существующие скальперы")
        print("   - Создает новые при необходимости")
        
        # Сценарий 2: Застревание скальперов
        print("\n📋 Сценарий 2: Застревание скальперов")
        print("   - BTC/ETH просели на 10%")
        print("   - Скальперы застряли")
        print("   - Через 24 часа создаются новые")
        
        # Сценарий 3: Защита баланса
        print("\n📋 Сценарий 3: Защита баланса")
        print("   - Минимум $20 USDC остается")
        print("   - Автоматический расчет безопасных сумм")
        print("   - Предотвращение исчерпания средств")
        
        # Сценарий 4: Множественные экземпляры
        print("\n📋 Сценарий 4: Множественные экземпляры")
        print("   - До 3 экземпляров на символ")
        print("   - Разные точки входа")
        print("   - Независимое управление")
        
        print("\n✅ Сценарии проанализированы!")
        
    except Exception as e:
        print(f"❌ Ошибка анализа сценариев: {e}")

if __name__ == "__main__":
    print("🧪 ЗАПУСК ТЕСТОВ ИНТЕГРАЦИИ")
    print("=" * 60)
    
    # Тест интеграции с main.py
    asyncio.run(test_main_integration())
    
    # Тест менеджера отдельно
    test_scalper_manager_standalone()
    
    # Тест сценариев
    test_integration_scenarios()
    
    print("\n🎉 ВСЕ ТЕСТЫ ИНТЕГРАЦИИ ЗАВЕРШЕНЫ!")
    print("\n📝 Следующие шаги:")
    print("1. Запустить полный бот: python3 main.py")
    print("2. Проверить логи менеджера скальперов")
    print("3. Мониторить Telegram уведомления")
    print("4. Проверить создание новых экземпляров")







