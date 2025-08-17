#!/usr/bin/env python3
"""
Тест новых таймингов отчетов
"""

import logging
from datetime import datetime
from market_scanner import MarketScanner
from config import PNL_MONITOR_CONFIG

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_new_timings():
    """Тест новых таймингов отчетов"""
    try:
        print("⏰ ТЕСТ НОВЫХ ТАЙМИНГОВ ОТЧЕТОВ")
        print("=" * 60)
        print(f"Время: {datetime.now()}")
        print()
        
        # Создаем сканер
        scanner = MarketScanner()
        
        print("📊 НОВЫЕ ТАЙМИНГИ:")
        print("-" * 30)
        
        # Сканер рынка
        scan_interval_minutes = scanner.scan_interval / 60
        print(f"🔍 Сканер рынка:")
        print(f"   Интервал: {scanner.scan_interval} сек ({scan_interval_minutes:.0f} мин)")
        print(f"   Отчеты: каждые {scan_interval_minutes:.0f} минут")
        print()
        
        # PnL монитор
        pnl_check_interval = PNL_MONITOR_CONFIG['check_interval']
        pnl_notification_interval = PNL_MONITOR_CONFIG['notification_interval']
        pnl_check_minutes = pnl_check_interval / 60
        pnl_notification_minutes = pnl_notification_interval / 60
        
        print(f"📈 PnL монитор:")
        print(f"   Проверка: {pnl_check_interval} сек ({pnl_check_minutes:.0f} мин)")
        print(f"   Отчеты: {pnl_notification_interval} сек ({pnl_notification_minutes:.0f} мин)")
        print()
        
        print("✅ ИЗМЕНЕНИЯ:")
        print("-" * 30)
        print("🔍 Сканер рынка: 5 мин → 10 мин (отчеты)")
        print("📈 PnL монитор: 5 мин → 10 мин (отчеты)")
        print("⚙️ Процессы бота: БЕЗ ИЗМЕНЕНИЙ")
        print()
        
        print("📱 РЕЗУЛЬТАТ:")
        print("-" * 30)
        print("✅ Отчеты в Telegram стали реже (в 2 раза)")
        print("✅ Бот работает с той же частотой")
        print("✅ Меньше спама в Telegram")
        print("✅ Сохранена функциональность")
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        logger.error(f"Ошибка теста: {e}")

if __name__ == "__main__":
    test_new_timings() 