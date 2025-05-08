"""
Модуль для управления данными о криптовалютах
Объединяет различные источники данных: API, WebSocket, кэш и базу данных
"""

import logging
import asyncio
import numpy as np
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
            # Не обновляем данные сразу при запуске, чтобы не тратить API запросы
            # await self._update_data()
            logger.info("Фоновое обновление данных запущено, первое обновление через 1 час")
            
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
            
            # Используем заглушки вместо API запросов
            coins = await self._get_mock_coins(limit=500)
            
            if coins:
                # Сохраняем данные в базу данных
                await self.db.save_coins(coins)
                
                # Инвалидируем кэш
                self.cache.invalidate("get_coins")
                
                logger.info(f"Обновлены данные о {len(coins)} монетах")
            
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
        
        # Иначе генерируем заглушку для монет
        logger.info(f"Генерация заглушки для {limit} монет")
        return await self._get_mock_coins(limit)
    
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
                market_cap = coin_data["price"] * np.random.uniform(1000000, 10000000000)
                
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
        
        # Получаем историю цен из базы данных
        history = await self.db.get_price_history(coin_id, days)
        
        # Возвращаем историю из базы данных, даже если она неполная
        # Чтобы не тратить API запросы
        if history:
            return history
            
        # Генерируем заглушку для истории цен
        mock_history = []
        current_price = coin.get('price', 1000)
        current_time = datetime.now()
        
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
                'timestamp': (current_time - timedelta(days=i)).isoformat(),
                'price': price,
                'volume': volume,
                'marketCap': market_cap
            })
        
        return mock_history
    
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