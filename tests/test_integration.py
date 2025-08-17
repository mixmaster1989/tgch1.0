#!/usr/bin/env python3
"""
Тест интеграции всех компонентов бота
"""

import logging
import sys
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """Тест импорта всех модулей"""
    try:
        logger.info("🔍 Тестирование импортов...")
        
        # Тест основных модулей
        from mex_api import MexAPI
        logger.info("✅ MexAPI импортирован")
        
        from balance_monitor import BalanceMonitor
        logger.info("✅ BalanceMonitor импортирован")
        
        from pnl_monitor import PnLMonitor
        logger.info("✅ PnLMonitor импортирован")
        
        from native_trader_bot import NativeTraderBot
        logger.info("✅ NativeTraderBot импортирован")
        
        from config import PNL_MONITOR_CONFIG
        logger.info("✅ Конфигурация PnL импортирована")
        
        from auto_purchase_config import get_config
        logger.info("✅ Конфигурация автопокупок импортирована")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка импорта: {e}")
        return False

def test_api_connection():
    """Тест подключения к API"""
    try:
        logger.info("🔍 Тестирование подключения к API...")
        
        from mex_api import MexAPI
        api = MexAPI()
        
        # Тест получения балансов
        account_info = api.get_account_info()
        if 'balances' in account_info:
            logger.info(f"✅ API подключение успешно, найдено {len(account_info['balances'])} балансов")
            return True
        else:
            logger.error("❌ Не удалось получить балансы")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к API: {e}")
        return False

def test_pnl_monitor():
    """Тест PnL монитора"""
    try:
        logger.info("🔍 Тестирование PnL монитора...")
        
        from pnl_monitor import PnLMonitor
        monitor = PnLMonitor()
        
        # Тест получения статуса
        status = monitor.get_current_status()
        logger.info(f"✅ PnL монитор работает, общий PnL: ${status['total_pnl']:.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка PnL монитора: {e}")
        return False

def test_balance_monitor():
    """Тест монитора баланса"""
    try:
        logger.info("🔍 Тестирование монитора баланса...")
        
        from balance_monitor import BalanceMonitor
        monitor = BalanceMonitor()
        
        # Тест получения баланса USDT
        usdt_balance = monitor.get_usdt_balance()
        logger.info(f"✅ Монитор баланса работает, USDT: ${usdt_balance:.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка монитора баланса: {e}")
        return False

def test_configurations():
    """Тест конфигураций"""
    try:
        logger.info("🔍 Тестирование конфигураций...")
        
        from config import PNL_MONITOR_CONFIG
        from auto_purchase_config import get_config
        
        # Тест PnL конфигурации
        logger.info(f"✅ PnL порог: ${PNL_MONITOR_CONFIG['profit_threshold']}")
        logger.info(f"✅ PnL интервал: {PNL_MONITOR_CONFIG['check_interval']} сек")
        
        # Тест автопокупок конфигурации
        auto_config = get_config()
        balance_config = auto_config['balance_monitor']
        logger.info(f"✅ Автопокупки порог: ${balance_config['min_balance_threshold']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Ошибка конфигураций: {e}")
        return False

def main():
    """Главная функция тестирования"""
    logger.info("🚀 ТЕСТ ИНТЕГРАЦИИ MEXCAITRADE")
    logger.info("=" * 60)
    logger.info(f"Время тестирования: {datetime.now()}")
    
    tests = [
        ("Импорты модулей", test_imports),
        ("Подключение к API", test_api_connection),
        ("PnL монитор", test_pnl_monitor),
        ("Монитор баланса", test_balance_monitor),
        ("Конфигурации", test_configurations),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 {test_name}...")
        if test_func():
            passed += 1
            logger.info(f"✅ {test_name} - ПРОЙДЕН")
        else:
            logger.error(f"❌ {test_name} - ПРОВАЛЕН")
    
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    logger.info(f"✅ Пройдено: {passed}/{total}")
    logger.info(f"❌ Провалено: {total - passed}/{total}")
    
    if passed == total:
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к запуску.")
        logger.info("🚀 Запустите: python3 main.py")
        return True
    else:
        logger.error("⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ! Проверьте настройки.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 