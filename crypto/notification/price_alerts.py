"""
Модуль для отслеживания и уведомления о важных ценовых событиях
"""

import logging
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set

from ..models import CryptoSignal, SignalType, SignalDirection
from ..data_sources.cryptorank_api import CryptorankAPI
from ..config import get_config
from ..user_settings.user_preferences import UserPreferences

# Получаем логгер для модуля
logger = logging.getLogger('crypto.notification.price_alerts')

class PriceAlertManager:
    """
    Класс для управления уведомлениями о ценовых событиях
    """
    
    def __init__(self):
        """
        Инициализирует менеджер ценовых уведомлений
        """
        config = get_config()
        api_key = config.cryptorank.api_key
        self.cryptorank_api = CryptorankAPI(api_key)
        self.config = config
        self.user_preferences = UserPreferences()
        
        # Для отслеживания последних цен и объемов
        self.last_prices = {}  # pair -> price
        self.last_volumes = {}  # pair -> volume
        self.last_check_time = datetime.now()
        
        # Для отслеживания психологических уровней
        self.psychological_levels = {}  # pair -> [levels]
        self.triggered_levels = set()  # set of (pair, level) tuples
        
        logger.info("Инициализирован менеджер ценовых уведомлений")
    
    async def update_market_data(self):
        """
        Обновляет данные о рынке для отслеживания
        """
        try:
            # Получаем список монет для отслеживания
            user_coins = await self.user_preferences.get_user_watched_coins()
            if not user_coins:
                logger.debug("Нет монет для отслеживания")
                return
            
            # Получаем данные о монетах
            coins = await self.cryptorank_api.get_coins(limit=200)
            if not coins:
                logger.error("Не удалось получить данные о монетах")
                return
            
            # Обновляем данные о ценах и объемах
            current_time = datetime.now()
            for coin in coins:
                symbol = coin.get('symbol', '')
                if symbol in user_coins:
                    pair = f"{symbol}/USDT"
                    
                    # Обновляем цену
                    current_price = float(coin.get('price', '0') or '0')
                    old_price = self.last_prices.get(pair, current_price)
                    self.last_prices[pair] = current_price
                    
                    # Обновляем объем
                    current_volume = float(coin.get('volume24h', '0') or '0')
                    old_volume = self.last_volumes.get(pair, current_volume)
                    self.last_volumes[pair] = current_volume
                    
                    # Обновляем психологические уровни
                    if pair not in self.psychological_levels:
                        self.psychological_levels[pair] = self._generate_psychological_levels(current_price)
            
            self.last_check_time = current_time
            logger.info(f"Обновлены данные о рынке для {len(user_coins)} монет")
        except Exception as e:
            logger.error(f"Ошибка при обновлении данных о рынке: {e}", exc_info=True)
    
    def _generate_psychological_levels(self, current_price: float) -> List[float]:
        """
        Генерирует психологические уровни цены на основе текущей цены
        
        Args:
            current_price: Текущая цена
            
        Returns:
            List[float]: Список психологических уровней
        """
        levels = []
        
        # Определяем порядок цены
        if current_price >= 1:
            # Для цен >= 1 используем круглые числа
            magnitude = 10 ** int(len(str(int(current_price))) - 1)
            
            # Добавляем уровни выше текущей цены
            for i in range(1, 6):
                level = ((int(current_price / magnitude) + i) * magnitude)
                levels.append(level)
            
            # Добавляем уровни ниже текущей цены
            for i in range(0, 5):
                level = ((int(current_price / magnitude) - i) * magnitude)
                if level > 0:
                    levels.append(level)
        else:
            # Для цен < 1 используем степени 10
            decimals = 0
            temp_price = current_price
            while temp_price < 1:
                temp_price *= 10
                decimals += 1
            
            # Добавляем уровни для маленьких цен
            for i in range(-5, 6):
                if i == 0:
                    continue
                level = 10 ** (-decimals + i)
                if level > 0 and level < 1:
                    levels.append(level)
        
        return sorted(levels)
    
    async def check_price_changes(self) -> List[CryptoSignal]:
        """
        Проверяет значительные изменения цены
        
        Returns:
            List[CryptoSignal]: Список сигналов о значительных изменениях цены
        """
        signals = []
        
        try:
            # Получаем настройки для отслеживания изменений цены
            threshold_percent = self.config['notification']['price_change']['threshold_percent']
            time_window_minutes = self.config['notification']['price_change']['time_window_minutes']
            
            # Проверяем, прошло ли достаточно времени с последней проверки
            time_diff = (datetime.now() - self.last_check_time).total_seconds() / 60
            if time_diff < time_window_minutes:
                return []
            
            # Получаем данные о монетах
            coins = await self.cryptorank_api.get_coins(limit=200)
            if not coins:
                logger.error("Не удалось получить данные о монетах для проверки изменений цены")
                return []
            
            # Получаем список монет для отслеживания
            user_coins = await self.user_preferences.get_user_watched_coins()
            if not user_coins:
                return []
            
            # Проверяем изменения цены
            for coin in coins:
                symbol = coin.get('symbol', '')
                if symbol in user_coins:
                    pair = f"{symbol}/USDT"
                    
                    # Получаем текущую цену
                    current_price = float(coin.get('price', '0') or '0')
                    old_price = self.last_prices.get(pair)
                    
                    # Если у нас есть предыдущая цена, проверяем изменение
                    if old_price:
                        price_change_percent = ((current_price - old_price) / old_price) * 100
                        
                        # Если изменение превышает порог, создаем сигнал
                        if abs(price_change_percent) >= threshold_percent:
                            direction = SignalDirection.LONG if price_change_percent > 0 else SignalDirection.SHORT
                            
                            signal = CryptoSignal(
                                id=str(uuid.uuid4()),
                                pair=pair,
                                timestamp=datetime.now(),
                                signal_type=SignalType.VOLUME_SPIKE,  # Используем существующий тип
                                direction=direction,
                                price=current_price,
                                confidence=min(abs(price_change_percent) / threshold_percent, 1.0),
                                description=f"Значительное изменение цены для {symbol}: {price_change_percent:.2f}% за {time_diff:.1f} минут.",
                                metadata={
                                    'old_price': old_price,
                                    'current_price': current_price,
                                    'price_change_percent': price_change_percent,
                                    'time_window_minutes': time_diff
                                }
                            )
                            
                            signals.append(signal)
                            logger.info(f"Создан сигнал о значительном изменении цены для {symbol}")
            
            logger.info(f"Обнаружено {len(signals)} сигналов о значительных изменениях цены")
            return signals
        except Exception as e:
            logger.error(f"Ошибка при проверке изменений цены: {e}", exc_info=True)
            return []
    
    async def check_psychological_levels(self) -> List[CryptoSignal]:
        """
        Проверяет достижение психологических уровней цены
        
        Returns:
            List[CryptoSignal]: Список сигналов о достижении психологических уровней
        """
        signals = []
        
        try:
            # Получаем данные о монетах
            coins = await self.cryptorank_api.get_coins(limit=200)
            if not coins:
                logger.error("Не удалось получить данные о монетах для проверки психологических уровней")
                return []
            
            # Получаем список монет для отслеживания
            user_coins = await self.user_preferences.get_user_watched_coins()
            if not user_coins:
                return []
            
            # Проверяем достижение психологических уровней
            for coin in coins:
                symbol = coin.get('symbol', '')
                if symbol in user_coins:
                    pair = f"{symbol}/USDT"
                    
                    # Получаем текущую цену
                    current_price = float(coin.get('price', '0') or '0')
                    
                    # Проверяем, есть ли психологические уровни для этой пары
                    if pair not in self.psychological_levels:
                        self.psychological_levels[pair] = self._generate_psychological_levels(current_price)
                    
                    # Проверяем каждый уровень
                    for level in self.psychological_levels[pair]:
                        # Проверяем, находится ли цена в пределах 1% от уровня
                        level_proximity = abs(current_price - level) / level
                        
                        if level_proximity <= 0.01:
                            # Проверяем, не было ли уже уведомления об этом уровне
                            level_key = (pair, level)
                            if level_key not in self.triggered_levels:
                                # Определяем направление
                                old_price = self.last_prices.get(pair, current_price)
                                direction = SignalDirection.LONG if current_price > old_price else SignalDirection.SHORT
                                
                                # Создаем сигнал
                                signal = CryptoSignal(
                                    id=str(uuid.uuid4()),
                                    pair=pair,
                                    timestamp=datetime.now(),
                                    signal_type=SignalType.VOLUME_SPIKE,  # Используем существующий тип
                                    direction=direction,
                                    price=current_price,
                                    confidence=1.0 - level_proximity,  # Чем ближе к уровню, тем выше уверенность
                                    description=f"{symbol} достиг психологического уровня {level:.4f}.",
                                    metadata={
                                        'level': level,
                                        'proximity': level_proximity
                                    }
                                )
                                
                                signals.append(signal)
                                self.triggered_levels.add(level_key)
                                logger.info(f"Создан сигнал о достижении психологического уровня для {symbol}")
            
            # Очищаем старые триггеры через 24 часа
            if len(self.triggered_levels) > 100:  # Ограничиваем размер множества
                self.triggered_levels = set()
            
            logger.info(f"Обнаружено {len(signals)} сигналов о достижении психологических уровней")
            return signals
        except Exception as e:
            logger.error(f"Ошибка при проверке психологических уровней: {e}", exc_info=True)
            return []
    
    async def check_volume_spikes(self) -> List[CryptoSignal]:
        """
        Проверяет необычные всплески объема торгов
        
        Returns:
            List[CryptoSignal]: Список сигналов о всплесках объема
        """
        signals = []
        
        try:
            # Получаем настройки для отслеживания всплесков объема
            threshold = self.config['notification']['volume_spike']['threshold']
            
            # Получаем данные о монетах
            coins = await self.cryptorank_api.get_coins(limit=200)
            if not coins:
                logger.error("Не удалось получить данные о монетах для проверки всплесков объема")
                return []
            
            # Получаем список монет для отслеживания
            user_coins = await self.user_preferences.get_user_watched_coins()
            if not user_coins:
                return []
            
            # Проверяем всплески объема
            for coin in coins:
                symbol = coin.get('symbol', '')
                if symbol in user_coins:
                    pair = f"{symbol}/USDT"
                    
                    # Получаем текущий объем
                    current_volume = float(coin.get('volume24h', '0') or '0')
                    old_volume = self.last_volumes.get(pair)
                    
                    # Если у нас есть предыдущий объем, проверяем изменение
                    if old_volume and old_volume > 0:
                        volume_ratio = current_volume / old_volume
                        
                        # Если отношение превышает порог, создаем сигнал
                        if volume_ratio > threshold:
                            # Определяем направление на основе изменения цены
                            price_change = float(coin.get('percentChange', {}).get('h24', '0') or '0')
                            direction = SignalDirection.LONG if price_change > 0 else SignalDirection.SHORT
                            
                            # Создаем сигнал
                            signal = CryptoSignal(
                                id=str(uuid.uuid4()),
                                pair=pair,
                                timestamp=datetime.now(),
                                signal_type=SignalType.VOLUME_SPIKE,
                                direction=direction,
                                price=float(coin.get('price', '0') or '0'),
                                confidence=min(volume_ratio / threshold, 1.0),
                                description=f"Необычный всплеск объема для {symbol}. Текущий объем в {volume_ratio:.2f}x раз выше предыдущего.",
                                metadata={
                                    'current_volume': current_volume,
                                    'old_volume': old_volume,
                                    'volume_ratio': volume_ratio
                                }
                            )
                            
                            signals.append(signal)
                            logger.info(f"Создан сигнал о всплеске объема для {symbol}")
            
            logger.info(f"Обнаружено {len(signals)} сигналов о всплесках объема")
            return signals
        except Exception as e:
            logger.error(f"Ошибка при проверке всплесков объема: {e}", exc_info=True)
            return []
    
    async def get_all_alerts(self) -> List[CryptoSignal]:
        """
        Получает все уведомления о важных событиях
        
        Returns:
            List[CryptoSignal]: Список всех сигналов
        """
        # Обновляем данные о рынке
        await self.update_market_data()
        
        # Получаем все типы сигналов
        price_signals = await self.check_price_changes()
        level_signals = await self.check_psychological_levels()
        volume_signals = await self.check_volume_spikes()
        
        # Объединяем все сигналы
        all_signals = price_signals + level_signals + volume_signals
        
        return all_signals