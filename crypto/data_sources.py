import logging
import aiohttp
import asyncio
import json
import time
import sys
import traceback
from datetime import datetime, timedelta
from .config import crypto_config

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

class CryptoDataSource:
    """
    Базовый класс для источников данных по криптовалюте
    """
    def __init__(self):
        self.session = None
        self.last_request_time = {}
        self.rate_limit_delay = 1  # Задержка между запросами в секундах
    
    async def initialize(self):
        """
        Инициализация сессии для HTTP запросов
        """
        if self.session is None:
            self.session = aiohttp.ClientSession()
            logger.info(f"Инициализирована HTTP сессия для {self.__class__.__name__}")
    
    async def close(self):
        """
        Закрытие сессии
        """
        if self.session:
            await self.session.close()
            self.session = None
            logger.info(f"Закрыта HTTP сессия для {self.__class__.__name__}")
    
    async def _make_request(self, url, method="GET", headers=None, params=None, data=None):
        """
        Выполняет HTTP запрос с учетом ограничений по частоте
        
        Args:
            url (str): URL для запроса
            method (str): HTTP метод (GET, POST и т.д.)
            headers (dict): Заголовки запроса
            params (dict): Параметры запроса
            data (dict): Данные для отправки в теле запроса
            
        Returns:
            dict: Результат запроса в формате JSON
        """
        await self.initialize()
        
        # Проверяем ограничение частоты запросов
        endpoint = url.split('/')[-1]
        current_time = time.time()
        
        if endpoint in self.last_request_time:
            elapsed = current_time - self.last_request_time[endpoint]
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)
        
        self.last_request_time[endpoint] = time.time()
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Ошибка запроса {url}: {response.status} - {error_text}")
                    return None
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса {url}: {e}")
            return None


class BinanceDataSource(CryptoDataSource):
    """
    Источник данных с биржи Binance
    """
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.binance.com/api/v3"
        self.api_key = crypto_config.get('api_keys', {}).get('binance', '')
        self.rate_limit_delay = 0.5  # Binance имеет ограничение 1200 запросов в минуту
    
    async def get_ticker_price(self, symbol):
        """
        Получает текущую цену для указанного символа
        
        Args:
            symbol (str): Торговая пара (например, BTCUSDT)
            
        Returns:
            float: Текущая цена
        """
        url = f"{self.base_url}/ticker/price"
        params = {"symbol": symbol}
        
        result = await self._make_request(url, params=params)
        if result and "price" in result:
            return float(result["price"])
        return None
    
    async def get_klines(self, symbol, interval, limit=100):
        """
        Получает свечи (klines) для указанного символа и интервала
        
        Args:
            symbol (str): Торговая пара (например, BTCUSDT)
            interval (str): Интервал (1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d и т.д.)
            limit (int): Количество свечей (макс. 1000)
            
        Returns:
            list: Список свечей
        """
        url = f"{self.base_url}/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        result = await self._make_request(url, params=params)
        if result:
            # Преобразуем данные в более удобный формат
            klines = []
            for k in result:
                kline = {
                    "open_time": k[0],
                    "open": float(k[1]),
                    "high": float(k[2]),
                    "low": float(k[3]),
                    "close": float(k[4]),
                    "volume": float(k[5]),
                    "close_time": k[6],
                    "quote_volume": float(k[7]),
                    "trades": k[8],
                    "taker_buy_base": float(k[9]),
                    "taker_buy_quote": float(k[10])
                }
                klines.append(kline)
            return klines
        return []
    
    async def get_order_book(self, symbol, limit=100):
        """
        Получает книгу ордеров для указанного символа
        
        Args:
            symbol (str): Торговая пара (например, BTCUSDT)
            limit (int): Глубина книги ордеров (макс. 5000)
            
        Returns:
            dict: Книга ордеров
        """
        url = f"{self.base_url}/depth"
        params = {
            "symbol": symbol,
            "limit": limit
        }
        
        result = await self._make_request(url, params=params)
        if result:
            # Преобразуем строковые значения в числа
            for side in ["bids", "asks"]:
                result[side] = [[float(price), float(qty)] for price, qty in result[side]]
            return result
        return None
    
    async def get_recent_trades(self, symbol, limit=500):
        """
        Получает последние сделки для указанного символа
        
        Args:
            symbol (str): Торговая пара (например, BTCUSDT)
            limit (int): Количество сделок (макс. 1000)
            
        Returns:
            list: Список сделок
        """
        url = f"{self.base_url}/trades"
        params = {
            "symbol": symbol,
            "limit": limit
        }
        
        result = await self._make_request(url, params=params)
        if result:
            return result
        return []
    
    async def get_funding_rate(self, symbol):
        """
        Получает текущую ставку финансирования для фьючерсов
        
        Args:
            symbol (str): Торговая пара (например, BTCUSDT)
            
        Returns:
            float: Текущая ставка финансирования
        """
        # Для фьючерсов используется другой базовый URL
        futures_url = "https://fapi.binance.com/fapi/v1/premiumIndex"
        params = {"symbol": symbol}
        
        headers = {}
        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
        
        result = await self._make_request(futures_url, params=params, headers=headers)
        if result and "lastFundingRate" in result:
            return float(result["lastFundingRate"])
        return None
    
    async def get_open_interest(self, symbol):
        """
        Получает текущий открытый интерес для фьючерсов
        
        Args:
            symbol (str): Торговая пара (например, BTCUSDT)
            
        Returns:
            float: Текущий открытый интерес
        """
        # Для фьючерсов используется другой базовый URL
        futures_url = "https://fapi.binance.com/fapi/v1/openInterest"
        params = {"symbol": symbol}
        
        headers = {}
        if self.api_key:
            headers["X-MBX-APIKEY"] = self.api_key
        
        result = await self._make_request(futures_url, params=params, headers=headers)
        if result and "openInterest" in result:
            return float(result["openInterest"])
        return None


