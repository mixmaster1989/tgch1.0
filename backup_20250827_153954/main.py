#!/usr/bin/env python3
"""
MEX Trading Bot - Главный файл запуска
Торговля на спотовом рынке MEX с использованием ИИ анализа
"""

import asyncio
import logging
from logging.handlers import RotatingFileHandler
import threading
from native_trader_bot import NativeTraderBot
from startup_dashboard import StartupDashboard
from balance_monitor import BalanceMonitor
from pnl_monitor import PnLMonitor
from auto_purchase_config import get_config
from config import PNL_MONITOR_CONFIG
from alt_monitor import AltsMonitor
# from stablecoin_balancer import StablecoinBalancer
from market_scanner import MarketScanner
from orders_reporter import OrdersReporter
from active_50_50_balancer import Active5050Balancer
from btc_scalper import BTCScalper
from eth_scalper import ETHScalper
from scalpers_reporter import ScalpersReporter
from scalper_manager import ScalperManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler('bot.log', maxBytes=20 * 1024 * 1024, backupCount=5, encoding='utf-8'),
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

def start_scalper_manager():
    """Запуск менеджера скальперов в отдельном потоке"""
    try:
        logger.info("🚀 Запуск менеджера скальперов...")
        
        # Создаем менеджер скальперов
        scalper_manager = ScalperManager()
        
        # Отправляем информацию о настройках
        logger.info("📊 Настройки менеджера скальперов:")
        logger.info(f"   Защита баланса: ${scalper_manager.min_usdc_balance_after_scalper:.2f} USDC")
        logger.info(f"   Размер позиции: ${scalper_manager.position_size_usdc:.2f} USDC")
        logger.info(f"   Максимум экземпляров: {scalper_manager.max_instances_per_symbol} на символ")
        logger.info(f"   Минимальное время застревания: {scalper_manager.min_stuck_time/3600:.1f} часов")
        logger.info(f"   Интервал проверки: {scalper_manager.scan_interval} сек")
        
        # Запускаем менеджер в отдельном потоке
        def run_scalper_manager():
            asyncio.run(scalper_manager.run())
        
        manager_thread = threading.Thread(target=run_scalper_manager, daemon=True)
        manager_thread.start()
        
        logger.info("✅ Менеджер скальперов запущен в отдельном потоке")
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска менеджера скальперов: {e}")

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
        
        # Запускаем репортер ордеров (каждые 10 минут)
        try:
            logger.info("🚀 Запуск репортера ордеров...")
            orders_reporter = OrdersReporter()
            def run_orders_reporter():
                orders_reporter.start()
            t = threading.Thread(target=run_orders_reporter, daemon=True)
            t.start()
            logger.info("✅ Репортер ордеров запущен в отдельном потоке")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска репортера ордеров: {e}")

        # Запускаем репортер скальперов (каждые 10 минут)
        try:
            logger.info("🚀 Запуск репортера скальперов...")
            scalpers_reporter = ScalpersReporter()
            def run_scalpers_reporter():
                scalpers_reporter.start()
            t = threading.Thread(target=run_scalpers_reporter, daemon=True)
            t.start()
            logger.info("✅ Репортер скальперов запущен в отдельном потоке")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска репортера скальперов: {e}")

        # Запускаем активный балансировщик 50/50
        try:
            logger.info("🚀 Запуск активного балансировщика 50/50...")
            active_balancer = Active5050Balancer()
            def run_active_balancer():
                asyncio.run(active_balancer.start_monitoring())
            t = threading.Thread(target=run_active_balancer, daemon=True)
            t.start()
            logger.info("✅ Активный балансировщик 50/50 запущен в отдельном потоке")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска активного балансировщика 50/50: {e}")

        # Запускаем BTC скальпер
        try:
            logger.info("🚀 Запуск BTC скальпера (BTCUSDC)...")
            btc_scalper = BTCScalper()
            def run_btc_scalper():
                asyncio.run(btc_scalper.start_scalping())
            t = threading.Thread(target=run_btc_scalper, daemon=True)
            t.start()
            logger.info("✅ BTC скальпер (BTCUSDC) запущен в отдельном потоке")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска BTC скальпера: {e}")

        # Запускаем ETH скальпер
        try:
            logger.info("🚀 Запуск ETH скальпера (ETHUSDC)...")
            eth_scalper = ETHScalper()
            def run_eth_scalper():
                asyncio.run(eth_scalper.start_scalping())
            t = threading.Thread(target=run_eth_scalper, daemon=True)
            t.start()
            logger.info("✅ ETH скальпер (ETHUSDC) запущен в отдельном потоке")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска ETH скальпера: {e}")

        # Запускаем менеджер скальперов
        start_scalper_manager()

        # (Отключено) Запуск балансировщика стейблкоинов
        # try:
        #     logger.info("🚀 Запуск балансировщика USDT/USDC...")
        #     stablecoin_balancer = StablecoinBalancer()
        #     def run_stablecoin_balancer():
        #         stablecoin_balancer.start_monitoring()
        #     t = threading.Thread(target=run_stablecoin_balancer, daemon=True)
        #     t.start()
        #     logger.info("✅ Балансировщик стейблов запущен в отдельном потоке")
        # except Exception as e:
        #     logger.error(f"❌ Ошибка запуска балансировщика стейблов: {e}")

        logger.info("✅ Все компоненты запущены:")
        logger.info("   🔍 Сканер рынка с автопокупками")
        logger.info("   📈 Автоматические покупки BTC/ETH")
        logger.info("   📊 PnL мониторинг с автопродажей")
        logger.info("   🧩 Мониторинг альтов (порог $0.15)")
        logger.info("   ⚖️ Активный балансировщик 50/50 (каждые 10 сек)")
        logger.info("   ⚡ BTC скальпер BTCUSDC (каждые 5 сек, рыночные ордера)")
        logger.info("   ⚡ ETH скальпер ETHUSDC (каждые 5 сек, лимитные ордера)")
        logger.info("   🎯 Менеджер скальперов (каждые 30 сек, защита $20 USDC)")
        logger.info("   📊 Репортер скальперов (каждые 10 мин, ≤$5 позиции)")
        # logger.info("   ⚖️ Балансировщик USDT/USDC (каждый час)")
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