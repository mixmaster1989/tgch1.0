#!/usr/bin/env python3
"""
Запуск нативного Трейдера
"""

import logging
from datetime import datetime
from native_trader_bot import NativeTraderBot
from startup_dashboard import StartupDashboard

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trader.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("=== ЗАПУСК НАТИВНОГО ТРЕЙДЕРА ===")
        logger.info(f"Время запуска: {datetime.now()}")
        
        # Отправляем стартовую плашку
        logger.info("Отправка стартовой плашки...")
        dashboard = StartupDashboard()
        dashboard.send_startup_notification()
        
        # Запускаем Трейдера
        logger.info("Трейдер заходит в группу...")
        trader = NativeTraderBot()
        
        logger.info("🔥 Трейдер готов материться и помогать!")
        trader.run()
        
    except KeyboardInterrupt:
        logger.info("Трейдер ушел из группы")
    except Exception as e:
        logger.error(f"Трейдер упал: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()