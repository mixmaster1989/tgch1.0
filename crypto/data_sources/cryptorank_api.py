"""
Модуль для работы с API Cryptorank
"""

import aiohttp
import logging
import time
from typing import Dict, List, Any, Optional
import asyncio

from ..config import get_cryptorank_api_key, get_config

# Получаем логгер для модуля
logger = logging.getLogger('crypto.data_sources.cryptorank')

class CryptorankAPI:
    """
    Класс для работы с API Cryptorank
    """
    
    def __init__(self):
        """
        Инициализирует клиент API Cryptorank
        """
        config = get_config()
        self.api_key = get_cryptorank_api_key()
        self.base_url = config['api']['cryptorank']['base_url']
        self.rate_limit = config['api']['cryptorank']['rate_limit']
        
        # Для отслеживания запросов и соблюдения rate limit
        self.last_request_time = 0
        self.requests_in_current_minute = 0
        
        logger.info("Инициализирован клиент API Cryptorank")
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Выполняет запрос к API с учетом rate limit
        
        Args:
            endpoint: Конечная точка API
            params: Параметры запроса
            
        Returns:
            Dict[str, Any]: Ответ API в формате JSON
        """
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
        
        # Добавляем API ключ
        params['api_key'] = self.api_key
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    # Увеличиваем счетчик запросов
                    self.requests_in_current_minute += 1
                    self.last_request_time = time.time()
                    
                    # Проверяем статус ответа
                    if response.status == 200:
                        data = await response.json()
                        return data
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
    
    async def get_coins(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Получает список криптовалют
        
        Args:
            limit: Максимальное количество монет
            offset: Смещение для пагинации
            
        Returns:
            List[Dict[str, Any]]: Список монет
        """
        try:
            params = {
                'limit': limit,
                'offset': offset
            }
            
            response = await self._make_request('coins', params)
            
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
    
    async def get_coin_details(self, coin_id: str) -> Optional[Dict[str, Any]]:
        """
        Получает детальную информацию о монете
        
        Args:
            coin_id: Идентификатор монеты
            
        Returns:
            Optional[Dict[str, Any]]: Информация о монете или None в случае ошибки
        """
        try:
            response = await self._make_request(f'coins/{coin_id}')
            
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
    
    async def get_market_data(self) -> Optional[Dict[str, Any]]:
        """
        Получает общие данные о рынке
        
        Returns:
            Optional[Dict[str, Any]]: Данные о рынке или None в случае ошибки
        """
        try:
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