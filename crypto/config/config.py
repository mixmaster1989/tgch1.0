"""
Модуль для работы с конфигурацией
"""

# Импортируем модули
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional  # Добавлен импорт Optional
from datetime import timedelta  # Добавлен для использования в конфигурации

# Получаем логгер для модуля
logger = logging.getLogger('crypto.config')

# Импортируем менеджер данных
try:
    from ..data_sources.crypto_data_manager import CryptoDataManager, get_data_manager
    logger.info("Импортирован CryptoDataManager для использования в конфигурации")
except Exception as e:
    logger.error(f"Ошибка при импорте CryptoDataManager: {e}")
    CryptoDataManager = None

# Путь к файлу конфигурации
CONFIG_PATH = Path(__file__).parent / "config.yaml"

# Кэш конфигурации
_config_cache = None

logger.info(f"Попытка загрузки конфигурации из: {CONFIG_PATH}")


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
                    "cryptorank": [
                        {
                            "key": "016d6a16d3bd018fa02c0ddff345d4c5899584e80923c973a282ca4955a3",  # Первый API-ключ
                            "rate_limit": {
                                "requests_per_minute": 30,
                                "credits_per_day": 1000
                            }
                        },
                        {
                            "key": "kb77lvszgqgtxcxs_oikpmfenof6phtzn",  # Второй API-ключ
                            "rate_limit": {
                                "requests_per_minute": 30,
                                "credits_per_day": 1000
                            }
                        }
                    ],
                    # Добавляем секцию для Santiment API
                    "santiment": {
                        "key": "kb77lvszgqgtxcxs_oikpmfenof6phtzn"  # Ваш API-ключ для Santiment API
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
                },
                "caching": {
                    "coins_ttl": 3600,  # Кэшируем список монет на 1 час
                    "coin_details_ttl": 1800,  # Кэшируем детали монет на 30 минут
                    "markets_ttl": 7200,  # Кэшируем данные о рынках на 2 часа
                    "exchanges_ttl": 7200  # Кэшируем данные о биржах на 2 часа
                },
                "background": {
                    "update_interval": 3600,  # Интервал фонового обновления (в секундах)
                    "retry_interval": 300  # Интервал повторных попыток при ошибках (в секундах)
                }
            }
            
            # Сохраняем конфигурацию по умолчанию
            with open(CONFIG_PATH, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            
            logger.info(f"Создана конфигурация по умолчанию: {CONFIG_PATH}")
            _config_cache = default_config
            return default_config
    except Exception as e:
        logger.error(f"Ошибка при создании конфигурации: {e}")
        
        # Возвращаем конфигурацию по умолчанию без сохранения в файл
        _config_cache = default_config
        logger.warning("Используется временная конфигурация без сохранения в файл")
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

def get_santiment_api_key() -> str:
    """
    Получает API ключ для Santiment
    
    Returns:
        str: API ключ
    """
    # Пытаемся получить ключ из основного файла конфигурации
    config = get_config()
    
    if config and 'api' in config and 'santiment' in config['api'] and 'key' in config['api']['santiment']:
        logger.info("API ключ для Santiment получен из файла конфигурации")
        return config['api']['santiment']['key']
    
    # Если не удалось получить из файла, пытаемся из переменных окружения
    api_key = os.getenv("SANTIMENT_API_KEY")
    
    if not api_key:
        logger.warning("API ключ для Santiment не найден ни в файле конфигурации, ни в переменных окружения")
        return ""
    
    logger.info("API ключ для Santiment получен из переменных окружения")
    return api_key

# Создаем глобальный экземпляр менеджера данных
_data_manager = None

def get_data_manager() -> Optional[CryptoDataManager]:
    """
    Получает глобальный экземпляр менеджера данных
    
    Returns:
        Optional[CryptoDataManager]: Глобальный экземпляр менеджера данных или None
    """
    global _data_manager
    
    if _data_manager is None:
        try:
            # Получаем конфигурацию
            from .config import get_config, get_santiment_api_key
            config = get_config()
            
            # Получаем API-ключи Cryptorank
            cryptorank_keys = []
            if config and "api" in config and "cryptorank" in config["api"]:
                if isinstance(config["api"]["cryptorank"], list):
                    for key_info in config["api"]["cryptorank"]:
                        if isinstance(key_info, dict) and "key" in key_info:
                            cryptorank_keys.append(key_info["key"])
                        elif isinstance(key_info, str):
                            cryptorank_keys.append(key_info)
                elif "key" in config["api"]["cryptorank"]:
                    cryptorank_keys.append(config["api"]["cryptorank"]["key"])
                else:
                    # Старый формат конфигурации с одним ключом
                    cryptorank_keys.append(config["api"]["cryptorank"])
            
            # Если нет ключей в конфигурации, пытаемся получить из переменной окружения
            if not cryptorank_keys:
                env_key = os.getenv("CRYPTORANK_API_KEY")
                if env_key:
                    cryptorank_keys.append(env_key)
                    logger.info("Используется API-ключ из переменной окружения")
            
            # Если все еще нет ключей, используем ключ по умолчанию
            if not cryptorank_keys:
                cryptorank_keys.append("default_api_key")
                logger.warning("Используется ключ по умолчанию для Cryptorank API")
            
            # Получаем API-ключ Santiment
            santiment_api_key = get_santiment_api_key()
            
            # Инициализируем менеджер данных с API-ключами
            _data_manager = CryptoDataManager(santiment_api_key=santiment_api_key)
            
            # Устанавливаем дополнительные параметры
            if config and "background" in config:
                if "update_interval" in config["background"]:
                    update_interval = config["background"]["update_interval"]
                    # Обновляем интервал фонового обновления в секундах
                    _data_manager.min_update_interval = timedelta(seconds=update_interval)
                    logger.info(f"Установлен интервал фонового обновления: {update_interval} секунд")
        except Exception as e:
            logger.error(f"Ошибка при получении конфигурации: {e}")
            
    return _data_manager
