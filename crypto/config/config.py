"""
Модуль для работы с конфигурацией
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

# Получаем логгер для модуля
logger = logging.getLogger('crypto.config')

# Путь к файлу конфигурации
CONFIG_PATH = Path(__file__).parent / "config.yaml"

# Кэш конфигурации
_config_cache = None

def get_config() -> Dict[str, Any]:
    """
    Получает конфигурацию из файла
    
    Returns:
        Dict[str, Any]: Конфигурация
    """
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
    
    try:
        if not CONFIG_PATH.exists():
            # Создаем конфигурацию по умолчанию
            default_config = {
                "api": {
                    "cryptorank": {
                        "rate_limit": {
                            "requests_per_minute": 30,
                            "credits_per_day": 1000
                        }
                    }
                },
                "analytics": {
                    "volume_spike": {
                        "threshold": 2.0
                    }
                },
                "notification": {
                    "max_signals_per_hour": 10,
                    "cooldown_per_pair": 3600,  # 1 час в секундах
                    "whitelist_pairs": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"],
                    "price_change": {
                        "threshold_percent": 5.0,
                        "time_window_minutes": 60
                    },
                    "volume_spike": {
                        "threshold": 2.0
                    }
                }
            }
            
            # Сохраняем конфигурацию по умолчанию
            with open(CONFIG_PATH, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            
            logger.info(f"Создана конфигурация по умолчанию: {CONFIG_PATH}")
            _config_cache = default_config
            return default_config
        
        # Загружаем конфигурацию из файла
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info(f"Загружена конфигурация из файла: {CONFIG_PATH}")
        _config_cache = config
        return config
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации: {e}", exc_info=True)
        
        # Возвращаем конфигурацию по умолчанию в случае ошибки
        default_config = {
            "api": {
                "cryptorank": {
                    "rate_limit": {
                        "requests_per_minute": 30,
                        "credits_per_day": 1000
                    }
                }
            },
            "analytics": {
                "volume_spike": {
                    "threshold": 2.0
                }
            },
            "notification": {
                "max_signals_per_hour": 10,
                "cooldown_per_pair": 3600,  # 1 час в секундах
                "whitelist_pairs": ["BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT"],
                "price_change": {
                    "threshold_percent": 5.0,
                    "time_window_minutes": 60
                },
                "volume_spike": {
                    "threshold": 2.0
                }
            }
        }
        
        _config_cache = default_config
        return default_config

def get_cryptorank_api_key() -> str:
    """
    Получает API ключ для Cryptorank
    
    Returns:
        str: API ключ
    """
    # Пытаемся получить ключ из файла smart_money_config.yaml
    try:
        smart_money_config_path = Path(__file__).parent / "smart_money_config.yaml"
        if smart_money_config_path.exists():
            with open(smart_money_config_path, 'r') as f:
                config = yaml.safe_load(f)
                if config and 'api' in config and 'cryptorank' in config['api'] and 'api_key' in config['api']['cryptorank']:
                    logger.info("API ключ для Cryptorank получен из файла конфигурации")
                    return config['api']['cryptorank']['api_key']
    except Exception as e:
        logger.error(f"Ошибка при чтении API ключа из файла конфигурации: {e}")
    
    # Если не удалось получить из файла, пытаемся из переменных окружения
    api_key = os.getenv("CRYPTORANK_API_KEY")
    
    if not api_key:
        logger.warning("API ключ для Cryptorank не найден ни в файле конфигурации, ни в переменных окружения")
        return ""
    
    return api_key