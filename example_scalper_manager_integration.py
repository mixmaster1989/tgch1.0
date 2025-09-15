#!/usr/bin/env python3
"""
Пример интеграции менеджера скальперов в main.py
"""

import asyncio
import logging
import threading
from scalper_manager import ScalperManager, get_scalper_protected_balance

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_scalper_manager():
    """Запуск менеджера скальперов в отдельном потоке"""
    try:
        logger.info("🚀 Запуск менеджера скальперов...")
        
        # Создаем менеджер
        manager = ScalperManager()
        
        # Отправляем информацию о настройках
        logger.info("📊 Настройки менеджера скальперов:")
        logger.info(f"   Защита баланса: ${manager.min_usdc_balance_after_scalper:.2f} USDC")
        logger.info(f"   Размер позиции: ${manager.position_size_usdc:.2f} USDC")
        logger.info(f"   Максимум экземпляров: {manager.max_instances_per_symbol} на символ")
        logger.info(f"   Интервал проверки: {manager.scan_interval} сек")
        
        # Запускаем менеджер в отдельном потоке
        def run_manager():
            asyncio.run(manager.run())
        
        manager_thread = threading.Thread(target=run_manager, daemon=True)
        manager_thread.start()
        
        logger.info("✅ Менеджер скальперов запущен в отдельном потоке")
        
        return manager
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска менеджера скальперов: {e}")
        return None

def get_scalper_status():
    """Получить статус менеджера скальперов"""
    try:
        manager = ScalperManager()
        status = manager.get_manager_status()
        
        logger.info("📊 Статус менеджера скальперов:")
        logger.info(f"   BTC активных: {status.get('btc_active', 0)}")
        logger.info(f"   BTC застрявших: {status.get('btc_stuck', 0)}")
        logger.info(f"   ETH активных: {status.get('eth_active', 0)}")
        logger.info(f"   ETH застрявших: {status.get('eth_stuck', 0)}")
        logger.info(f"   Всего создано: {status.get('total_created', 0)}")
        logger.info(f"   Общая прибыль: ${status.get('total_profit', 0):.3f}")
        logger.info(f"   Баланс USDC: ${status.get('usdc_balance', 0):.2f}")
        
        return status
        
    except Exception as e:
        logger.error(f"❌ Ошибка получения статуса: {e}")
        return {}

def check_scalper_balance():
    """Проверить защищенный баланс для скальперов"""
    try:
        protected_balance = get_scalper_protected_balance()
        
        logger.info("🛡️ Защищенный баланс для скальперов:")
        logger.info(f"   Доступно: ${protected_balance:.2f} USDC")
        
        # Рассчитываем максимальное количество позиций
        manager = ScalperManager()
        max_positions = int(protected_balance / manager.position_size_usdc)
        logger.info(f"   Максимум позиций: {max_positions}")
        
        return protected_balance, max_positions
        
    except Exception as e:
        logger.error(f"❌ Ошибка проверки баланса: {e}")
        return 0.0, 0

# Пример интеграции в main.py
def integrate_with_main():
    """Пример интеграции менеджера скальперов в main.py"""
    
    print("🔧 ИНТЕГРАЦИЯ МЕНЕДЖЕРА СКАЛЬПЕРОВ В MAIN.PY")
    print("=" * 60)
    
    # 1. Запуск менеджера скальперов
    print("\n1️⃣ Запуск менеджера скальперов...")
    manager = start_scalper_manager()
    
    if manager:
        print("✅ Менеджер запущен успешно")
    else:
        print("❌ Ошибка запуска менеджера")
        return
    
    # 2. Проверка баланса
    print("\n2️⃣ Проверка защищенного баланса...")
    protected_balance, max_positions = check_scalper_balance()
    
    # 3. Получение статуса
    print("\n3️⃣ Получение статуса менеджера...")
    status = get_scalper_status()
    
    # 4. Интеграция с существующими модулями
    print("\n4️⃣ Интеграция с существующими модулями...")
    
    # Пример модификации balance_monitor.py
    print("   📝 Модификация balance_monitor.py:")
    print("   - Увеличить защиту баланса до $20 USDC")
    print("   - Добавить проверку менеджера скальперов")
    
    # Пример модификации btc_scalper.py и eth_scalper.py
    print("   📝 Модификация скальперов:")
    print("   - Добавить интеграцию с менеджером")
    print("   - Передавать статусы в менеджер")
    
    print("\n✅ Интеграция завершена!")

# Пример использования в main.py
def example_main_integration():
    """Пример как это будет выглядеть в main.py"""
    
    print("\n📋 ПРИМЕР ИНТЕГРАЦИИ В MAIN.PY")
    print("=" * 40)
    
    print("""
# В main.py добавить:

from scalper_manager import ScalperManager, get_scalper_protected_balance

def start_scalper_manager():
    \"\"\"Запуск менеджера скальперов в отдельном потоке\"\"\"
    try:
        logger.info("🚀 Запуск менеджера скальперов...")
        
        manager = ScalperManager()
        
        def run_manager():
            asyncio.run(manager.run())
        
        manager_thread = threading.Thread(target=run_manager, daemon=True)
        manager_thread.start()
        
        logger.info("✅ Менеджер скальперов запущен")
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска менеджера: {e}")

# В функции main() добавить:
def main():
    # ... существующий код ...
    
    # Запускаем менеджер скальперов
    start_scalper_manager()
    
    # ... остальной код ...
""")

if __name__ == "__main__":
    # Демонстрация интеграции
    integrate_with_main()
    
    # Пример кода для main.py
    example_main_integration()
    
    print("\n🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА!")
    print("\n📝 Следующие шаги:")
    print("1. Протестировать менеджер: python3 test_scalper_manager.py")
    print("2. Интегрировать в main.py")
    print("3. Модифицировать существующие скальперы")
    print("4. Обновить защиту баланса в других модулях")







