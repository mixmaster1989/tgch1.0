#!/usr/bin/env python3
"""
Запуск автоматических покупок BTC/ETH
"""

import asyncio
import logging
import sys
from datetime import datetime
from balance_monitor import BalanceMonitor
from auto_purchase_config import get_config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_purchase.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Главная функция запуска"""
    try:
        # Получаем конфигурацию
        config = get_config()
        
        logger.info("🚀 ЗАПУСК АВТОМАТИЧЕСКИХ ПОКУПОК BTC/ETH")
        logger.info("=" * 60)
        logger.info(f"Время запуска: {datetime.now()}")
        
        # Выводим настройки
        balance_config = config['balance_monitor']
        allocation_config = config['allocation']
        
        logger.info("📊 НАСТРОЙКИ:")
        logger.info(f"   Минимальный баланс: ${balance_config['min_balance_threshold']}")
        logger.info(f"   Максимальная покупка: ${balance_config['max_purchase_amount']}")
        logger.info(f"   Интервал проверки: {balance_config['balance_check_interval']} сек")
        logger.info(f"   BTC: {allocation_config['btc_allocation']*100}%")
        logger.info(f"   ETH: {allocation_config['eth_allocation']*100}%")
        
        # Создаем монитор баланса
        monitor = BalanceMonitor()
        
        # Настраиваем параметры из конфигурации
        monitor.min_balance_threshold = balance_config['min_balance_threshold']
        monitor.max_purchase_amount = balance_config['max_purchase_amount']
        monitor.balance_check_interval = balance_config['balance_check_interval']
        monitor.min_purchase_interval = balance_config['min_purchase_interval']
        monitor.btc_allocation = allocation_config['btc_allocation']
        monitor.eth_allocation = allocation_config['eth_allocation']
        
        logger.info("✅ Монитор баланса настроен")
        
        # Запускаем мониторинг
        logger.info("🔄 Запуск мониторинга...")
        await monitor.start_monitoring()
        
    except KeyboardInterrupt:
        logger.info("🛑 Автоматические покупки остановлены пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

def test_configuration():
    """Тест конфигурации"""
    try:
        config = get_config()
        print("✅ Конфигурация загружена успешно")
        
        # Проверяем основные настройки
        balance_config = config['balance_monitor']
        allocation_config = config['allocation']
        
        print(f"📊 Настройки мониторинга:")
        print(f"   Минимальный баланс: ${balance_config['min_balance_threshold']}")
        print(f"   Максимальная покупка: ${balance_config['max_purchase_amount']}")
        print(f"   Интервал проверки: {balance_config['balance_check_interval']} сек")
        
        print(f"📈 Стратегия распределения:")
        print(f"   BTC: {allocation_config['btc_allocation']*100}%")
        print(f"   ETH: {allocation_config['eth_allocation']*100}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

def show_help():
    """Показать справку"""
    print("""
🤖 АВТОМАТИЧЕСКИЕ ПОКУПКИ BTC/ETH

Использование:
  python3 run_auto_purchase.py [команда]

Команды:
  start     - Запустить автоматические покупки
  test      - Тест конфигурации
  help      - Показать эту справку

Примеры:
  python3 run_auto_purchase.py start
  python3 run_auto_purchase.py test

Настройки в auto_purchase_config.py:
  - Минимальный баланс для покупки
  - Максимальная сумма покупки
  - Распределение между BTC/ETH
  - Интервалы проверки
  - Безопасность и уведомления
""")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            asyncio.run(main())
        elif command == "test":
            test_configuration()
        elif command == "help":
            show_help()
        else:
            print(f"❌ Неизвестная команда: {command}")
            show_help()
    else:
        # По умолчанию запускаем
        asyncio.run(main()) 