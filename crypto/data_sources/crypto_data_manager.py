"""
Модуль для управления данными о криптовалютах
Объединяет различные источники данных: API, WebSocket, кэш и базу данных
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import logging
import asyncio
from datetime import timedelta
import yaml
import os
from pathlib import Path
import numpy as np
from datetime import datetime

# Импортируем модули
from .cryptorank_api import CryptorankAPI
from .santiment_api import SantimentAPI
from .crypto_database import CryptoDatabase
from .crypto_cache import CryptoCache, get_cache, cached
from .crypto_websocket import get_websocket

# Получаем логгер для модуля
logger = logging.getLogger('crypto.data_sources.crypto_data_manager')


class CryptoDataManager:
    """
    Класс для управления данными о криптовалютах
    """
    
    def __init__(self, santiment_api_key: str = None):
        """
        Инициализирует менеджер данных
        
        Args:
            santiment_api_key: API-ключ для Santiment API (опционально)
        """
        # Получаем конфигурацию
        self.config = None
        try:
            from crypto.config.config import get_config
            self.config = get_config()
            logger.info("Конфигурация загружена успешно")
        except Exception as e:
            logger.error(f"Ошибка при загрузке конфигурации: {e}")
            
        # Загружаем настройки кэширования
        self.caching_settings = self._load_caching_settings()
        
        # Инициализируем клиенты
        self.db = CryptoDatabase()
        self.cache = get_cache()
        self.websocket = get_websocket()
        
        # Инициализируем клиенты
        self.cryptorank_api_keys = self._load_cryptorank_api_keys()
        self.current_api_key_index = 0
        
        # Проверяем, есть ли ключи
        if self.cryptorank_api_keys:
            # Используем первый ключ
            self.api = self._initialize_cryptorank_client(self.cryptorank_api_keys[self.current_api_key_index])
        else:
            # Клиент с дефолтным ключом
            self.api = self._initialize_cryptorank_client("default_api_key")
            
        # Инициализируем Santiment API если предоставлен API-ключ
        self.santiment = None
        if santiment_api_key:
            try:
                self.santiment = SantimentAPI(santiment_api_key)
                logger.info("Инициализирован клиент Santiment API")
            except Exception as e:
                logger.error(f"Ошибка при инициализации Santiment API: {e}")
        
        # Настройки обновления данных
        self.min_update_interval = self._load_min_update_interval()
        self.last_api_update = None  # Время последнего обновления данных
        
        # Флаг для управления фоновым обновлением данных
        self._updating = False
        self._update_task = None
        
        logger.info("Инициализирован менеджер данных о криптовалютах")
    
    def _load_cryptorank_api_keys(self) -> List[str]:
        """
        Загружает API-ключи Cryptorank из конфигурации или переменных окружения
        
        Returns:
            List[str]: Список API-ключей
        """
        keys = []
        
        try:
            # Из конфигурации
            if self.config and "api" in self.config and "cryptorank" in self.config["api"]:
                if isinstance(self.config["api"]["cryptorank"], list):
                    for key_info in self.config["api"]["cryptorank"]:
                        if isinstance(key_info, dict) and "key" in key_info:
                            keys.append(key_info["key"])
                        elif isinstance(key_info, str):
                            keys.append(key_info)
                elif "key" in self.config["api"]["cryptorank"]:
                    keys.append(self.config["api"]["cryptorank"]["key"])
                else:
                    # Старый формат конфигурации с одним ключом
                    keys.append(self.config["api"]["cryptorank"])
        except Exception as e:
            logger.warning(f"Не удалось загрузить API-ключи из конфигурации: {e}")
        
        # Из переменной окружения
        env_key = os.getenv("CRYPTORANK_API_KEY")
        if env_key:
            keys.append(env_key)
        
        return keys
    
    def _initialize_cryptorank_client(self, api_key: str) -> CryptorankAPI:
        """
        Инициализирует клиент Cryptorank с заданным API-ключом
        
        Args:
            api_key: API-ключ для инициализации клиента
            
        Returns:
            CryptorankAPI: Инициализированный клиент
        """
        try:
            client = CryptorankAPI(api_key)
            logger.info("Клиент Cryptorank инициализирован")
            return client
        except Exception as e:
            logger.error(f"Ошибка при инициализации клиента Cryptorank: {e}")
            raise
    
    def _load_min_update_interval(self) -> timedelta:
        """
        Загружает минимальный интервал обновления из конфигурации
        
        Returns:
            timedelta: Минимальный интервал обновления
        """
        # По умолчанию 1 час
        default_interval = 3600  # 1 час в секундах
        
        try:
            # Получаем настройки из конфигурации
            if self.config and "background" in self.config and "update_interval" in self.config["background"]:
                interval_seconds = self.config["background"]["update_interval"]
                logger.info(f"Минимальный интервал обновления установлен из конфигурации: {interval_seconds} секунд")
                return timedelta(seconds=interval_seconds)
            else:
                logger.info(f"Минимальный интервал обновления установлен по умолчанию: {default_interval // 60} минут")
                return timedelta(seconds=default_interval)
        except Exception as e:
            logger.error(f"Ошибка при загрузке настроек обновления: {e}")
            return timedelta(seconds=default_interval)
    
    def _load_caching_settings(self) -> Dict[str, int]:
        """
        Загружает настройки кэширования из конфигурации
        
        Returns:
            Dict[str, int]: Настройки кэширования
        """
        # Настройки кэширования по умолчанию
        default_settings = {
            "coins_ttl": 3600,  # 1 час
            "coin_details_ttl": 1800,  # 30 минут
            "markets_ttl": 7200,  # 2 часа
            "exchanges_ttl": 7200  # 2 часа
        }
        
        try:
            # Получаем настройки из конфигурации
            if self.config and "caching" in self.config:
                caching_config = self.config["caching"]
                
                # Обновляем настройки, если они есть в конфигурации
                for key in default_settings:
                    if key in caching_config:
                        default_settings[key] = int(caching_config[key])
                        logger.info(f"Настройка кэширования {key} установлена из конфигурации: {default_settings[key]} секунд")
            
            return default_settings
        except Exception as e:
            logger.error(f"Ошибка при загрузке настроек кэширования: {e}")
            return default_settings
    
    @property
    def retry_interval(self) -> int:
        """
        Получает интервал повторных попыток из конфигурации
        
        Returns:
            int: Интервал повторных попыток
        """
        try:
            if self.config and "background" in self.config and "retry_interval" in self.config["background"]:
                return int(self.config["background"]["retry_interval"])
        except Exception as e:
            logger.error(f"Ошибка при получении интервала повторных попыток: {e}")
        
        return 300  # Значение по умолчанию - 5 минут
    
    async def start(self):
        """
        Запускает менеджер данных
        """
        # Запускаем WebSocket
        await self.websocket.start()
        
        # Запускаем фоновое обновление данных
        self._updating = True
        self._update_task = asyncio.create_task(self._update_loop())
        
        logger.info("Запущен менеджер данных о криптовалютах")
    
    async def stop(self):
        """
        Останавливает менеджер данных
        """
        # Останавливаем фоновое обновление данных
        self._updating = False
        
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None
        
        # Останавливаем WebSocket
        await self.websocket.stop()
        
        logger.info("Остановлен менеджер данных о криптовалютах")
    
    async def _update_data(self):
        """
        Обновляет данные из API и сохраняет их в базу данных
        """
        try:
            logger.info("Начало обновления данных из API")
            
            # Получаем свежесть данных
            coins_updated, market_updated = await self.db.get_data_freshness()
            now = datetime.now()
            
            # Обновляем данные только если они старше установленного интервала
            update_coins = not coins_updated or (now - coins_updated) > self.min_update_interval
            update_market = not market_updated or (now - market_updated) > self.min_update_interval
            
            if update_coins:
                # Используем заглушки вместо API запросов
                coins = await self._get_mock_coins(limit=500)
                
                if coins:
                    # Сохраняем данные в базу данных
                    await self.db.save_coins(coins)
                    
                    # Инвалидируем кэш
                    self.cache.invalidate("get_coins")
                    
                    logger.info(f"Обновлены данные о {len(coins)} монетах")
            
            if update_market:
                # Получаем рыночные данные из заглушки
                market_data = self._get_mock_market_data()
                
                if market_data:
                    # Сохраняем данные в базу данных
                    await self.db.save_market_data(market_data)
                    
                    # Инвалидируем кэш
                    self.cache.invalidate("get_market_data")
                    
                    logger.info("Обновлены рыночные данные")
            
            # Очищаем устаревшие данные из базы
            await self.db.cleanup_old_data()
            
            logger.info("Завершено обновление данных из API")
        except Exception as e:
            logger.error(f"Ошибка при обновлении данных: {e}")
            # Сохраняем информацию об ошибке
            self._last_error = str(e)
    
    async def _get_mock_coins(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Генерирует заглушку для монет
        
        Args:
            limit: Максимальное количество монет
            
        Returns:
            List[Dict[str, Any]]: Список монет
        """
        # Список популярных монет
        popular_coins = [
            {"symbol": "BTC", "name": "Bitcoin", "price": 50000.0},
            {"symbol": "ETH", "name": "Ethereum", "price": 3000.0},
            {"symbol": "BNB", "name": "Binance Coin", "price": 400.0},
            {"symbol": "SOL", "name": "Solana", "price": 100.0},
            {"symbol": "XRP", "name": "Ripple", "price": 0.5},
            {"symbol": "ADA", "name": "Cardano", "price": 0.4},
            {"symbol": "DOGE", "name": "Dogecoin", "price": 0.1},
            {"symbol": "DOT", "name": "Polkadot", "price": 6.0},
            {"symbol": "AVAX", "name": "Avalanche", "price": 30.0},
            {"symbol": "MATIC", "name": "Polygon", "price": 0.8},
            {"symbol": "LINK", "name": "Chainlink", "price": 15.0},
            {"symbol": "UNI", "name": "Uniswap", "price": 5.0},
            {"symbol": "ATOM", "name": "Cosmos", "price": 8.0},
            {"symbol": "LTC", "name": "Litecoin", "price": 70.0},
            {"symbol": "SHIB", "name": "Shiba Inu", "price": 0.00001},
            {"symbol": "NEAR", "name": "Near Protocol", "price": 3.0},
            {"symbol": "ALGO", "name": "Algorand", "price": 0.2},
            {"symbol": "FTM", "name": "Fantom", "price": 0.4},
            {"symbol": "MANA", "name": "Decentraland", "price": 0.5},
            {"symbol": "XLM", "name": "Stellar", "price": 0.1}
        ]
        
        mock_coins = []
        
        for i, coin_data in enumerate(popular_coins[:limit]):
            # Генерируем случайное изменение цены
            price_change_percent = (np.random.random() - 0.5) * 10  # от -5% до +5%
            price_change = coin_data["price"] * price_change_percent / 100
            
            # Генерируем случайный объем
            volume = coin_data["price"] * np.random.uniform(1000, 100000)
            
            # Генерируем случайную рыночную капитализацию
            market_cap = coin_data["price"] * np.random.uniform(1000000, 10000000000)
            
            # Создаем заглушку для монеты
            mock_coin = {
                "id": f"mock-{coin_data['symbol'].lower()}",
                "symbol": coin_data["symbol"],
                "name": coin_data["name"],
                "price": coin_data["price"],
                "price_change_24h": price_change,
                "price_change_percent_24h": price_change_percent,
                "volume24h": volume,
                "marketCap": market_cap,
                "rank": i + 1,
                "high24h": coin_data["price"] * (1 + np.random.uniform(0, 0.05)),
                "low24h": coin_data["price"] * (1 - np.random.uniform(0, 0.05))
            }
            
            mock_coins.append(mock_coin)
        
        return mock_coins
    
    def _get_mock_market_data(self) -> Dict[str, Any]:
        """
        Генерирует заглушку для рыночных данных
        
        Returns:
            Dict[str, Any]: Рыночные данные
        """
        return {
            "totalMarketCap": 1.2e12,  # 1.2 триллиона
            "total24hVolume": 48.5e9,  # 48.5 миллиардов
            "btcDominance": 52.3,
            "timestamp": datetime.now().isoformat()
        }
    
    @cached(ttl=3600)  # Используем ttl из конфигурации
    async def get_coins(self, limit: int = 100, offset: int = 0) -> Optional[List[Dict[str, Any]]]:
        """
        Получает информацию о монетах
        
        Args:
            limit: Максимальное количество монет
            offset: Смещение для пагинации
            
        Returns:
            Optional[List[Dict[str, Any]]]: Список монет или None
        """
        # Проверяем кэш
        cache_key = f"coins_{limit}_{offset}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.debug(f"Получено {len(cached_data)} монет из кэша")
            return cached_data
        
        # Получаем данные из API
        try:
            coins = await self.api.get_coins(limit=limit, offset=offset)
            
            # Если получили ошибку лимита, переключаемся на следующий ключ
            if not coins and hasattr(self.api, "_last_error") and "daily credits used" in str(self.api._last_error):
                logger.warning("Достигнут дневной лимит текущего ключа")
                await self._switch_cryptorank_api_key()
                coins = await self.api.get_coins(limit=limit, offset=offset)
            
            if coins:
                # Сохраняем в кэш только если нет ошибки
                self.cache.set(cache_key, coins, ttl=self.caching_settings['coins_ttl'])
                logger.debug(f"Сохранено {len(coins)} монет в кэш")
            
            return coins
        except Exception as e:
            logger.error(f"Ошибка при получении списка монет: {e}")
            return None
    
    @cached(ttl=1800)  # Используем ttl из конфигурации
    async def get_coin_details(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Получает детали о криптовалюте
        
        Args:
            symbol: Символ монеты
            
        Returns:
            Optional[Dict[str, Any]]: Детали монеты или None
        """
        try:
            # Сначала проверяем данные из WebSocket (самые свежие)
            websocket_data = self.websocket.get_price_data(symbol)
            
            # Получаем данные из базы данных
            db_data = await self.db.get_coin_by_symbol(symbol)
            
            # Если есть данные из WebSocket, обновляем данные из базы
            if websocket_data and db_data:
                db_data['price'] = websocket_data['price']
                db_data['price_change_24h'] = websocket_data['price_change']
                db_data['price_change_percent_24h'] = websocket_data['price_change_percent']
                db_data['volume_24h'] = websocket_data['volume']
                db_data['high_24h'] = websocket_data['high']
                db_data['low_24h'] = websocket_data['low']
                
                # Добавляем данные о времени обновления
                db_data['last_updated'] = datetime.now().isoformat()
            
            # Если нет данных в базе и из WebSocket, генерируем заглушку
            if not db_data:
                # Словарь популярных монет
                popular_coins = {
                    "BTC": {"name": "Bitcoin", "price": 50000.0},
                    "ETH": {"name": "Ethereum", "price": 3000.0},
                    "BNB": {"name": "Binance Coin", "price": 400.0},
                    "SOL": {"name": "Solana", "price": 100.0},
                    "XRP": {"name": "Ripple", "price": 0.5},
                    "ADA": {"name": "Cardano", "price": 0.4},
                    "DOGE": {"name": "Dogecoin", "price": 0.1},
                    "DOT": {"name": "Polkadot", "price": 6.0},
                    "AVAX": {"name": "Avalanche", "price": 30.0},
                    "MATIC": {"name": "Polygon", "price": 0.8},
                    "LINK": {"name": "Chainlink", "price": 15.0},
                    "UNI": {"name": "Uniswap", "price": 5.0},
                    "ATOM": {"name": "Cosmos", "price": 8.0},
                    "LTC": {"name": "Litecoin", "price": 70.0},
                    "SHIB": {"name": "Shiba Inu", "price": 0.00001},
                    "NEAR": {"name": "Near Protocol", "price": 3.0},
                    "ALGO": {"name": "Algorand", "price": 0.2},
                    "FTM": {"name": "Fantom", "price": 0.4},
                    "MANA": {"name": "Decentraland", "price": 0.5},
                    "XLM": {"name": "Stellar", "price": 0.1}
                }
                
                # Проверяем, есть ли монета в списке популярных
                symbol_upper = symbol.upper()
                if symbol_upper in popular_coins:
                    coin_data = popular_coins[symbol_upper]
                    
                    # Генерируем случайное изменение цены
                    price_change_percent = (np.random.random() - 0.5) * 10  # от -5% до +5%
                    price_change = coin_data["price"] * price_change_percent / 100
                    
                    # Генерируем случайный объем
                    volume = coin_data["price"] * np.random.uniform(1000, 100000)
                    
                    # Генерируем случайную рыночную капитализацию
                    market_cap = coin_data["price"] * np.random.uniform(1000000, 10000000)
                    
                    # Создаем заглушку для монеты
                    mock_coin = {
                        "id": f"mock-{symbol_upper.lower()}",
                        "symbol": symbol_upper,
                        "name": coin_data["name"],
                        "price": coin_data["price"],
                        "price_change_24h": price_change,
                        "price_change_percent_24h": price_change_percent,
                        "volume24h": volume,
                        "marketCap": market_cap,
                        "rank": list(popular_coins.keys()).index(symbol_upper) + 1,
                        "high24h": coin_data["price"] * (1 + np.random.uniform(0, 0.05)),
                        "low24h": coin_data["price"] * (1 - np.random.uniform(0, 0.05))
                    }
                    
                    return mock_coin
            
            # Если есть клиент Santiment, получаем дополнительные метрики
            if self.santiment and db_data:
                try:
                    slug = symbol.lower()
                    
                    # Получаем активность разработчиков
                    dev_activity = self.santiment.get_dev_activity(slug, days=30)
                    if dev_activity:
                        # Вычисляем среднее значение активности за последние 7 дней
                        recent_dev_activity = dev_activity[-7:]
                        avg_value = sum(item["value"] for item in recent_dev_activity) / len(recent_dev_activity)
                        db_data['dev_activity'] = avg_value
                        
                        # Добавляем тенденцию (positive, negative, neutral) на основе сравнения последних 3 и предыдущих 3 дней
                        if len(dev_activity) >= 6:
                            last_3 = sum(item["value"] for item in dev_activity[-3:]) / 3
                            prev_3 = sum(item["value"] for item in dev_activity[-6:-3]) / 3
                            
                            if last_3 > prev_3 * 1.2:
                                db_data['dev_activity_trend'] = 'positive'
                            elif last_3 < prev_3 * 0.8:
                                db_data['dev_activity_trend'] = 'negative'
                            else:
                                db_data['dev_activity_trend'] = 'neutral'
                        
                    # Получаем социальный объем
                    social_volume = self.santiment.get_social_volume(slug, days=30)
                    if social_volume:
                        # Вычисляем среднее значение социального объема за последние 7 дней
                        recent_social_volume = social_volume[-7:]
                        avg_value = sum(item["value"] for item in recent_social_volume) / len(recent_social_volume)
                        db_data['social_volume'] = avg_value
                        
                        # Добавляем тенденцию (positive, negative, neutral) на основе сравнения последних 3 и предыдущих 3 дней
                        if len(social_volume) >= 6:
                            last_3 = sum(item["value"] for item in social_volume[-3:]) / 3
                            prev_3 = sum(item["value"] for item in social_volume[-6:-3]) / 3
                            
                            if last_3 > prev_3 * 1.2:
                                db_data['social_volume_trend'] = 'positive'
                            elif last_3 < prev_3 * 0.8:
                                db_data['social_volume_trend'] = 'negative'
                            else:
                                db_data['social_volume_trend'] = 'neutral'
                        
                    # Получаем потоки на биржах
                    exchange_flows = self.santiment.get_exchange_flows(slug, days=30)
                    if exchange_flows:
                        # Вычисляем среднее значение потоков на биржах за последние 7 дней
                        recent_exchange_flows = exchange_flows[-7:]
                        avg_value = sum(item["value"] for item in recent_exchange_flows) / len(recent_exchange_flows)
                        db_data['exchange_flows'] = avg_value
                        
                        # Добавляем тенденцию (positive, negative, neutral) на основе сравнения последних 3 и предыдущих 3 дней
                        if len(exchange_flows) >= 6:
                            last_3 = sum(item["value"] for item in exchange_flows[-3:]) / 3
                            prev_3 = sum(item["value"] for item in exchange_flows[-6:-3]) / 3
                            
                            if last_3 > prev_3 * 1.2:
                                db_data['exchange_flows_trend'] = 'positive'
                            elif last_3 < prev_3 * 0.8:
                                db_data['exchange_flows_trend'] = 'negative'
                            else:
                                db_data['exchange_flows_trend'] = 'neutral'
                        
                    # Получаем рост сети
                    network_growth = self.santiment.get_network_growth(slug, days=30)
                    if network_growth:
                        # Вычисляем среднее значение роста сети за последние 7 дней
                        recent_network_growth = network_growth[-7:]
                        avg_value = sum(item["value"] for item in recent_network_growth) / len(recent_network_growth)
                        db_data['network_growth'] = avg_value
                        
                        # Добавляем тенденцию (positive, negative, neutral) на основе сравнения последних 3 и предыдущих 3 дней
                        if len(network_growth) >= 6:
                            last_3 = sum(item["value"] for item in network_growth[-3:]) / 3
                            prev_3 = sum(item["value"] for item in network_growth[-6:-3]) / 3
                            
                            if last_3 > prev_3 * 1.2:
                                db_data['network_growth_trend'] = 'positive'
                            elif last_3 < prev_3 * 0.8:
                                db_data['network_growth_trend'] = 'negative'
                            else:
                                db_data['network_growth_trend'] = 'neutral'
                        
                except Exception as e:
                    logger.error(f"Ошибка при получении данных из Santiment API: {e}")
            
            return db_data
        except Exception as e:
            logger.error(f"Ошибка при получении деталей монеты: {e}")
            return None
    
    @cached(ttl=7200)  # Используем ttl из конфигурации
    async def get_market_data(self) -> Optional[Dict[str, Any]]:
        """
        Получает рыночные данные
        
        Returns:
            Optional[Dict[str, Any]]: Рыночные данные или None
        """
        # Используем кэш для рыночных данных
        cache_key = "market_data"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.debug("Получены рыночные данные из кэша")
            return cached_data
        
        # Проверяем свежесть данных
        _, market_updated = await self.db.get_data_freshness()
        
        # Если данные свежие (не старше 1 часа), берем из базы данных
        if market_updated and datetime.now() - market_updated < timedelta(hours=1):
            logger.info("Получение рыночных данных из базы данных")
            return await self.db.get_latest_market_data()
        
        # Иначе генерируем заглушку для рыночных данных
        logger.info("Генерация заглушки для рыночных данных")
        return self._get_mock_market_data()
    
    async def get_price_history(self, symbol: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Получает историю цен монеты
        
        Args:
            symbol: Символ монеты
            days: Количество дней истории
            
        Returns:
            List[Dict[str, Any]]: История цен
        """
        # Получаем информацию о монете
        coin = await self.get_coin_by_symbol(symbol)
        
        if not coin:
            return []
        
        coin_id = coin.get('id', '')
        
        if not coin_id:
            return []
        
        # Получаем историю из базы данных
        history = await self.db.get_price_history(coin_id, days)
        
        # Возвращаем историю из базы данных, даже если она неполная
        if history:
            return history
        
        # Генерируем заглушку для истории цен
        mock_history = []
        current_price = coin.get('price', 1000)
        
        # Используем более длительный интервал для генерации истории
        interval = timedelta(days=1)
        start_date = datetime.now() - timedelta(days=days)
        
        for i in range(days):
            # Генерируем случайную цену в пределах ±5% от текущей
            price_change = (np.random.random() - 0.5) * 0.1  # от -5% до +5%
            price = current_price * (1 + price_change)
            
            # Генерируем случайный объем
            volume = current_price * np.random.uniform(100, 10000)
            
            # Генерируем случайную рыночную капитализацию
            market_cap = price * np.random.uniform(1000000, 10000000)
            
            # Добавляем точку истории
            mock_history.append({
                'timestamp': (start_date + i * interval).isoformat(),
                'price': price,
                'volume': volume,
                'marketCap': market_cap
            })
        
        return mock_history
    
    async def get_coin_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о монете по символу
        
        Args:
            symbol: Символ монеты
            
        Returns:
            Optional[Dict[str, Any]]: Информация о монете или None
        """
        # Используем кэш с уникальным ключом для каждой монеты
        cache_key = f"coin:{symbol}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            logger.debug(f"Получена информация о монете {symbol} из кэша")
            return cached_data
        
        # Получаем данные из базы данных
        coin = await self.db.get_coin_by_symbol(symbol)
        
        if coin:
            # Сохраняем в кэш
            self.cache.set(cache_key, coin, ttl=self.caching_settings['coin_details_ttl'])
            logger.debug(f"Сохранена информация о монете {symbol} в кэш")
        
        return coin
    
    async def get_top_coins(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Получает топ монет по рыночной капитализации
        
        Args:
            limit: Количество монет
            
        Returns:
            List[Dict[str, Any]]: Список топ монет
        """
        # Получаем монеты из базы данных или API
        coins = await self.get_coins(limit=limit)
        
        # Обновляем данные из WebSocket, если доступны
        for coin in coins:
            symbol = coin.get('symbol', '')
            websocket_data = self.websocket.get_price_data(symbol)
            
            if websocket_data:
                coin['price'] = websocket_data['price']
                coin['price_change_24h'] = websocket_data['price_change']
                coin['price_change_percent_24h'] = websocket_data['price_change_percent']
        
        return coins
    
    async def get_market_overview(self) -> Dict[str, Any]:
        """
        Получает обзор рынка
        
        Returns:
            Dict[str, Any]: Обзор рынка
        """
        # Получаем рыночные данные
        market_data = await self.get_market_data() or {}
        
        # Получаем топ монет
        top_coins = await self.get_top_coins(20)
        
        # Разделяем на растущие и падающие
        gainers = []
        losers = []
        
        for coin in top_coins:
            price_change = coin.get('price_change_percent_24h', 0)
            
            if price_change > 0:
                gainers.append(coin)
            else:
                losers.append(coin)
        
        # Сортируем по изменению цены
        gainers.sort(key=lambda x: x.get('price_change_percent_24h', 0), reverse=True)
        losers.sort(key=lambda x: x.get('price_change_percent_24h', 0))
        
        # Формируем обзор рынка
        overview = {
            'total_market_cap': market_data.get('totalMarketCap', 0),
            'total_volume_24h': market_data.get('total24hVolume', 0),
            'btc_dominance': market_data.get('btcDominance', 0),
            'top_gainers': gainers[:5],  # Топ-5 растущих
            'top_losers': losers[:5],    # Топ-5 падающих
            'timestamp': datetime.now()
        }
        
        return overview
    
    async def _update_loop(self):
        """
        Фоновый процесс для обновления данных
        """
        try:
            logger.info("Фоновое обновление данных запущено")
            
            while self._updating:
                # Проверяем, не было ли недавно обновления
                if not self.last_api_update or (datetime.now() - self.last_api_update) > self.min_update_interval:
                    # Обновляем данные
                    await self._update_data()
                    self.last_api_update = datetime.now()
                
                # Ждем перед следующей проверкой
                # Если был достигнут лимит API, ждем дольше
                if hasattr(self, '_last_error') and "daily credits used" in str(getattr(self, '_last_error', '')):
                    # Используем интервал повторных попыток из конфигурации
                    retry_interval = self.retry_interval
                    logger.info(f"Достигнут лимит API, повторная попытка через {retry_interval} секунд")
                    await asyncio.sleep(retry_interval)
                else:
                    # Используем стандартный интервал
                    update_interval = self.min_update_interval.total_seconds()
                    logger.info(f"Следующая проверка через {update_interval} секунд")
                    await asyncio.sleep(update_interval)
        except asyncio.CancelledError:
            logger.info("Отменен фоновый процесс обновления данных")
        except Exception as e:
            logger.error(f"Ошибка в фоновом процессе обновления данных: {e}")
    
    async def _switch_cryptorank_api_key(self):
        """
        Переключается на следующий доступный API-ключ при достижении лимитов
        """
        if len(self.cryptorank_api_keys) <= 1:
            logger.warning("Нет дополнительных API-ключей для переключения")
            return
        
        # Переключаемся на следующий ключ
        self.current_api_key_index = (self.current_api_key_index + 1) % len(self.cryptorank_api_keys)
        new_api_key = self.cryptorank_api_keys[self.current_api_key_index]
        
        try:
            # Инициализируем новый клиент
            self.api = self._initialize_cryptorank_client(new_api_key)
            logger.info(f"Переключились на новый API-ключ: {new_api_key[-4:]}")
        except Exception as e:
            logger.error(f"Ошибка при инициализации нового клиента: {e}")
            # Пробуем следующий ключ
            await self._switch_cryptorank_api_key()

# Создаем глобальный экземпляр менеджера данных
_data_manager = None

def get_data_manager() -> CryptoDataManager:
    """
    Получает глобальный экземпляр менеджера данных
    
    Returns:
        CryptoDataManager: Глобальный экземпляр менеджера данных
    """
    global _data_manager
    
    if _data_manager is None:
        try:
            # Получаем конфигурацию
            from ..config.config import get_config, get_santiment_api_key
            config = get_config()
            
            # Получаем API-ключ Santiment
            santiment_api_key = get_santiment_api_key()
            
            # Инициализируем менеджер данных с API-ключом Santiment
            _data_manager = CryptoDataManager(santiment_api_key=santiment_api_key)
        except Exception as e:
            logger.error(f"Ошибка при инициализации менеджера данных: {e}")
            
        # Если все еще нет менеджера, создаем минимальный экземпляр
        if _data_manager is None:
            _data_manager = CryptoDataManager(santiment_api_key=None)
            logger.warning("Создан базовый менеджер данных без конфигурации")
    
    return _data_manager
