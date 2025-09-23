#!/usr/bin/env python3
"""
Запуск демонстрации мощи проекта MEXCAITRADE
"""

import logging
import asyncio
from datetime import datetime
from demo_power_script import PowerDemoScript

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('demo.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Главная функция запуска демонстрации"""
    try:
        logger.info("=== ЗАПУСК ДЕМОНСТРАЦИИ МОЩИ MEXCAITRADE ===")
        logger.info(f"Время запуска: {datetime.now()}")
        
        # Создаем и запускаем демонстрацию
        demo = PowerDemoScript()
        await demo.run_demo()
        
        logger.info("✅ Демонстрация успешно завершена!")
        
    except KeyboardInterrupt:
        logger.info("Демонстрация остановлена пользователем")
    except Exception as e:
        logger.error(f"Ошибка демонстрации: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main()) 