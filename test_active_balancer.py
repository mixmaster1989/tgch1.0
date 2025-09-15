#!/usr/bin/env python3
"""
Тест активного балансировщика 50/50
"""

import asyncio
import logging
from active_50_50_balancer import Active5050Balancer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_balancer():
    """Тестирование балансировщика"""
    try:
        logger.info("🧪 Запуск теста активного балансировщика 50/50")
        
        # Создаем балансировщик
        balancer = Active5050Balancer()
        
        # Получаем текущие балансы
        logger.info("📊 Получение балансов стейблкоинов...")
        stablecoins = balancer.get_stablecoin_balances()
        logger.info(f"💵 USDT: ${stablecoins['USDT']:.2f}")
        logger.info(f"💵 USDC: ${stablecoins['USDC']:.2f}")
        
        # Получаем стоимость портфеля
        logger.info("📈 Расчет стоимости портфеля...")
        portfolio = balancer.get_portfolio_values()
        logger.info(f"🧩 Альты: ${portfolio['alts_value']:.2f}")
        logger.info(f"🟡 BTC/ETH: ${portfolio['btceth_value']:.2f}")
        logger.info(f"💰 Общая стоимость: ${portfolio['total_value']:.2f}")
        
        if portfolio['total_value'] > 0:
            alts_ratio = portfolio['alts_value'] / portfolio['total_value']
            btceth_ratio = portfolio['btceth_value_usdt'] / portfolio['total_value']
            logger.info(f"📊 Пропорции: Альты {alts_ratio*100:.1f}% | BTC/ETH {btceth_ratio*100:.1f}%")
        
        # Рассчитываем необходимую балансировку
        logger.info("⚖️ Расчет необходимой балансировки...")
        balance_plan = balancer.calculate_balance_needed()
        
        if balance_plan:
            logger.info(f"🎯 План балансировки:")
            logger.info(f"   Действие: {balance_plan['action']}")
            logger.info(f"   Сумма: ${balance_plan['amount']:.2f}")
            logger.info(f"   Причина: {balance_plan['reason']}")
            
            # Спрашиваем пользователя
            response = input("\n❓ Выполнить балансировку? (y/n): ")
            if response.lower() == 'y':
                logger.info("🚀 Выполнение балансировки...")
                result = balancer.execute_conversion(balance_plan['action'], balance_plan['amount'])
                
                if result['success']:
                    logger.info("✅ Балансировка выполнена успешно!")
                    logger.info(f"   Ордер ID: {result['order_id']}")
                    logger.info(f"   Цена: {result['price']:.6f}")
                else:
                    logger.error(f"❌ Ошибка балансировки: {result['error']}")
            else:
                logger.info("⏸️ Балансировка отменена пользователем")
        else:
            logger.info("✅ Балансировка не требуется")
        
        # Показываем статус
        status = balancer.get_status()
        logger.info(f"\n📊 Статус балансировщика:")
        logger.info(f"   Работает: {status['is_running']}")
        logger.info(f"   Всего балансировок: {status['total_balances']}")
        logger.info(f"   Всего конвертировано: ${status['total_converted']:.2f}")
        logger.info(f"   Интервал сканирования: {status['scan_interval']} сек")
        logger.info(f"   Минимальный баланс: ${status['min_balance_threshold']}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка тестирования: {e}")

if __name__ == "__main__":
    asyncio.run(test_balancer())

