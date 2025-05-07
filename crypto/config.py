import os
import yaml
import logging
import sys
import traceback

# Настройка подробного логирования
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

def load_crypto_config():
    """
    Загружает конфигурацию для криптовалютного модуля
    
    Returns:
        dict: Конфигурация криптовалютного модуля
    """
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'crypto_config.yaml')
    
    # Проверяем существование файла конфигурации
    if not os.path.exists(config_path):
        # Создаем файл с дефолтными настройками
        default_config = {
            'api_keys': {
                'tradingview': '',
                'cryptorank': '',
                'whale_alert': '',
                'binance': '',
            },
            'monitoring': {
                'pairs': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT'],
                'timeframes': ['1h', '4h', '1d'],
                'volume_threshold': 1000000,  # Объем в USD для отслеживания
                'whale_threshold': 500000,    # Размер транзакции для отслеживания китов
            },
            'signals': {
                'enabled': True,
                'channel_id': None,  # ID канала для отправки сигналов
                'include_charts': True,
                'notification_cooldown': 3600,  # Время между уведомлениями в секундах
            },
            'smart_money': {
                'oi_change_threshold': 5,     # % изменения Open Interest
                'funding_rate_threshold': 0.1, # % Funding Rate для сигнала
                'liquidity_zones': True,       # Отслеживать зоны ликвидности
                'order_blocks': True,          # Отслеживать блоки ордеров
            }
        }
        
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Записываем дефолтную конфигурацию
        with open(config_path, 'w', encoding='utf-8') as file:
            yaml.dump(default_config, file, default_flow_style=False)
        
        logger.info(f"Создан файл конфигурации криптовалютного модуля: {config_path}")
        return default_config
    
    try:
        # Загружаем конфигурацию из файла
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        logger.info(f"Загружена конфигурация криптовалютного модуля")
        return config
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации криптовалютного модуля: {e}")
        return {}

# Загружаем конфигурацию при импорте модуля
crypto_config = load_crypto_config()