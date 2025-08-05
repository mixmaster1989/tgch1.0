#!/usr/bin/env python3
"""
MEX Trading Bot - Главный файл запуска
Торговля на спотовом рынке MEX с использованием ИИ анализа
"""

import asyncio
import logging
from native_trader_bot import NativeTraderBot
from startup_dashboard import StartupDashboard

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Главная функция запуска"""
    try:
        logger.info("Запуск MEX Trading Bot...")
        
        # Отправляем стартовую плашку
        dashboard = StartupDashboard()
        dashboard.send_startup_notification()
        
        # Запускаем нативного Трейдера
        trader = NativeTraderBot()
        trader.run()
        
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    main()