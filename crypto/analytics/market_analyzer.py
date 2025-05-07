"""
Модуль для анализа рыночных данных
"""

import logging
import asyncio
from datetime import datetime
import uuid
from typing import List, Dict, Any, Optional

from ..data_sources.cryptorank_api import CryptorankAPI
from ..models import MarketOverview, CryptoSignal, SignalType, SignalDirection
from ..config import get_config

# Получаем логгер для модуля
logger = logging.getLogger('crypto.analytics.market_analyzer')

class MarketAnalyzer:
    """
    Класс для анализа рыночных данных и генерации сигналов
    """
    
    def __init__(self):
        """
        Инициализирует анализатор рынка
        """
        self.cryptorank_api = CryptorankAPI()
        self.config = get_config()
        logger.info("Инициализирован анализатор рынка")
    
    async def get_market_overview(self) -> Optional[MarketOverview]:
        """
        Получает и анализирует общий обзор рынка
        
        Returns:
            Optional[MarketOverview]: Обзор рынка или None в случае ошибки
        """
        try:
            # Получаем данные о рынке
            market_data = await self.cryptorank_api.get_market_data()
            if not market_data:
                logger.error("Не удалось получить данные о рынке")
                return None
            
            # Получаем топ монет для определения лидеров и аутсайдеров
            coins = await self.cryptorank_api.get_coins(limit=100)
            if not coins:
                logger.error("Не удалось получить данные о монетах")
                return None
            
            # Сортируем монеты по изменению цены за 24 часа
            sorted_coins = sorted(
                coins, 
                key=lambda x: x.get('values', {}).get('USD', {}).get('percentChange24h', 0) or 0, 
                reverse=True
            )
            
            # Получаем топ-5 растущих и падающих монет
            top_gainers = sorted_coins[:5]
            top_losers = sorted_coins[-5:]
            
            # Форматируем данные для топ монет
            formatted_gainers = [
                {
                    'symbol': coin['symbol'],
                    'name': coin['name'],
                    'price': coin.get('values', {}).get('USD', {}).get('price', 0),
                    'change_24h': coin.get('values', {}).get('USD', {}).get('percentChange24h', 0)
                }
                for coin in top_gainers
            ]
            
            formatted_losers = [
                {
                    'symbol': coin['symbol'],
                    'name': coin['name'],
                    'price': coin.get('values', {}).get('USD', {}).get('price', 0),
                    'change_24h': coin.get('values', {}).get('USD', {}).get('percentChange24h', 0)
                }
                for coin in top_losers
            ]
            
            # Создаем обзор рынка
            overview = MarketOverview(
                timestamp=datetime.now(),
                total_market_cap=market_data.get('marketCap', {}).get('USD', 0),
                btc_dominance=market_data.get('btcDominance', 0),
                total_volume_24h=market_data.get('volume24h', {}).get('USD', 0),
                top_gainers=formatted_gainers,
                top_losers=formatted_losers
            )
            
            logger.info("Создан обзор рынка")
            return overview
        except Exception as e:
            logger.error(f"Ошибка при создании обзора рынка: {e}", exc_info=True)
            return None
    
    async def detect_volume_spikes(self) -> List[CryptoSignal]:
        """
        Обнаруживает всплески объема торгов
        
        Returns:
            List[CryptoSignal]: Список сигналов о всплесках объема
        """
        try:
            signals = []
            
            # Получаем настройки для анализа всплесков объема
            threshold = self.config['analytics']['volume_spike']['threshold']
            
            # Получаем данные о монетах
            coins = await self.cryptorank_api.get_coins(limit=50)  # Анализируем топ-50 монет
            if not coins:
                logger.error("Не удалось получить данные о монетах для анализа объема")
                return []
            
            # Анализируем каждую монету
            for coin in coins:
                try:
                    symbol = coin['symbol']
                    name = coin['name']
                    
                    # Получаем данные об объеме
                    volume_24h = coin.get('values', {}).get('USD', {}).get('volume24h', 0)
                    avg_volume_7d = coin.get('values', {}).get('USD', {}).get('averageVolume7d', 0)
                    
                    # Проверяем наличие данных
                    if not volume_24h or not avg_volume_7d:
                        continue
                    
                    # Вычисляем отношение текущего объема к среднему
                    volume_ratio = volume_24h / avg_volume_7d if avg_volume_7d > 0 else 0
                    
                    # Если отношение превышает порог, создаем сигнал
                    if volume_ratio > threshold:
                        # Определяем направление на основе изменения цены
                        price_change = coin.get('values', {}).get('USD', {}).get('percentChange24h', 0)
                        direction = SignalDirection.LONG if price_change > 0 else SignalDirection.SHORT
                        
                        # Создаем сигнал
                        signal = CryptoSignal(
                            id=str(uuid.uuid4()),
                            pair=f"{symbol}/USDT",
                            timestamp=datetime.now(),
                            signal_type=SignalType.VOLUME_SPIKE,
                            direction=direction,
                            price=coin.get('values', {}).get('USD', {}).get('price', 0),
                            confidence=min(volume_ratio / threshold, 1.0),  # Нормализуем уверенность
                            description=f"Обнаружен всплеск объема для {name} ({symbol}). "
                                       f"Текущий объем в {volume_ratio:.2f}x раз выше среднего за 7 дней.",
                            metadata={
                                'volume_24h': volume_24h,
                                'avg_volume_7d': avg_volume_7d,
                                'volume_ratio': volume_ratio,
                                'price_change_24h': price_change
                            }
                        )
                        
                        signals.append(signal)
                        logger.info(f"Создан сигнал о всплеске объема для {symbol}")
                except Exception as e:
                    logger.error(f"Ошибка при анализе монеты {coin.get('symbol', 'Unknown')}: {e}")
                    continue
            
            logger.info(f"Обнаружено {len(signals)} сигналов о всплесках объема")
            return signals
        except Exception as e:
            logger.error(f"Ошибка при обнаружении всплесков объема: {e}", exc_info=True)
            return []