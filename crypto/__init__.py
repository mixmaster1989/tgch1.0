import logging
import sys
import traceback

# Настройка подробного логирования для модуля crypto
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Добавляем обработчик для вывода в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Функция для логирования с трассировкой стека
def log_exception(e, message="Произошла ошибка"):
    logger.error(f"{message}: {str(e)}")
    logger.error(traceback.format_exc())

try:
    logger.debug("Инициализация модуля crypto")
    from .telegram_interface import register_crypto_handlers
    from .main_menu import register_crypto_menu_handlers
    from .config import crypto_config
    from .data_sources import DataSourceManager
    from .smart_money_analyzer import SmartMoneyAnalyzer
    from .signal_dispatcher import SignalDispatcher
    
    logger.debug("Модуль crypto успешно инициализирован")
    
    __all__ = [
        'register_crypto_handlers',
        'register_crypto_menu_handlers',
        'crypto_config',
        'DataSourceManager',
        'SmartMoneyAnalyzer',
        'SignalDispatcher'
    ]
except Exception as e:
    log_exception(e, "Ошибка при инициализации модуля crypto")