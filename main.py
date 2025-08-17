#!/usr/bin/env python3
"""
MEX Trading Bot - Главный файл запуска
Торговля на спотовом рынке MEX с использованием ИИ анализа
"""

import asyncio
import logging
import threading
from native_trader_bot import NativeTraderBot
from startup_dashboard import StartupDashboard
from balance_monitor import BalanceMonitor
from pnl_monitor import PnLMonitor
from auto_purchase_config import get_config
from config import PNL_MONITOR_CONFIG
from alt_monitor import AltsMonitor
from stablecoin_balancer import StablecoinBalancer
from market_scanner import MarketScanner

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

def start_balance_monitor():
    """Запуск монитора баланса в отдельном потоке"""
    try:
        logger.info("🚀 Запуск монитора баланса для автоматических покупок...")
        
        # Получаем конфигурацию
        config = get_config()
        balance_config = config['balance_monitor']
        allocation_config = config['allocation']
        
        logger.info("📊 Настройки автоматических покупок:")
        logger.info(f"   Минимальный баланс: ${balance_config['min_balance_threshold']}")
        logger.info(f"   Максимальная покупка: ${balance_config['max_purchase_amount']}")
        logger.info(f"   BTC: {allocation_config['btc_allocation']*100}% | ETH: {allocation_config['eth_allocation']*100}%")
        
        # Создаем монитор баланса
        monitor = BalanceMonitor()
        
        # Настраиваем параметры из конфигурации
        monitor.min_balance_threshold = balance_config['min_balance_threshold']
        monitor.max_purchase_amount = balance_config['max_purchase_amount']
        monitor.balance_check_interval = balance_config['balance_check_interval']
        monitor.min_purchase_interval = balance_config['min_purchase_interval']
        monitor.btc_allocation = allocation_config['btc_allocation']
        monitor.eth_allocation = allocation_config['eth_allocation']
        
        # Запускаем мониторинг в отдельном потоке
        def run_monitor():
            asyncio.run(monitor.start_monitoring())
        
        monitor_thread = threading.Thread(target=run_monitor, daemon=True)
        monitor_thread.start()
        
        logger.info("✅ Монитор баланса запущен в отдельном потоке")
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска монитора баланса: {e}")

def start_pnl_monitor():
    """Запуск PnL монитора в отдельном потоке"""
    try:
        logger.info("🚀 Запуск PnL монитора для автоматической продажи...")
        
        # Создаем PnL монитор
        pnl_monitor = PnLMonitor()
        
        # Настройки уже загружены из конфигурации
        logger.info("📊 Настройки PnL монитора:")
        logger.info(f"   Порог прибыли: ${pnl_monitor.profit_threshold}")
        logger.info(f"   Интервал проверки: {pnl_monitor.check_interval} сек")
        logger.info(f"   Интервал уведомлений: {pnl_monitor.notification_interval} сек")
        logger.info(f"   Мониторинг: {', '.join(pnl_monitor.trading_pairs)}")
        logger.info(f"   Автопродажа: {'Включена' if pnl_monitor.auto_sell_enabled else 'Отключена'}")
        
        # Запускаем мониторинг в отдельном потоке
        def run_pnl_monitor():
            pnl_monitor.start_monitoring()
        
        pnl_thread = threading.Thread(target=run_pnl_monitor, daemon=True)
        pnl_thread.start()
        
        logger.info("✅ PnL монитор запущен в отдельном потоке")
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска PnL монитора: {e}")

def start_market_scanner():
    """Запуск сканера рынка в отдельном потоке"""
    try:
        logger.info("🚀 Запуск сканера рынка для автоматических покупок...")
        
        # Создаем сканер рынка
        scanner = MarketScanner()
        
        logger.info("📊 Настройки сканера рынка:")
        logger.info(f"   Интервал сканирования: {scanner.scan_interval} сек")
        logger.info(f"   Анализируем пары: {len(scanner.trading_pairs)}")
        logger.info(f"   Автоматические покупки: ВКЛЮЧЕНЫ")
        
        # Запускаем сканирование в отдельном потоке
        def run_scanner():
            asyncio.run(scanner.start_scanning())
        
        scanner_thread = threading.Thread(target=run_scanner, daemon=True)
        scanner_thread.start()
        
        logger.info("✅ Сканер рынка запущен в отдельном потоке")
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска сканера рынка: {e}")

def main():
    """Главная функция запуска"""
    try:
        logger.info("🚀 Запуск MEX Trading Bot...")
        logger.info("=" * 60)
        
        # Отправляем стартовую плашку
        dashboard = StartupDashboard()
        dashboard.send_startup_notification()
        
        # Отправляем расширенный отчет о портфеле
        logger.info("📊 Отправка расширенного отчета о портфеле...")
        dashboard.send_extended_portfolio_report()
        
        # Запускаем сканер рынка для автоматических покупок
        start_market_scanner()
        
        # Запускаем монитор баланса для автоматических покупок
        start_balance_monitor()
        
        # Запускаем PnL монитор для автоматической продажи
        start_pnl_monitor()
        
        # Запускаем монитор альтов (порог $0.15)
        try:
            logger.info("🚀 Запуск монитора альтов (порог $0.15)...")
            alts_monitor = AltsMonitor()
            def run_alts_monitor():
                alts_monitor.start()
            t = threading.Thread(target=run_alts_monitor, daemon=True)
            t.start()
            logger.info("✅ Монитор альтов запущен в отдельном потоке")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска монитора альтов: {e}")
        
        # Запускаем балансировщик стейблкоинов
        try:
            logger.info("🚀 Запуск балансировщика USDT/USDC...")
            stablecoin_balancer = StablecoinBalancer()
            def run_stablecoin_balancer():
                stablecoin_balancer.start_monitoring()
            t = threading.Thread(target=run_stablecoin_balancer, daemon=True)
            t.start()
            logger.info("✅ Балансировщик стейблов запущен в отдельном потоке")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска балансировщика стейблов: {e}")

        logger.info("✅ Все компоненты запущены:")
        logger.info("   🔍 Сканер рынка с автопокупками")
        logger.info("   📈 Автоматические покупки BTC/ETH")
        logger.info("   📊 PnL мониторинг с автопродажей")
        logger.info("   🧩 Мониторинг альтов (порог $0.15)")
        logger.info("   ⚖️ Балансировщик USDT/USDC (каждый час)")
        logger.info("   🤖 Telegram бот")
        
        # Запускаем нативного Трейдера
        trader = NativeTraderBot()
        trader.run()
        
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()