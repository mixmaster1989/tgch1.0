"""
Модуль для управления данными о криптовалютах
Объединяет различные источники данных: API, WebSocket, кэш и базу данных
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from .cryptorank_api import CryptorankAPI
from .crypto_database import CryptoDatabase
from .crypto_cache import CryptoCache, get_cache, cached
from .crypto_websocket import CryptoWebSocket, get_websocket

# Получаем логгер для модуля
logger = logging.getLogger('crypto.data_sources.crypto_data_manager')

class CryptoDataManager:
    """
    Класс для управления данными о криптовалютах
    """
    
    def __init__(self):
        """
        Инициализирует менеджер данных
        """
        self.api = CryptorankAPI()
        self.db = CryptoDatabase()
        self.cache = get_cache()
        self.websocket = get_websocket()
        
        # Флаг для управления фоновым обновлением данных
        self._updating = False
        self._update_task = None
        
        logger.info("Инициализирован менеджер данных о криптовалютах")
    
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
    
    async def _update_loop(self):
        """
        Фоновый процесс для обновления данных
        """
        try:
            # Сначала обновляем данные сразу
            await self._update_data()
            
            while self._updating:
                # Ждем 1 час перед следующим обновлением
                await asyncio.sleep(3600)
                
                # Обновляем данные
                await self._update_data()
        except asyncio.CancelledError:
            logger.info("Отменен фоновый процесс обновления данных")
        except Exception as e:
            logger.error(f"Ошибка в фоновом процессе обновления данных: {e}")
    
    async def _update_data(self):
        """
        Обновляет данные из API и сохраняет их в базу данных
        """
        try:
            logger.info("Начало обновления данных из API")
            
            # Получаем данные о монетах из API
            coins = await self.api.get_coins(limit=500)
            
            if coins:
                # Сохраняем данные в базу данных
                await self.db.save_coins(coins)
                
                # Инвалидируем кэш
                self.cache.invalidate("get_coins")
                
                logger.info(f"Обновлены данные о {len(coins)} монетах")
            
            # Получаем рыночные данные из API
            market_data = await self.api.get_market_data()
            
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
    
    @cached(ttl=300)  # Кэшируем на 5 минут
    async def get_coins(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Получает информацию о монетах
        
        Args:
            limit: Максимальное количество монет
            offset: Смещение для пагинации
            
        Returns:
            List[Dict[str, Any]]: Список монет
        """
        # Проверяем свежесть данных
        coins_updated, _ = await self.db.get_data_freshness()
        
        # Если данные свежие (не старше 1 часа), берем из базы данных
        if coins_updated and datetime.now() - coins_updated < timedelta(hours=1):
            logger.info(f"Получение {limit} монет из базы данных")
            return await self.db.get_coins(limit, offset)
        
        # Иначе получаем данные из API
        logger.info(f"Получение {limit} монет из API")
        coins = await self.api.get_coins(limit, offset)
        
        # Если получили данные из API, сохраняем их в базу
        if coins:
            await self.db.save_coins(coins)
        
        return coins
    
    @cached(ttl=300)  # Кэшируем на 5 минут
    async def get_coin_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о монете по символу
        
        Args:
            symbol: Символ монеты
            
        Returns:
            Optional[Dict[str, Any]]: Информация о монете или None
        """
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
            
            return db_data
        
        # Если нет данных в базе, пробуем получить из API
        if not db_data:
            # Ищем монету по символу в API
            coins = await self.api.get_coins(limit=500)
            
            for coin in coins:
                if coin.get('symbol', '').upper() == symbol.upper():
                    # Сохраняем монету в базу данных
                    await self.db.save_coins([coin])
                    return coin
        
        return db_data
    
    @cached(ttl=300)  # Кэшируем на 5 минут
    async def get_market_data(self) -> Optional[Dict[str, Any]]:
        """
        Получает рыночные данные
        
        Returns:
            Optional[Dict[str, Any]]: Рыночные данные или None
        """
        # Проверяем свежесть данных
        _, market_updated = await self.db.get_data_freshness()
        
        # Если данные свежие (не старше 1 часа), берем из базы данных
        if market_updated and datetime.now() - market_updated < timedelta(hours=1):
            logger.info("Получение рыночных данных из базы данных")
            return await self.db.get_latest_market_data()
        
        # Иначе получаем данные из API
        logger.info("Получение рыночных данных из API")
        market_data = await self.api.get_market_data()
        
        # Если получили данные из API, сохраняем их в базу
        if market_data:
            await self.db.save_market_data(market_data)
        
        return market_data
    
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
        
        # Получаем историю цен из базы данных
        history = await self.db.get_price_history(coin_id, days)
        
        # Если история недостаточно полная, получаем из API
        if len(history) < days:
            # Получаем историю из API
            api_history = await self.api.get_coin_historical(coin_id, days=days)
            
            if api_history:
                # Сохраняем историю в базу данных
                # Здесь нужно преобразовать формат данных API в формат базы данных
                # Это зависит от конкретного API и структуры базы данных
                pass
            
            return api_history
        
        return history
    
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

# Создаем глобальный экземпляр менеджера данных
_data_manager = CryptoDataManager()

def get_data_manager() -> CryptoDataManager:
    """
    Получает глобальный экземпляр менеджера данных
    
    Returns:
        CryptoDataManager: Глобальный экземпляр менеджера данных
    """
    return _data_manager