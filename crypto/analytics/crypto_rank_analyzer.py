"""
Модуль для анализа данных с использованием CryptoRank API V2
"""

import logging
import asyncio
from datetime import datetime, timedelta
import uuid
from typing import List, Dict, Any, Optional, Tuple

from ..data_sources.cryptorank_api import CryptorankAPI
from ..models import MarketOverview, CryptoSignal, SignalType, SignalDirection
from ..config import get_config

# Получаем логгер для модуля
logger = logging.getLogger('crypto.analytics.crypto_rank_analyzer')

class CryptoRankAnalyzer:
    """
    Класс для анализа данных с использованием CryptoRank API V2
    """
    
    def __init__(self):
        """
        Инициализирует анализатор данных CryptoRank
        """
        self.cryptorank_api = CryptorankAPI()
        self.config = get_config()
        logger.info("Инициализирован анализатор данных CryptoRank")
    
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
            coins = await self.cryptorank_api.get_coins(limit=100, include_percent_change=True)
            if not coins:
                logger.error("Не удалось получить данные о монетах")
                return None
            
            # Сортируем монеты по изменению цены за 24 часа
            # Адаптируем к структуре данных API V2
            sorted_coins = sorted(
                coins, 
                key=lambda x: float(x.get('percentChange', {}).get('h24', '0') or '0'), 
                reverse=True
            )
            
            # Получаем топ-5 растущих и падающих монет
            top_gainers = sorted_coins[:5]
            top_losers = sorted_coins[-5:]
            
            # Форматируем данные для топ монет с учетом структуры данных API V2
            formatted_gainers = [
                {
                    'symbol': coin.get('symbol', ''),
                    'name': coin.get('name', ''),
                    'price': float(coin.get('price', '0') or '0'),
                    'change_24h': float(coin.get('percentChange', {}).get('h24', '0') or '0')
                }
                for coin in top_gainers
            ]
            
            formatted_losers = [
                {
                    'symbol': coin.get('symbol', ''),
                    'name': coin.get('name', ''),
                    'price': float(coin.get('price', '0') or '0'),
                    'change_24h': float(coin.get('percentChange', {}).get('h24', '0') or '0')
                }
                for coin in reversed(top_losers)  # Переворачиваем, чтобы показать от худшего к лучшему
            ]
            
            # Создаем обзор рынка с учетом структуры данных API V2
            overview = MarketOverview(
                timestamp=datetime.now(),
                total_market_cap=float(market_data.get('totalMarketCap', '0') or '0'),
                btc_dominance=float(market_data.get('btcDominance', '0') or '0'),
                total_volume_24h=float(market_data.get('totalVolume24h', '0') or '0'),
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
            coins = await self.cryptorank_api.get_coins(limit=50, include_percent_change=True)
            if not coins:
                logger.error("Не удалось получить данные о монетах для анализа объема")
                return []
            
            # Анализируем каждую монету с учетом структуры данных API V2
            for coin in coins:
                try:
                    symbol = coin.get('symbol', '')
                    name = coin.get('name', '')
                    
                    # Получаем данные об объеме с учетом новой структуры
                    volume_24h = float(coin.get('volume24h', '0') or '0')
                    
                    # Получаем исторические данные для расчета среднего объема за 7 дней
                    coin_id = coin.get('id')
                    if not coin_id:
                        continue
                    
                    # Рассчитываем даты для исторических данных
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=8)  # Берем 8 дней для расчета среднего за 7 дней
                    
                    # Получаем исторические данные
                    historical_data = await self.cryptorank_api.get_coin_historical(
                        coin_id=coin_id,
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d"),
                        interval="day",
                        limit=8
                    )
                    
                    if not historical_data or len(historical_data) < 7:
                        # Если нет достаточно исторических данных, используем приближение
                        avg_volume_7d = volume_24h / 1.5
                    else:
                        # Рассчитываем средний объем за 7 дней (исключая текущий день)
                        volumes = [float(item.get('volume', '0') or '0') for item in historical_data[1:]]
                        avg_volume_7d = sum(volumes) / len(volumes) if volumes else volume_24h / 1.5
                    
                    # Проверяем наличие данных
                    if not volume_24h or not avg_volume_7d:
                        continue
                    
                    # Вычисляем отношение текущего объема к среднему
                    volume_ratio = volume_24h / avg_volume_7d if avg_volume_7d > 0 else 0
                    
                    # Если отношение превышает порог, создаем сигнал
                    if volume_ratio > threshold:
                        # Определяем направление на основе изменения цены
                        price_change = float(coin.get('percentChange', {}).get('h24', '0') or '0')
                        direction = SignalDirection.LONG if price_change > 0 else SignalDirection.SHORT
                        
                        # Создаем сигнал
                        signal = CryptoSignal(
                            id=str(uuid.uuid4()),
                            pair=f"{symbol}/USDT",
                            timestamp=datetime.now(),
                            signal_type=SignalType.VOLUME_SPIKE,
                            direction=direction,
                            price=float(coin.get('price', '0') or '0'),
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
    
    async def detect_price_breakouts(self) -> List[CryptoSignal]:
        """
        Обнаруживает прорывы цены
        
        Returns:
            List[CryptoSignal]: Список сигналов о прорывах цены
        """
        try:
            signals = []
            
            # Получаем настройки для анализа прорывов цены
            threshold_percent = self.config['analytics']['price_breakout']['threshold_percent']
            
            # Получаем данные о монетах
            coins = await self.cryptorank_api.get_coins(limit=50, include_percent_change=True)
            if not coins:
                logger.error("Не удалось получить данные о монетах для анализа прорывов цены")
                return []
            
            # Анализируем каждую монету
            for coin in coins:
                try:
                    symbol = coin.get('symbol', '')
                    name = coin.get('name', '')
                    coin_id = coin.get('id')
                    
                    if not coin_id:
                        continue
                    
                    # Получаем текущую цену
                    current_price = float(coin.get('price', '0') or '0')
                    if not current_price:
                        continue
                    
                    # Получаем исторические данные для определения уровней поддержки и сопротивления
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=30)  # Анализируем данные за 30 дней
                    
                    historical_data = await self.cryptorank_api.get_coin_historical(
                        coin_id=coin_id,
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d"),
                        interval="day",
                        limit=30
                    )
                    
                    if not historical_data or len(historical_data) < 7:
                        continue
                    
                    # Находим максимумы и минимумы за последние 7 дней (исключая текущий день)
                    recent_data = historical_data[:7]
                    highs = [float(item.get('high', '0') or '0') for item in recent_data]
                    lows = [float(item.get('low', '0') or '0') for item in recent_data]
                    
                    resistance_level = max(highs) if highs else 0
                    support_level = min(lows) if lows else 0
                    
                    if not resistance_level or not support_level:
                        continue
                    
                    # Проверяем прорыв уровня сопротивления
                    resistance_breakout = current_price > resistance_level * (1 + threshold_percent / 100)
                    
                    # Проверяем прорыв уровня поддержки (вниз)
                    support_breakout = current_price < support_level * (1 - threshold_percent / 100)
                    
                    if resistance_breakout or support_breakout:
                        # Определяем направление сигнала
                        direction = SignalDirection.LONG if resistance_breakout else SignalDirection.SHORT
                        breakout_type = "сопротивления" if resistance_breakout else "поддержки"
                        breakout_level = resistance_level if resistance_breakout else support_level
                        
                        # Рассчитываем процент прорыва
                        breakout_percent = abs((current_price - breakout_level) / breakout_level * 100)
                        
                        # Создаем сигнал
                        signal = CryptoSignal(
                            id=str(uuid.uuid4()),
                            pair=f"{symbol}/USDT",
                            timestamp=datetime.now(),
                            signal_type=SignalType.PRICE_BREAKOUT,
                            direction=direction,
                            price=current_price,
                            confidence=min(breakout_percent / threshold_percent, 1.0),  # Нормализуем уверенность
                            description=f"Обнаружен прорыв уровня {breakout_type} для {name} ({symbol}). "
                                       f"Текущая цена: {current_price:.4f}, уровень {breakout_type}: {breakout_level:.4f}, "
                                       f"прорыв: {breakout_percent:.2f}%",
                            metadata={
                                'current_price': current_price,
                                'breakout_level': breakout_level,
                                'breakout_percent': breakout_percent,
                                'breakout_type': breakout_type
                            }
                        )
                        
                        signals.append(signal)
                        logger.info(f"Создан сигнал о прорыве цены для {symbol}")
                except Exception as e:
                    logger.error(f"Ошибка при анализе прорывов цены для {coin.get('symbol', 'Unknown')}: {e}")
                    continue
            
            logger.info(f"Обнаружено {len(signals)} сигналов о прорывах цены")
            return signals
        except Exception as e:
            logger.error(f"Ошибка при обнаружении прорывов цены: {e}", exc_info=True)
            return []
    
    async def analyze_token_unlocks(self, days_ahead: int = 7) -> List[Dict[str, Any]]:
        """
        Анализирует предстоящие разблокировки токенов
        
        Args:
            days_ahead: Количество дней вперед для анализа
            
        Returns:
            List[Dict[str, Any]]: Список предстоящих разблокировок
        """
        try:
            # Получаем данные о предстоящих разблокировках
            token_unlocks = await self.cryptorank_api.get_coins(
                limit=100,
                sort_by="nextUnlockDate"
            )
            
            if not token_unlocks:
                logger.error("Не удалось получить данные о разблокировках токенов")
                return []
            
            # Фильтруем разблокировки, которые произойдут в ближайшие дни
            upcoming_unlocks = []
            current_time = datetime.now().timestamp()
            future_time = (datetime.now() + timedelta(days=days_ahead)).timestamp()
            
            for token in token_unlocks:
                try:
                    # Проверяем наличие данных о следующей разблокировке
                    next_unlock = token.get('nextUnlock')
                    if not next_unlock:
                        continue
                    
                    unlock_date = next_unlock.get('date')
                    if not unlock_date:
                        continue
                    
                    # Проверяем, что разблокировка произойдет в заданный период
                    if current_time <= unlock_date <= future_time:
                        # Форматируем данные о разблокировке
                        unlock_info = {
                            'id': token.get('id'),
                            'symbol': token.get('symbol', ''),
                            'name': token.get('name', ''),
                            'unlock_date': datetime.fromtimestamp(unlock_date).strftime("%Y-%m-%d %H:%M:%S"),
                            'unlock_tokens': next_unlock.get('tokens', '0'),
                            'unlock_percent_of_supply': token.get('nextUnlockOfSupply', '0'),
                            'unlock_percent_of_circulating': token.get('nextUnlockOfCirculating', '0'),
                            'price': token.get('price', '0'),
                            'market_cap': token.get('marketCap', '0')
                        }
                        
                        upcoming_unlocks.append(unlock_info)
                except Exception as e:
                    logger.error(f"Ошибка при анализе разблокировки для {token.get('symbol', 'Unknown')}: {e}")
                    continue
            
            # Сортируем по дате разблокировки
            upcoming_unlocks.sort(key=lambda x: x['unlock_date'])
            
            logger.info(f"Обнаружено {len(upcoming_unlocks)} предстоящих разблокировок токенов")
            return upcoming_unlocks
        except Exception as e:
            logger.error(f"Ошибка при анализе разблокировок токенов: {e}", exc_info=True)
            return []
    
    async def analyze_market_sentiment(self) -> Dict[str, Any]:
        """
        Анализирует настроение рынка на основе различных метрик
        
        Returns:
            Dict[str, Any]: Данные о настроении рынка
        """
        try:
            # Получаем общие данные о рынке
            market_data = await self.cryptorank_api.get_market_data()
            if not market_data:
                logger.error("Не удалось получить данные о рынке")
                return {}
            
            # Получаем топ монеты для анализа
            coins = await self.cryptorank_api.get_coins(limit=100, include_percent_change=True)
            if not coins:
                logger.error("Не удалось получить данные о монетах")
                return {}
            
            # Анализируем изменения цен за разные периоды
            changes_24h = [float(coin.get('percentChange', {}).get('h24', '0') or '0') for coin in coins]
            changes_7d = [float(coin.get('percentChange', {}).get('d7', '0') or '0') for coin in coins]
            changes_30d = [float(coin.get('percentChange', {}).get('d30', '0') or '0') for coin in coins]
            
            # Рассчитываем средние изменения
            avg_change_24h = sum(changes_24h) / len(changes_24h) if changes_24h else 0
            avg_change_7d = sum(changes_7d) / len(changes_7d) if changes_7d else 0
            avg_change_30d = sum(changes_30d) / len(changes_30d) if changes_30d else 0
            
            # Рассчитываем процент монет с положительной динамикой
            positive_24h = sum(1 for change in changes_24h if change > 0)
            positive_7d = sum(1 for change in changes_7d if change > 0)
            positive_30d = sum(1 for change in changes_30d if change > 0)
            
            percent_positive_24h = positive_24h / len(changes_24h) * 100 if changes_24h else 0
            percent_positive_7d = positive_7d / len(changes_7d) * 100 if changes_7d else 0
            percent_positive_30d = positive_30d / len(changes_30d) * 100 if changes_30d else 0
            
            # Определяем настроение рынка
            sentiment_24h = self._determine_sentiment(avg_change_24h, percent_positive_24h)
            sentiment_7d = self._determine_sentiment(avg_change_7d, percent_positive_7d)
            sentiment_30d = self._determine_sentiment(avg_change_30d, percent_positive_30d)
            
            # Формируем результат
            sentiment_data = {
                'timestamp': datetime.now().isoformat(),
                'btc_dominance': float(market_data.get('btcDominance', '0') or '0'),
                'total_market_cap': float(market_data.get('totalMarketCap', '0') or '0'),
                'total_volume_24h': float(market_data.get('totalVolume24h', '0') or '0'),
                'investment_activity': float(market_data.get('investmentActivity', '0') or '0'),
                'average_changes': {
                    '24h': avg_change_24h,
                    '7d': avg_change_7d,
                    '30d': avg_change_30d
                },
                'percent_positive': {
                    '24h': percent_positive_24h,
                    '7d': percent_positive_7d,
                    '30d': percent_positive_30d
                },
                'sentiment': {
                    '24h': sentiment_24h,
                    '7d': sentiment_7d,
                    '30d': sentiment_30d
                },
                'overall_sentiment': self._calculate_overall_sentiment(sentiment_24h, sentiment_7d, sentiment_30d)
            }
            
            logger.info("Создан анализ настроения рынка")
            return sentiment_data
        except Exception as e:
            logger.error(f"Ошибка при анализе настроения рынка: {e}", exc_info=True)
            return {}
    
    def _determine_sentiment(self, avg_change: float, percent_positive: float) -> str:
        """
        Определяет настроение рынка на основе средних изменений и процента положительных изменений
        
        Args:
            avg_change: Среднее изменение цены
            percent_positive: Процент монет с положительной динамикой
            
        Returns:
            str: Настроение рынка (Крайне негативное, Негативное, Нейтральное, Позитивное, Крайне позитивное)
        """
        if avg_change < -5 and percent_positive < 30:
            return "Крайне негативное"
        elif avg_change < -2 and percent_positive < 45:
            return "Негативное"
        elif -2 <= avg_change <= 2 and 40 <= percent_positive <= 60:
            return "Нейтральное"
        elif avg_change > 2 and percent_positive > 55:
            return "Позитивное"
        elif avg_change > 5 and percent_positive > 70:
            return "Крайне позитивное"
        else:
            return "Нейтральное"
    
    def _calculate_overall_sentiment(self, sentiment_24h: str, sentiment_7d: str, sentiment_30d: str) -> str:
        """
        Рассчитывает общее настроение рынка на основе настроений за разные периоды
        
        Args:
            sentiment_24h: Настроение за 24 часа
            sentiment_7d: Настроение за 7 дней
            sentiment_30d: Настроение за 30 дней
            
        Returns:
            str: Общее настроение рынка
        """
        # Преобразуем настроения в числовые значения
        sentiment_map = {
            "Крайне негативное": -2,
            "Негативное": -1,
            "Нейтральное": 0,
            "Позитивное": 1,
            "Крайне позитивное": 2
        }
        
        # Рассчитываем взвешенное среднее (больший вес для более коротких периодов)
        weighted_sentiment = (
            sentiment_map.get(sentiment_24h, 0) * 0.5 +
            sentiment_map.get(sentiment_7d, 0) * 0.3 +
            sentiment_map.get(sentiment_30d, 0) * 0.2
        )
        
        # Преобразуем обратно в текстовое представление
        if weighted_sentiment <= -1.5:
            return "Крайне негативное"
        elif -1.5 < weighted_sentiment <= -0.5:
            return "Негативное"
        elif -0.5 < weighted_sentiment < 0.5:
            return "Нейтральное"
        elif 0.5 <= weighted_sentiment < 1.5:
            return "Позитивное"
        else:
            return "Крайне позитивное"