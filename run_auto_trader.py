#!/usr/bin/env python3
"""
Запуск автоматического торгового бота
"""

import asyncio
import logging
from datetime import datetime

from auto_trader import AutoTrader

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Главная функция"""
    logger.info("🚀 ЗАПУСК АВТОМАТИЧЕСКОГО ТОРГОВОГО БОТА")
    logger.info("=" * 60)
    logger.info(f"Время запуска: {datetime.now()}")
    
    trader = AutoTrader()
    
    try:
        # Запускаем бота
        await trader.start()
        
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки (Ctrl+C)")
        await trader.stop()
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        await trader.stop()
        
    finally:
        logger.info("✅ Бот завершен")

if __name__ == "__main__":
    asyncio.run(main()) 