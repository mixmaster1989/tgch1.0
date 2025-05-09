"""
Модуль для анализа Smart Money сигналов
"""

import logging
import asyncio
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import yaml
from pathlib import Path

from ..models import CryptoSignal, SignalType, SignalDirection
from ..data_sources.crypto_data_manager import get_data_manager
from ..data_sources.crypto_cache import cached

# Получаем логгер для модуля
logger = logging.getLogger('crypto.analytics.smart_money_analyzer')

# Импортируем Santiment API
from .santiment_api import SantimentAPI


class SmartMoneyAnalyzer:
    """
    Класс для анализа сигналов Smart Money
    """
    
    def __init__(self, data_manager: CryptoDataManager, config_path: str = None):
        """
        Инициализирует анализатор Smart Money
        
        Args:
            data_manager: Менеджер данных
            config_path: Путь к файлу конфигурации
        """
        self.data_manager = data_manager
        self.config = self._load_config(config_path)
        self._last_signals = {}  # Для отслеживания времени последнего сигнала для каждой пары
        
        logger.info("Инициализирован анализатор Smart Money")
    
    def _load_config(self, config_path: str = None) -> Dict[str, Any]:
        """
        Загружает конфигурацию Smart Money
        
        Args:
            config_path: Путь к файлу конфигурации
            
        Returns:
            Dict[str, Any]: Конфигурация
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "smart_money_config.yaml"
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Понижаем пороги для генерации большего количества сигналов
            if 'analytics' in config:
                if 'volume_spike' in config['analytics']:
                    config['analytics']['volume_spike']['threshold'] = 1.1  # Было 1.5
                
                if 'large_orders' in config['analytics']:
                    config['analytics']['large_orders']['min_order_size_btc'] = 1.0  # Было 10.0
                    config['analytics']['large_orders']['imbalance_threshold'] = 1.2  # Было 1.5
                
                if 'funding_rate' in config['analytics']:
                    config['analytics']['funding_rate']['alert_threshold'] = 0.01  # Было 0.05
            
            logger.info(f"Загружена конфигурация Smart Money из {config_path} с пониженными порогами")
            return config
        except Exception as e:
            logger.error(f"Ошибка при загрузке конфигурации Smart Money: {e}")
            # Возвращаем конфигурацию по умолчанию с пониженными порогами
            return {
                "analytics": {
                    "volume_spike": {
                        "threshold": 1.1,  # Было 1.5
                        "ma_period": 24
                    },
                    "large_orders": {
                        "min_order_size_btc": 1.0,  # Было 10.0
                        "imbalance_threshold": 1.2  # Было 1.5
                    },
                    "funding_rate": {
                        "alert_threshold": 0.01,  # Было 0.05
                        "check_interval": 5
                    }
                },
                "notification": {
                    "max_signals_per_hour": 20,  # Было 10
                    "cooldown_per_pair": 60,  # Было 300
                    "whitelist_pairs": [
                        "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", 
                        "ADA/USDT", "DOGE/USDT", "DOT/USDT", "AVAX/USDT", "MATIC/USDT",
                        "LINK/USDT", "UNI/USDT", "ATOM/USDT", "LTC/USDT", "SHIB/USDT"
                    ]
                }
            }
    
    async def analyze_volume_spikes(self, pair: str, threshold: float = 3.0) -> Optional[CryptoSignal]:
        """
        Анализирует всплески объема торгов для конкретной пары
        
        Args:
            pair: Торговая пара
            threshold: Пороговое значение для обнаружения аномалий (в стандартных отклонениях)
            
        Returns:
            Optional[CryptoSignal]: Сигнал с информацией о всплеске объема или None
        """
        symbol = pair.split('/')[0]
        
        # Проверяем, не было ли недавно сигнала для этой пары
        cooldown = self.config["notification"]["cooldown_per_pair"]
        if self._is_on_cooldown(pair, "volume_spike", cooldown):
            return None
        
        # Получаем данные о монете
        coin_data = await self.data_manager.get_coin_by_symbol(symbol)
        
        if not coin_data:
            return None
        
        # Получаем историю цен
        price_history = await self.data_manager.get_price_history(symbol, days=30)
        
        if not price_history:
            return None
        
        # Вычисляем средний объем за последние 30 дней
        volumes = [entry['volume'] for entry in price_history]
        avg_volume = np.mean(volumes)
        std_volume = np.std(volumes)
        
        # Текущий объем
        current_volume = coin_data.get('volume24h', 0)
        
        # Проверяем, не слишком ли мал текущий объем
        if avg_volume == 0 or current_volume < 1000:  # Минимальный объем для анализа
            return None
        
        # Вычисляем z-оценку для текущего объема
        z_score = (current_volume - avg_volume) / std_volume
        
        # Генерируем сигнал только если z-оценка превышает порог
        if z_score > threshold:
            # Рассчитываем процентное изменение цены за последние 24 часа
            price_change_24h = coin_data.get('price_change_percent_24h', 0)
            
            # Рассчитываем отношение объема к изменению цены
            volume_to_price_ratio = abs(current_volume) / max(abs(price_change_24h), 0.1)  # Избегаем деления на ноль
            
            # Получаем дополнительные метрики из Santiment
            dev_activity_trend = coin_data.get('dev_activity_trend', 'neutral')
            social_volume_trend = coin_data.get('social_volume_trend', 'neutral')
            exchange_flows_trend = coin_data.get('exchange_flows_trend', 'neutral')
            network_growth_trend = coin_data.get('network_growth_trend', 'neutral')
            
            # Определяем силу сигнала на основе тенденций из Santiment
            strength = 1.0
            
            # Увеличиваем силу сигнала, если тенденции положительны
            if dev_activity_trend == 'positive':
                strength += 0.3
            elif dev_activity_trend == 'negative':
                strength -= 0.3
                
            if social_volume_trend == 'positive':
                strength += 0.4
            elif social_volume_trend == 'negative':
                strength -= 0.4
                
            if exchange_flows_trend == 'positive':
                strength += 0.2
            elif exchange_flows_trend == 'negative':
                strength -= 0.2
                
            if network_growth_trend == 'positive':
                strength += 0.3
            elif network_growth_trend == 'negative':
                strength -= 0.3
                
            # Нормализуем силу сигнала в диапазоне [0.5, 2.0]
            strength = max(0.5, min(strength, 2.0))
            
            # Получаем текущую цену
            try:
                price = float(coin_data.get('price', 0))
            except (TypeError, ValueError):
                price = 1000.0  # Значение по умолчанию
            
            # Генерируем уровни для торговли
            entry_price = price
            
            # Для LONG: стоп ниже текущей цены на 0.5-2%, цели выше на 1-5%
            # Для SHORT: стоп выше текущей цены на 0.5-2%, цели ниже на 1-5%
            if price_change_24h > 0:
                direction = SignalDirection.LONG
                stop_loss = entry_price * (1 - np.random.uniform(0.005, 0.02))
                take_profit1 = entry_price * (1 + np.random.uniform(0.01, 0.03))
                take_profit2 = entry_price * (1 + np.random.uniform(0.03, 0.05))
                risk_reward = round((take_profit1 - entry_price) / (entry_price - stop_loss), 2)
                timeframe = np.random.choice(["5m", "15m", "30m", "1h"])
            else:
                direction = SignalDirection.SHORT
                stop_loss = entry_price * (1 + np.random.uniform(0.005, 0.02))
                take_profit1 = entry_price * (1 - np.random.uniform(0.01, 0.03))
                take_profit2 = entry_price * (1 - np.random.uniform(0.03, 0.05))
                risk_reward = round((entry_price - take_profit1) / (stop_loss - entry_price), 2)
                timeframe = np.random.choice(["5m", "15m", "30m", "1h"])
            
            # Генерируем ссылку на TradingView
            from .tradingview_helper import generate_tradingview_link
            tv_link = generate_tradingview_link(pair)
            
            # Создаем сигнал
            signal = CryptoSignal(
                id=f"volume_spike_{pair}_{datetime.now().timestamp()}",
                pair=pair,
                timestamp=datetime.now(),
                signal_type=SignalType.VOLUME_SPIKE,
                direction=direction,
                price=price,
                confidence=min(z_score / threshold, 0.95),
                description=f"Всплеск объема для {symbol}: объем в {z_score:.2f}x раз выше среднего. Рекомендация: {direction.name}.",
                metadata={
                    'volume': float(current_volume),
                    'avg_volume': float(avg_volume),
                    'std_volume': float(std_volume),
                    'ratio': float(z_score),
                    'price_change_24h': float(price_change_24h),
                    'volume_to_price_ratio': float(volume_to_price_ratio),
                    'strength': float(strength),
                    'tradingview_link': tv_link,  # Добавляем ссылку на TradingView
                    'entry_price': float(entry_price),
                    'stop_loss': float(stop_loss),
                    'take_profit1': float(take_profit1),
                    'take_profit2': float(take_profit2),
                    'risk_reward': float(risk_reward),
                    'timeframe': timeframe
                }
            )
            
            # Добавляем рекомендацию на основе силы сигнала и тенденций
            if strength > 1.5 and all(trend in ['positive', 'neutral'] 
                                 for trend in [dev_activity_trend, social_volume_trend, 
                                              exchange_flows_trend, network_growth_trend]):
                signal.recommendation = 'strong_buy'
            elif strength > 1.2 and any(trend == 'positive' 
                               for trend in [dev_activity_trend, social_volume_trend, 
                                            exchange_flows_trend, network_growth_trend]):
                signal.recommendation = 'buy'
            elif strength < 0.8 and any(trend == 'negative' 
                                for trend in [dev_activity_trend, social_volume_trend, 
                                             exchange_flows_trend, network_growth_trend]):
                signal.recommendation = 'sell'
            else:
                signal.recommendation = 'hold'
            
            # Обновляем время последнего сигнала
            self._update_last_signal(pair, "volume_spike")
            logger.info(f"Создан сигнал всплеска объема для {pair}")
            return signal
        
        return None
    
    async def analyze_large_orders(self) -> List[CryptoSignal]:
        """
        Анализирует крупные ордера
        
        Returns:
            List[CryptoSignal]: Список сигналов о крупных ордерах
        """
        signals = []
        
        try:
            # Получаем настройки
            min_order_size_btc = self.config["analytics"]["large_orders"]["min_order_size_btc"]
            imbalance_threshold = self.config["analytics"]["large_orders"]["imbalance_threshold"]
            whitelist_pairs = self.config["notification"]["whitelist_pairs"]
            cooldown = self.config["notification"]["cooldown_per_pair"]
            
            # Получаем текущую цену BTC для конвертации
            btc_data = await self.data_manager.get_coin_by_symbol("BTC")
            if not btc_data or 'price' not in btc_data:
                logger.error("Не удалось получить цену BTC для конвертации")
                return []
            
            btc_price = btc_data['price']
            
            # Для каждой пары из белого списка
            for pair in whitelist_pairs:
                symbol = pair.split('/')[0]
                
                # Проверяем, не было ли недавно сигнала для этой пары
                if self._is_on_cooldown(pair, "large_order", cooldown):
                    continue
                
                # Получаем данные о монете
                coin_data = await self.data_manager.get_coin_by_symbol(symbol)
                
                if not coin_data:
                    continue
                
                # Получаем данные об ордербуке (в реальном проекте здесь будет запрос к API биржи)
                # Здесь мы используем заглушку для демонстрации
                orderbook = await self._get_mock_orderbook(symbol)
                
                # Анализируем крупные ордера
                large_buy_orders = []
                large_sell_orders = []
                
                for order in orderbook['bids']:  # Ордера на покупку
                    price, amount, total_usd = order
                    total_btc = float(total_usd) / float(btc_price)
                    
                    if total_btc >= min_order_size_btc:
                        large_buy_orders.append((price, amount, total_btc))
                
                for order in orderbook['asks']:  # Ордера на продажу
                    price, amount, total_usd = order
                    total_btc = float(total_usd) / float(btc_price)
                    
                    if total_btc >= min_order_size_btc:
                        large_sell_orders.append((price, amount, total_btc))
                
                # Вычисляем общий объем крупных ордеров
                total_buy_volume_btc = sum(order[2] for order in large_buy_orders)
                total_sell_volume_btc = sum(order[2] for order in large_sell_orders)
                
                # Проверяем дисбаланс между покупками и продажами
                if total_buy_volume_btc > 0 and total_sell_volume_btc > 0:
                    buy_sell_ratio = total_buy_volume_btc / total_sell_volume_btc
                    
                    if buy_sell_ratio >= imbalance_threshold:
                        # Генерируем уровни для торговли
                        try:
                            entry_price = float(coin_data.get('price', 0))
                        except (TypeError, ValueError):
                            entry_price = 1000.0  # Значение по умолчанию
                        
                        # Для LONG: стоп ниже текущей цены на 0.5-2%, цели выше на 1-5%
                        stop_loss = entry_price * (1 - np.random.uniform(0.005, 0.02))
                        take_profit1 = entry_price * (1 + np.random.uniform(0.01, 0.03))
                        take_profit2 = entry_price * (1 + np.random.uniform(0.03, 0.05))
                        risk_reward = round((take_profit1 - entry_price) / (entry_price - stop_loss), 2)
                        timeframe = np.random.choice(["5m", "15m", "30m", "1h"])
                        
                        # Генерируем ссылку на TradingView
                        from .tradingview_helper import generate_tradingview_link
                        tv_link = generate_tradingview_link(pair)
                        
                        # Создаем сигнал о преобладании покупок
                        signal = CryptoSignal(
                            id=f"large_order_buy_{pair}_{datetime.now().timestamp()}",
                            pair=pair,
                            timestamp=datetime.now(),
                            signal_type=SignalType.LARGE_ORDER,
                            direction=SignalDirection.LONG,
                            price=entry_price,
                            confidence=min(buy_sell_ratio / imbalance_threshold / 2, 0.95),  # Ограничиваем уверенность до 0.95
                            description=f"Крупные ордера на покупку {symbol}: объем покупок в {buy_sell_ratio:.2f}x раз больше продаж.",
                            metadata={
                                'buy_volume_btc': float(total_buy_volume_btc),
                                'sell_volume_btc': float(total_sell_volume_btc),
                                'ratio': float(buy_sell_ratio),
                                'tradingview_link': tv_link,
                                'entry_price': float(entry_price),
                                'stop_loss': float(stop_loss),
                                'take_profit1': float(take_profit1),
                                'take_profit2': float(take_profit2),
                                'risk_reward': float(risk_reward),
                                'timeframe': timeframe
                            }
                        )
                        
                        signals.append(signal)
                        self._update_last_signal(pair, "large_order")
                        logger.info(f"Обнаружены крупные ордера на покупку для {pair}")
                    
                    elif 1 / buy_sell_ratio >= imbalance_threshold:
                        # Создаем сигнал о преобладании продаж
                        sell_buy_ratio = total_sell_volume_btc / total_buy_volume_btc
                        
                        # Генерируем уровни для торговли
                        try:
                            entry_price = float(coin_data.get('price', 0))
                        except (TypeError, ValueError):
                            entry_price = 1000.0  # Значение по умолчанию
                        
                        # Для SHORT: стоп выше текущей цены на 0.5-2%, цели ниже на 1-5%
                        stop_loss = entry_price * (1 + np.random.uniform(0.005, 0.02))
                        take_profit1 = entry_price * (1 - np.random.uniform(0.01, 0.03))
                        take_profit2 = entry_price * (1 - np.random.uniform(0.03, 0.05))
                        risk_reward = round((entry_price - take_profit1) / (stop_loss - entry_price), 2)
                        timeframe = np.random.choice(["5m", "15m", "30m", "1h"])
                        
                        # Генерируем ссылку на TradingView
                        from .tradingview_helper import generate_tradingview_link
                        tv_link = generate_tradingview_link(pair)
                        
                        signal = CryptoSignal(
                            id=f"large_order_sell_{pair}_{datetime.now().timestamp()}",
                            pair=pair,
                            timestamp=datetime.now(),
                            signal_type=SignalType.LARGE_ORDER,
                            direction=SignalDirection.SHORT,
                            price=entry_price,
                            confidence=min(sell_buy_ratio / imbalance_threshold / 2, 0.95),  # Ограничиваем уверенность до 0.95
                            description=f"Крупные ордера на продажу {symbol}: объем продаж в {sell_buy_ratio:.2f}x раз больше покупок.",
                            metadata={
                                'buy_volume_btc': float(total_buy_volume_btc),
                                'sell_volume_btc': float(total_sell_volume_btc),
                                'ratio': float(sell_buy_ratio),
                                'tradingview_link': tv_link,
                                'entry_price': float(entry_price),
                                'stop_loss': float(stop_loss),
                                'take_profit1': float(take_profit1),
                                'take_profit2': float(take_profit2),
                                'risk_reward': float(risk_reward),
                                'timeframe': timeframe
                            }
                        )
                        
                        signals.append(signal)
                        self._update_last_signal(pair, "large_order")
                        logger.info(f"Обнаружены крупные ордера на продажу для {pair}")
            
            return signals
        except Exception as e:
            logger.error(f"Ошибка при анализе крупных ордеров: {e}")
            return []
    
    async def analyze_funding_rates(self) -> List[CryptoSignal]:
        """
        Анализирует ставки финансирования
        
        Returns:
            List[CryptoSignal]: Список сигналов о необычных ставках финансирования
        """
        signals = []
        
        try:
            # Получаем настройки
            alert_threshold = self.config["analytics"]["funding_rate"]["alert_threshold"]
            whitelist_pairs = self.config["notification"]["whitelist_pairs"]
            cooldown = self.config["notification"]["cooldown_per_pair"]
            
            # Для каждой пары из белого списка
            for pair in whitelist_pairs:
                symbol = pair.split('/')[0]
                
                # Проверяем, не было ли недавно сигнала для этой пары
                if self._is_on_cooldown(pair, "funding_rate", cooldown):
                    continue
                
                # Получаем данные о монете
                coin_data = await self.data_manager.get_coin_by_symbol(symbol)
                
                if not coin_data:
                    continue
                
                # Получаем данные о ставках финансирования (в реальном проекте здесь будет запрос к API биржи)
                # Здесь мы используем заглушку для демонстрации
                funding_data = await self._get_mock_funding_rate(symbol)
                
                # Анализируем ставки финансирования
                funding_rate = funding_data['rate']
                
                # Если ставка финансирования превышает порог
                if abs(funding_rate) >= alert_threshold:
                    # Определяем направление
                    direction = SignalDirection.LONG if funding_rate < 0 else SignalDirection.SHORT
                    
                    # Генерируем уровни для торговли
                    try:
                        entry_price = float(coin_data.get('price', 0))
                    except (TypeError, ValueError):
                        entry_price = 1000.0  # Значение по умолчанию
                    
                    # Для LONG: стоп ниже текущей цены на 0.5-2%, цели выше на 1-5%
                    # Для SHORT: стоп выше текущей цены на 0.5-2%, цели ниже на 1-5%
                    if direction == SignalDirection.LONG:
                        stop_loss = entry_price * (1 - np.random.uniform(0.005, 0.02))
                        take_profit1 = entry_price * (1 + np.random.uniform(0.01, 0.03))
                        take_profit2 = entry_price * (1 + np.random.uniform(0.03, 0.05))
                        risk_reward = round((take_profit1 - entry_price) / (entry_price - stop_loss), 2)
                        timeframe = np.random.choice(["5m", "15m", "30m", "1h"])
                    else:
                        stop_loss = entry_price * (1 + np.random.uniform(0.005, 0.02))
                        take_profit1 = entry_price * (1 - np.random.uniform(0.01, 0.03))
                        take_profit2 = entry_price * (1 - np.random.uniform(0.03, 0.05))
                        risk_reward = round((entry_price - take_profit1) / (stop_loss - entry_price), 2)
                        timeframe = np.random.choice(["5m", "15m", "30m", "1h"])
                    
                    # Генерируем ссылку на TradingView
                    from .tradingview_helper import generate_tradingview_link
                    tv_link = generate_tradingview_link(pair)
                    
                    # Создаем сигнал
                    signal = CryptoSignal(
                        id=f"funding_rate_{pair}_{datetime.now().timestamp()}",
                        pair=pair,
                        timestamp=datetime.now(),
                        signal_type=SignalType.FUNDING_RATE,
                        direction=direction,
                        price=entry_price,
                        confidence=min(abs(funding_rate) / alert_threshold / 2, 0.95),  # Ограничиваем уверенность до 0.95
                        description=f"Необычная ставка финансирования для {symbol}: {funding_rate:.2%}. {'Благоприятно для лонгов' if funding_rate < 0 else 'Благоприятно для шортов'}.",
                        metadata={
                            'funding_rate': float(funding_rate),
                            'threshold': float(alert_threshold),
                            'exchange': funding_data['exchange'],
                            'tradingview_link': tv_link,
                            'entry_price': float(entry_price),
                            'stop_loss': float(stop_loss),
                            'take_profit1': float(take_profit1),
                            'take_profit2': float(take_profit2),
                            'risk_reward': float(risk_reward),
                            'timeframe': timeframe
                        }
                    )
                    
                    signals.append(signal)
                    self._update_last_signal(pair, "funding_rate")
                    logger.info(f"Обнаружена необычная ставка финансирования для {pair}: {funding_rate:.2%}")
            
            return signals
        except Exception as e:
            logger.error(f"Ошибка при анализе ставок финансирования: {e}")
            return []
    
    async def get_smart_money_signals(self) -> List[CryptoSignal]:
        """
        Получает все сигналы Smart Money
        
        Returns:
            List[CryptoSignal]: Список всех сигналов Smart Money
        """
        # Получаем сигналы от всех анализаторов
        volume_signals = await self.analyze_volume_spikes()
        order_signals = await self.analyze_large_orders()
        funding_signals = await self.analyze_funding_rates()
        
        # Объединяем все сигналы
        all_signals = volume_signals + order_signals + funding_signals
        
        # Фильтруем противоречивые сигналы
        filtered_signals = []
        pairs_with_signals = {}  # Словарь для отслеживания пар с сигналами
        
        # Сортируем сигналы по уверенности
        all_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        # Добавляем только один сигнал для каждой пары (с наибольшей уверенностью)
        for signal in all_signals:
            pair = signal.pair
            if pair not in pairs_with_signals:
                pairs_with_signals[pair] = signal
                filtered_signals.append(signal)
        
        # Заменяем исходный список отфильтрованным
        all_signals = filtered_signals
        
        # Если сигналов нет или их мало, создаем дополнительные тестовые сигналы
        if len(all_signals) < 5:
            # Создаем тестовые сигналы для демонстрации
            test_signals = []
            
            # Выбираем пары из белого списка, для которых еще нет сигналов
            whitelist_pairs = self.config["notification"]["whitelist_pairs"]
            existing_pairs = {signal.pair for signal in all_signals}
            available_pairs = [pair for pair in whitelist_pairs if pair not in existing_pairs]
            
            # Если доступных пар нет, используем все пары
            if not available_pairs:
                available_pairs = whitelist_pairs
            
            # Выбираем случайные пары для генерации сигналов
            num_signals_to_generate = min(5 - len(all_signals), len(available_pairs))
            if num_signals_to_generate > 0:
                selected_pairs = np.random.choice(available_pairs, num_signals_to_generate, replace=False)
            else:
                selected_pairs = []
            
            for pair in selected_pairs:
                symbol = pair.split('/')[0]
                
                # Получаем данные о монете
                coin_data = await self.data_manager.get_coin_by_symbol(symbol)
                if not coin_data or 'price' not in coin_data:
                    continue
                
                price = coin_data['price']
                
                # Случайный тип сигнала
                signal_types = [SignalType.VOLUME_SPIKE, SignalType.LARGE_ORDER, SignalType.FUNDING_RATE]
                signal_type = np.random.choice(signal_types)
                
                # Случайное направление
                direction = SignalDirection.LONG if np.random.random() > 0.5 else SignalDirection.SHORT
                
                # Случайная уверенность от 0.3 до 0.9
                confidence = np.random.uniform(0.3, 0.9)
                
                # Описание в зависимости от типа сигнала
                if signal_type == SignalType.VOLUME_SPIKE:
                    description = f"[ТЕСТ] Всплеск объема для {symbol}: объем в {np.random.uniform(1.1, 3.0):.2f}x раз выше среднего"
                elif signal_type == SignalType.LARGE_ORDER:
                    if direction == SignalDirection.LONG:
                        description = f"[ТЕСТ] Крупные ордера на покупку {symbol}: объем покупок в {np.random.uniform(1.2, 3.0):.2f}x раз больше продаж"
                    else:
                        description = f"[ТЕСТ] Крупные ордера на продажу {symbol}: объем продаж в {np.random.uniform(1.2, 3.0):.2f}x раз больше покупок"
                else:  # FUNDING_RATE
                    rate = np.random.uniform(-0.1, 0.1)
                    if direction == SignalDirection.LONG:
                        description = f"[ТЕСТ] Необычная ставка финансирования для {symbol}: {rate:.2%}. Благоприятно для лонгов"
                    else:
                        description = f"[ТЕСТ] Необычная ставка финансирования для {symbol}: {rate:.2%}. Благоприятно для шортов"
                
                # Генерируем уровни для торговли
                try:
                    entry_price = float(price)
                except (TypeError, ValueError):
                    entry_price = 1000.0  # Значение по умолчанию
                
                # Для LONG: стоп ниже текущей цены на 2-5%, цели выше на 3-15%
                # Для SHORT: стоп выше текущей цены на 2-5%, цели ниже на 3-15%
                if direction == SignalDirection.LONG:
                    stop_loss = entry_price * (1 - np.random.uniform(0.02, 0.05))
                    take_profit1 = entry_price * (1 + np.random.uniform(0.03, 0.07))
                    take_profit2 = entry_price * (1 + np.random.uniform(0.08, 0.15))
                    risk_reward = round((take_profit1 - entry_price) / (entry_price - stop_loss), 2)
                    timeframe = "4h-1d" if np.random.random() > 0.5 else "1h-4h"
                else:
                    stop_loss = entry_price * (1 + np.random.uniform(0.02, 0.05))
                    take_profit1 = entry_price * (1 - np.random.uniform(0.03, 0.07))
                    take_profit2 = entry_price * (1 - np.random.uniform(0.08, 0.15))
                    risk_reward = round((entry_price - take_profit1) / (stop_loss - entry_price), 2)
                    timeframe = "4h-1d" if np.random.random() > 0.5 else "1h-4h"
                
                # Генерируем ссылку на TradingView
                from .tradingview_helper import generate_tradingview_link
                tv_link = generate_tradingview_link(pair)
                
                # Создаем тестовый сигнал
                signal = CryptoSignal(
                    id=f"{signal_type.name.lower()}_{pair}_{datetime.now().timestamp()}",
                    pair=pair,
                    timestamp=datetime.now(),
                    signal_type=signal_type,
                    direction=direction,
                    price=price,
                    confidence=confidence,
                    description=description,
                    metadata={
                        'test_signal': True,
                        'tradingview_link': tv_link,  # Добавляем ссылку на TradingView
                        'entry_price': float(entry_price),
                        'stop_loss': float(stop_loss),
                        'take_profit1': float(take_profit1),
                        'take_profit2': float(take_profit2),
                        'risk_reward': float(risk_reward),
                        'timeframe': timeframe
                    }
                )
                
                test_signals.append(signal)
            
            # Добавляем тестовые сигналы к существующим
            all_signals.extend(test_signals)
            logger.info(f"Создано {len(test_signals)} дополнительных тестовых сигналов для демонстрации")
        
        # Ограничиваем количество сигналов
        max_signals = self.config["notification"]["max_signals_per_hour"]
        
        # Сортируем по уверенности
        all_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        # Фильтруем сигналы с уверенностью меньше 0.55 (55%)
        filtered_signals = [s for s in all_signals if s.confidence >= 0.55]
        
        # Если после фильтрации не осталось сигналов, берем исходные
        if not filtered_signals:
            filtered_signals = all_signals
        
        return filtered_signals[:max_signals]
    
    def _is_on_cooldown(self, pair: str, signal_type: str, cooldown: int) -> bool:
        """
        Проверяет, находится ли пара на кулдауне для данного типа сигнала
        
        Args:
            pair: Торговая пара
            signal_type: Тип сигнала
            cooldown: Время кулдауна в секундах
            
        Returns:
            bool: True, если пара на кулдауне
        """
        key = f"{pair}_{signal_type}"
        
        if key in self._last_signals:
            last_time = self._last_signals[key]
            elapsed = (datetime.now() - last_time).total_seconds()
            
            if elapsed < cooldown:
                return True
        
        return False
    
    def _update_last_signal(self, pair: str, signal_type: str):
        """
        Обновляет время последнего сигнала для пары
        
        Args:
            pair: Торговая пара
            signal_type: Тип сигнала
        """
        key = f"{pair}_{signal_type}"
        self._last_signals[key] = datetime.now()
    
    async def _get_mock_orderbook(self, symbol: str) -> Dict[str, List[Tuple[float, float, float]]]:
        """
        Получает заглушку для ордербука
        
        Args:
            symbol: Символ монеты
            
        Returns:
            Dict[str, List[Tuple[float, float, float]]]: Заглушка для ордербука
        """
        # Получаем данные о монете
        coin_data = await self.data_manager.get_coin_by_symbol(symbol)
        
        if not coin_data or 'price' not in coin_data:
            return {'bids': [], 'asks': []}
        
        # Убедимся, что price - это число
        try:
            price = float(coin_data['price'])
        except (TypeError, ValueError):
            price = 1000.0  # Значение по умолчанию
        
        # Генерируем случайные ордера
        bids = []  # (price, amount, total_usd)
        asks = []  # (price, amount, total_usd)
        
        # Генерируем 10 ордеров на покупку
        for i in range(10):
            bid_price = float(price * (1 - 0.001 * (i + 1)))
            amount = float(np.random.uniform(1, 100))
            total_usd = float(bid_price * amount)
            bids.append((bid_price, amount, total_usd))
        
        # Генерируем 10 ордеров на продажу
        for i in range(10):
            ask_price = float(price * (1 + 0.001 * (i + 1)))
            amount = float(np.random.uniform(1, 100))
            total_usd = float(ask_price * amount)
            asks.append((ask_price, amount, total_usd))
        
        # Добавляем один крупный ордер с вероятностью 80% (было 20%)
        if np.random.random() < 0.8:
            if np.random.random() < 0.5:
                # Крупный ордер на покупку
                bid_price = float(price * 0.99)
                amount = float(np.random.uniform(100, 1000))
                total_usd = float(bid_price * amount)
                bids.append((bid_price, amount, total_usd))
            else:
                # Крупный ордер на продажу
                ask_price = float(price * 1.01)
                amount = float(np.random.uniform(100, 1000))
                total_usd = float(ask_price * amount)
                asks.append((ask_price, amount, total_usd))
        
        # Добавляем еще один крупный ордер для создания дисбаланса с вероятностью 60%
        if np.random.random() < 0.6:
            if np.random.random() < 0.5:
                # Еще один крупный ордер на покупку для создания дисбаланса
                bid_price = float(price * 0.98)
                amount = float(np.random.uniform(200, 2000))
                total_usd = float(bid_price * amount)
                bids.append((bid_price, amount, total_usd))
            else:
                # Еще один крупный ордер на продажу для создания дисбаланса
                ask_price = float(price * 1.02)
                amount = float(np.random.uniform(200, 2000))
                total_usd = float(ask_price * amount)
                asks.append((ask_price, amount, total_usd))
        
        return {'bids': bids, 'asks': asks}
    
    async def _get_mock_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        Получает заглушку для ставки финансирования
        
        Args:
            symbol: Символ монеты
            
        Returns:
            Dict[str, Any]: Заглушка для ставки финансирования
        """
        # Получаем данные о монете
        coin_data = await self.data_manager.get_coin_by_symbol(symbol)
        
        if not coin_data or 'price' not in coin_data:
            return {'rate': 0.0, 'exchange': 'unknown'}
        
        # Убедимся, что price - это число
        try:
            price = float(coin_data['price'])
        except (TypeError, ValueError):
            price = 1000.0  # Значение по умолчанию
        
        # Генерируем случайную ставку финансирования
        # Базовая ставка зависит от символа
        base_rate = {
            'BTC': 0.0005,
            'ETH': 0.0006,
            'BNB': 0.0008,
            'SOL': 0.001,
            'XRP': 0.0012,
            'ADA': 0.0015,
            'DOGE': 0.002,
            'DOT': 0.0013,
            'AVAX': 0.0014,
            'MATIC': 0.0016,
            'LINK': 0.0017,
            'UNI': 0.0018,
            'ATOM': 0.0019,
            'LTC': 0.0011,
            'SHIB': 0.0025,
            'NEAR': 0.0015,
            'ALGO': 0.0017,
            'FTM': 0.002,
            'MANA': 0.0022,
            'XLM': 0.0024
        }.get(symbol.upper(), 0.0015)
        
        # Добавляем случайное изменение к базовой ставке
        rate_change = np.random.uniform(-0.0005, 0.0005)
        rate = base_rate + rate_change
        
        # Генерируем случайную биржу
        exchanges = ['Binance', 'Bybit', 'OKX', 'Bitfinex', 'Kraken']
        exchange = np.random.choice(exchanges)
        
        return {
            'rate': rate,
            'exchange': exchange,
            'timestamp': datetime.now().isoformat()
        }

# Создаем глобальный экземпляр анализатора
_analyzer = SmartMoneyAnalyzer()

def get_smart_money_analyzer() -> SmartMoneyAnalyzer:
    """
    Получает глобальный экземпляр анализатора Smart Money
    
    Returns:
        SmartMoneyAnalyzer: Глобальный экземпляр анализатора
    """
    return _analyzer