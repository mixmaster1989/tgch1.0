"""
Модуль для работы с API Cryptorank V2
"""

import aiohttp
import logging
import time
from typing import Dict, List, Any, Optional
import asyncio
from datetime import datetime, timedelta

from ..config import get_cryptorank_api_key, get_config

# Получаем логгер для модуля
logger = logging.getLogger('crypto.data_sources.cryptorank')

class CryptorankAPI:
    """
    Класс для работы с API Cryptorank V2
    """
    
    def __init__(self):
        """
        Инициализирует клиент API Cryptorank
        """
        config = get_config()
        self.api_key = get_cryptorank_api_key()
        self.base_url = "https://api.cryptorank.io/v2"
        self.rate_limit = config['api']['cryptorank']['rate_limit']
        
        # Для отслеживания запросов и соблюдения rate limit
        self.last_request_time = 0
        self.requests_in_current_minute = 0
        self.credits_used = 0
        
        logger.info("Инициализирован клиент API Cryptorank V2")
    
    # Словарь для отслеживания ошибок по эндпоинтам
    _endpoint_errors = {}
    # Список эндпоинтов, доступных на бесплатном тарифе
    _free_endpoints = [
        'currencies',
        'currencies/categories',
        'currencies/map',
        'currencies/tags',
        'global',
        'exchanges/map'
    ]
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполняет запрос к API с учетом rate limit и доступности эндпоинтов
        
        Args:
            endpoint: Конечная точка API
            params: Параметры запроса
            
        Returns:
            Dict[str, Any]: Ответ API в формате JSON
        """
        # Проверяем, доступен ли эндпоинт на бесплатном тарифе
        base_endpoint = endpoint.split('/')[0]
        if base_endpoint not in self._free_endpoints and not any(endpoint.startswith(f"{e}/") for e in self._free_endpoints):
            # Проверяем, не превышен ли лимит ошибок для этого эндпоинта
            if endpoint in self._endpoint_errors and self._endpoint_errors[endpoint] >= 3:
                logger.warning(f"Эндпоинт {endpoint} недоступен на бесплатном тарифе и был заблокирован после 3 ошибок")
                raise Exception(f"Endpoint {endpoint} is not available in free plan and has been blocked")
        
        # Проверяем rate limit
        current_time = time.time()
        if current_time - self.last_request_time > 60:
            # Прошла минута, сбрасываем счетчик
            self.requests_in_current_minute = 0
            self.last_request_time = current_time
        
        if self.requests_in_current_minute >= self.rate_limit['requests_per_minute']:
            # Превышен лимит запросов, ждем
            wait_time = 60 - (current_time - self.last_request_time)
            if wait_time > 0:
                logger.warning(f"Превышен rate limit, ожидание {wait_time:.2f} секунд")
                await asyncio.sleep(wait_time)
                # Сбрасываем счетчик после ожидания
                self.requests_in_current_minute = 0
                self.last_request_time = time.time()
        
        # Формируем URL и параметры
        url = f"{self.base_url}/{endpoint}"
        if params is None:
            params = {}
        
        # Добавляем API ключ в заголовки
        headers = {
            "X-Api-Key": self.api_key,
            "Accept": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    # Увеличиваем счетчик запросов
                    self.requests_in_current_minute += 1
                    self.last_request_time = time.time()
                    
                    # Проверяем статус ответа
                    if response.status == 200:
                        data = await response.json()
                        
                        # Отслеживаем использованные кредиты
                        if 'status' in data and 'usedCredits' in data['status']:
                            self.credits_used = data['status']['usedCredits']
                            logger.debug(f"Использовано кредитов: {self.credits_used}")
                        
                        # Сбрасываем счетчик ошибок для этого эндпоинта
                        if endpoint in self._endpoint_errors:
                            self._endpoint_errors[endpoint] = 0
                        
                        return data
                    elif response.status == 403:
                        error_text = await response.text()
                        logger.error(f"Ошибка API Cryptorank: {response.status} - {error_text}")
                        
                        # Увеличиваем счетчик ошибок для этого эндпоинта
                        if endpoint not in self._endpoint_errors:
                            self._endpoint_errors[endpoint] = 1
                        else:
                            self._endpoint_errors[endpoint] += 1
                        
                        raise Exception(f"API error: {response.status} - {error_text}")
                    else:
                        error_text = await response.text()
                        logger.error(f"Ошибка API Cryptorank: {response.status} - {error_text}")
                        raise Exception(f"API error: {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка соединения с API Cryptorank: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Неизвестная ошибка при запросе к API Cryptorank: {e}", exc_info=True)
            raise
    
    async def get_coins(self, limit: int = 100, offset: int = 0, 
                       include_percent_change: bool = True, 
                       include_sparkline: bool = False,
                       category_id: Optional[int] = None,
                       sort_by: str = "rank") -> List[Dict[str, Any]]:
        """
        Получает список криптовалют
        
        Args:
            limit: Максимальное количество монет (100, 500 или 1000)
            offset: Смещение для пагинации
            include_percent_change: Включить данные об изменении цены
            include_sparkline: Включить данные для графика
            category_id: ID категории для фильтрации
            sort_by: Поле для сортировки (rank, marketCap, volume24h)
            
        Returns:
            List[Dict[str, Any]]: Список монет
        """
        try:
            # API требует, чтобы limit был одним из значений: 100, 500, 1000
            if limit <= 100:
                limit = 100
            elif limit <= 500:
                limit = 500
            else:
                limit = 1000
                
            params = {
                'limit': limit,
                'skip': offset,
                'sortBy': sort_by,
                'sortDirection': 'ASC' if sort_by == 'rank' else 'DESC'
            }
            
            # Добавляем опциональные параметры
            include_params = []
            if include_percent_change:
                include_params.append('percentChange')
            if include_sparkline:
                include_params.append('sparkline7d')
            
            if include_params:
                params['include'] = include_params
                
            if category_id is not None:
                params['categoryId'] = category_id
            
            # Используем эндпоинт для v2 API
            response = await self._make_request('currencies', params)
            
            if 'data' in response:
                coins = response['data']
                logger.info(f"Получено {len(coins)} монет из API Cryptorank")
                return coins
            else:
                logger.error(f"Неожиданный формат ответа API: {response}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении списка монет: {e}", exc_info=True)
            return []
    
    async def get_coin_details(self, coin_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает детальную информацию о монете
        
        Args:
            coin_id: Идентификатор монеты
            
        Returns:
            Optional[Dict[str, Any]]: Информация о монете или None в случае ошибки
        """
        try:
            # Используем эндпоинт для v2 API
            response = await self._make_request(f'currencies/{coin_id}')
            
            if 'data' in response:
                coin_data = response['data']
                logger.info(f"Получена информация о монете {coin_id}")
                return coin_data
            else:
                logger.error(f"Неожиданный формат ответа API: {response}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении информации о монете {coin_id}: {e}", exc_info=True)
            return None
    
    async def get_coin_full_metadata(self, coin_id: int) -> Optional[Dict[str, Any]]:
        """
        Получает полную метаинформацию о монете
        
        Args:
            coin_id: Идентификатор монеты
            
        Returns:
            Optional[Dict[str, Any]]: Полная информация о монете или None в случае ошибки
        """
        try:
            # Используем эндпоинт для полной метаинформации
            response = await self._make_request(f'currencies/{coin_id}/full-metadata')
            
            if 'data' in response:
                coin_data = response['data']
                logger.info(f"Получена полная метаинформация о монете {coin_id}")
                return coin_data
            else:
                logger.error(f"Неожиданный формат ответа API: {response}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении полной метаинформации о монете {coin_id}: {e}", exc_info=True)
            return None
    
    async def get_market_data(self) -> Optional[Dict[str, Any]]:
        """
        Получает общие данные о рынке
        
        Returns:
            Optional[Dict[str, Any]]: Данные о рынке или None в случае ошибки
        """
        try:
            # Используем эндпоинт для v2 API
            response = await self._make_request('global')
            
            if 'data' in response:
                market_data = response['data']
                logger.info("Получены данные о рынке")
                return market_data
            else:
                logger.error(f"Неожиданный формат ответа API: {response}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении данных о рынке: {e}", exc_info=True)
            return None
    
    async def get_coin_historical(self, coin_id: int, start_date: str, 
                                 end_date: Optional[str] = None, 
                                 interval: str = "day", 
                                 limit: int = 20) -> List[Dict[str, Any]]:
        """
        Получает исторические данные о монете
        
        Args:
            coin_id: Идентификатор монеты
            start_date: Начальная дата в формате YYYY-MM-DD
            end_date: Конечная дата в формате YYYY-MM-DD (по умолчанию сегодня)
            interval: Интервал данных (day, week, month)
            limit: Количество точек данных (20, 50, 100)
            
        Returns:
            List[Dict[str, Any]]: Исторические данные
        """
        try:
            params = {
                'startDate': start_date,
                'interval': interval,
                'limit': min(limit, 100)  # Максимум 100 по документации
            }
            
            if end_date:
                params['endDate'] = end_date
            
            # Используем эндпоинт для исторических данных
            response = await self._make_request(f'currencies/{coin_id}/historical', params)
            
            if 'data' in response:
                historical_data = response['data']
                logger.info(f"Получены исторические данные для монеты {coin_id}")
                return historical_data
            else:
                logger.error(f"Неожиданный формат ответа API: {response}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении исторических данных для монеты {coin_id}: {e}", exc_info=True)
            return []
    
    async def get_coin_sparkline(self, coin_id: int, days: int = 7, interval: str = "1d") -> Optional[Dict[str, Any]]:
        """
        Получает данные для графика цены и объема
        
        Args:
            coin_id: Идентификатор монеты
            days: Количество дней для данных
            interval: Интервал данных (5m, 15m, 1h, 1d)
            
        Returns:
            Optional[Dict[str, Any]]: Данные для графика или None в случае ошибки
        """
        try:
            # Рассчитываем даты
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            params = {
                'from': start_date.strftime("%Y-%m-%dT00:00:00Z"),
                'interval': interval
            }
            
            # Используем эндпоинт для данных графика
            response = await self._make_request(f'currencies/{coin_id}/sparkline', params)
            
            if 'data' in response:
                sparkline_data = response['data']
                logger.info(f"Получены данные для графика монеты {coin_id}")
                return sparkline_data
            else:
                logger.error(f"Неожиданный формат ответа API: {response}")
                return None
        except Exception as e:
            logger.error(f"Ошибка при получении данных для графика монеты {coin_id}: {e}", exc_info=True)
            return None
    
    async def search_coin(self, symbol: Optional[str] = None, address: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Поиск монеты по символу или адресу контракта
        
        Args:
            symbol: Символ монеты
            address: Адрес контракта
            
        Returns:
            List[Dict[str, Any]]: Результаты поиска
        """
        try:
            params = {}
            if symbol:
                params['symbol'] = symbol
            if address:
                params['address'] = address
                
            if not params:
                logger.error("Для поиска необходимо указать symbol или address")
                return []
            
            # Используем эндпоинт для поиска
            response = await self._make_request('currencies/search', params)
            
            if isinstance(response, list):
                search_results = response
                logger.info(f"Найдено {len(search_results)} монет")
                return search_results
            else:
                logger.error(f"Неожиданный формат ответа API: {response}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при поиске монеты: {e}", exc_info=True)
            return []
    
    async def get_exchanges(self, limit: int = 100, offset: int = 0, 
                           exchange_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Получает список бирж
        
        Args:
            limit: Максимальное количество бирж
            offset: Смещение для пагинации
            exchange_type: Тип биржи (CEX, DEX, Futures)
            
        Returns:
            List[Dict[str, Any]]: Список бирж
        """
        try:
            params = {
                'limit': min(limit, 300),  # Максимум 300 по документации
                'skip': offset
            }
            
            if exchange_type:
                params['type'] = exchange_type
            
            # Используем эндпоинт для бирж
            response = await self._make_request('exchanges', params)
            
            if 'data' in response:
                exchanges = response['data']
                logger.info(f"Получено {len(exchanges)} бирж")
                return exchanges
            else:
                logger.error(f"Неожиданный формат ответа API: {response}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении списка бирж: {e}", exc_info=True)
            return []
    
    async def get_markets(self, limit: int = 100, offset: int = 0,
                         base_coin_id: Optional[int] = None,
                         quote_coin_id: Optional[int] = None,
                         exchange_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Получает список торговых пар
        
        Args:
            limit: Максимальное количество пар
            offset: Смещение для пагинации
            base_coin_id: ID базовой монеты
            quote_coin_id: ID котируемой монеты
            exchange_id: ID биржи
            
        Returns:
            List[Dict[str, Any]]: Список торговых пар
        """
        try:
            params = {
                'limit': min(limit, 1000),  # Максимум 1000 по документации
                'skip': offset,
                'sortBy': 'volume24hUSD',
                'sortDirection': 'DESC'
            }
            
            if base_coin_id:
                params['baseCoinId'] = base_coin_id
            if quote_coin_id:
                params['quoteCoinId'] = quote_coin_id
            if exchange_id:
                params['exchangeId'] = exchange_id
            
            # Используем эндпоинт для торговых пар
            response = await self._make_request('markets', params)
            
            if 'data' in response:
                markets = response['data']
                logger.info(f"Получено {len(markets)} торговых пар")
                return markets
            else:
                logger.error(f"Неожиданный формат ответа API: {response}")
                return []
        except Exception as e:
            logger.error(f"Ошибка при получении списка торговых пар: {e}", exc_info=True)
            return []