class WhaleAlertDataSource(CryptoDataSource):
    """
    Источник данных о крупных транзакциях (китах) через Whale Alert API
    """
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.whale-alert.io/v1"
        self.api_key = crypto_config.get('api_keys', {}).get('whale_alert', '')
        self.rate_limit_delay = 5  # Whale Alert имеет строгие ограничения
    
    async def get_transactions(self, min_value=500000, limit=10):
        """
        Получает последние крупные транзакции
        
        Args:
            min_value (int): Минимальная стоимость транзакции в USD
            limit (int): Количество транзакций
            
        Returns:
            list: Список транзакций
        """
        if not self.api_key:
            logger.warning("API ключ для Whale Alert не настроен")
            return []
        
        url = f"{self.base_url}/transactions"
        params = {
            "api_key": self.api_key,
            "min_value": min_value,
            "limit": limit
        }
        
        result = await self._make_request(url, params=params)
        if result and "transactions" in result:
            return result["transactions"]
        return []


class CryptorankDataSource(CryptoDataSource):
    """
    Источник данных о криптовалютах через Cryptorank API
    """
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.cryptorank.io/v1"
        self.api_key = crypto_config.get('api_keys', {}).get('cryptorank', '')
        self.rate_limit_delay = 1
    
    async def get_coins(self, limit=100):
        """
        Получает информацию о криптовалютах
        
        Args:
            limit (int): Количество криптовалют
            
        Returns:
            list: Список криптовалют
        """
        url = f"{self.base_url}/currencies"
        params = {"limit": limit}
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        result = await self._make_request(url, params=params)
        if result and "data" in result:
            return result["data"]
        return []
    
    async def get_coin_details(self, coin_key):
        """
        Получает детальную информацию о криптовалюте
        
        Args:
            coin_key (str): Ключ криптовалюты (например, "bitcoin")
            
        Returns:
            dict: Информация о криптовалюте
        """
        url = f"{self.base_url}/currencies/{coin_key}"
        params = {}
        
        if self.api_key:
            params["api_key"] = self.api_key
        
        result = await self._make_request(url, params=params)
        if result and "data" in result:
            return result["data"]
        return None


class DataSourceManager:
    """
    Менеджер источников данных
    """
    def __init__(self):
        self.sources = {
            "binance": BinanceDataSource(),
            "whale_alert": WhaleAlertDataSource(),
            "cryptorank": CryptorankDataSource()
        }
    
    async def initialize(self):
        """
        Инициализация всех источников данных
        """
        for name, source in self.sources.items():
            await source.initialize()
            logger.info(f"Инициализирован источник данных: {name}")
    
    async def close(self):
        """
        Закрытие всех источников данных
        """
        for name, source in self.sources.items():
            await source.close()
            logger.info(f"Закрыт источник данных: {name}")
    
    def get_source(self, name):
        """
        Получает источник данных по имени
        
        Args:
            name (str): Имя источника данных
            
        Returns:
            CryptoDataSource: Источник данных
        """
        return self.sources.get(name)