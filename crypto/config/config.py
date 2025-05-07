"""
Модуль для работы с конфигурацией криптомодуля
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional

# Получаем логгер для модуля
logger = logging.getLogger('crypto.config')

# Путь к файлу конфигурации по умолчанию
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'smart_money_config.yaml')

# Глобальная переменная для хранения конфигурации
_config = None

def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """
    Загружает конфигурацию из YAML-файла
    
    Args:
        config_path: Путь к файлу конфигурации
        
    Returns:
        Dict[str, Any]: Словарь с конфигурацией
    """
    global _config
    
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            _config = yaml.safe_load(file)
            logger.info(f"Конфигурация успешно загружена из {config_path}")
            return _config
    except FileNotFoundError:
        logger.warning(f"Файл конфигурации {config_path} не найден. Создаем конфигурацию по умолчанию.")
        _config = create_default_config(config_path)
        return _config
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации: {e}", exc_info=True)
        _config = create_default_config(config_path)
        return _config

def create_default_config(config_path: str) -> Dict[str, Any]:
    """
    Создает конфигурацию по умолчанию и сохраняет ее в файл
    
    Args:
        config_path: Путь для сохранения файла конфигурации
        
    Returns:
        Dict[str, Any]: Словарь с конфигурацией по умолчанию
    """
    default_config = {
        'api': {
            'cryptorank': {
                'api_key': 'a3b7d93f96fe3e3ea8cf6e7fbaec68f77fa730e8a2b3af6151d30e25a629',
                'base_url': 'https://api.cryptorank.io/v1',
                'rate_limit': {
                    'requests_per_minute': 30,
                    'retry_after': 60
                }
            }
        },
        'analytics': {
            'volume_spike': {
                'threshold': 2.5,
                'ma_period': 24  # часов
            },
            'large_orders': {
                'min_order_size_btc': 10.0,
                'imbalance_threshold': 1.5
            },
            'funding_rate': {
                'alert_threshold': 0.05,  # 5%
                'check_interval': 5  # минут
            }
        },
        'notification': {
            'max_signals_per_hour': 10,
            'cooldown_per_pair': 300,  # 5 минут
            'whitelist_pairs': [
                'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 
                'SOL/USDT', 'XRP/USDT', 'ADA/USDT',
                'AVAX/USDT', 'DOT/USDT', 'MATIC/USDT'
            ]
        },
        'cache': {
            'ttl': {
                'market_data': 300,  # 5 минут
                'coin_info': 3600,   # 1 час
                'signals': 86400     # 24 часа
            }
        }
    }
    
    try:
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        # Сохраняем конфигурацию в файл
        with open(config_path, 'w', encoding='utf-8') as file:
            yaml.dump(default_config, file, default_flow_style=False, allow_unicode=True)
            logger.info(f"Создана конфигурация по умолчанию и сохранена в {config_path}")
    except Exception as e:
        logger.error(f"Ошибка при создании конфигурации по умолчанию: {e}", exc_info=True)
    
    return default_config

def get_config() -> Dict[str, Any]:
    """
    Возвращает текущую конфигурацию
    
    Returns:
        Dict[str, Any]: Словарь с конфигурацией
    """
    global _config
    
    if _config is None:
        _config = load_config()
    
    return _config

def get_cryptorank_api_key() -> str:
    """
    Возвращает API ключ для Cryptorank
    
    Returns:
        str: API ключ
    """
    config = get_config()
    return config['api']['cryptorank']['api_key']

def get_whitelist_pairs() -> list:
    """
    Возвращает список разрешенных торговых пар
    
    Returns:
        list: Список разрешенных пар
    """
    config = get_config()
    return config['notification']['whitelist_pairs']