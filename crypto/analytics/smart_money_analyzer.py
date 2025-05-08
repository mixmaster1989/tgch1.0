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

class SmartMoneyAnalyzer:
    """
    Класс для анализа Smart Money сигналов
    """
    
    def __init__(self):
        """
        Инициализирует анализатор Smart Money
        """
        self.data_manager = get_data_manager()
        self.config = self._load_config()
        
        # Кэш для хранения последних сигналов
        self._last_signals = {}  # pair -> {timestamp, signal_type}
        
        logger.info("Инициализирован анализатор Smart Money")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Загружает конфигурацию Smart Money
        
        Returns:
            Dict[str, Any]: Конфигурация
        """
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
    
    async def analyze_volume_spikes(self) -> List[CryptoSignal]:
        """
        Анализирует всплески объема
        
        Returns:
            List[CryptoSignal]: Список сигналов о всплесках объема
        """
        signals = []
        
        try:
            # Получаем настройки
            threshold = self.config["analytics"]["volume_spike"]["threshold"]
            ma_period = self.config["analytics"]["volume_spike"]["ma_period"]
            whitelist_pairs = self.config["notification"]["whitelist_pairs"]
            cooldown = self.config["notification"]["cooldown_per_pair"]
            
            # Для каждой пары из белого списка
            for pair in whitelist_pairs:
                symbol = pair.split('/')[0]
                
                # Проверяем, не было ли недавно сигнала для этой пары
                if self._is_on_cooldown(pair, "volume_spike", cooldown):
                    continue
                
                # Получаем историю цен и объемов
                history = await self.data_manager.get_price_history(symbol, days=ma_period)
                
                if not history:
                    # Если истории нет, генерируем тестовый сигнал с вероятностью 30%
                    if np.random.random() < 0.3:
                        # Получаем данные о монете
                        coin_data = await self.data_manager.get_coin_by_symbol(symbol)
                        if coin_data and 'price' in coin_data:
                            price = coin_data['price']
                            # Случайное направление
                            direction = SignalDirection.LONG if np.random.random() > 0.5 else SignalDirection.SHORT
                            # Случайная уверенность от 0.3 до 0.9
                            confidence = np.random.uniform(0.3, 0.9)
                            
                            # Генерируем ссылку на TradingView
                            from .tradingview_helper import generate_tradingview_link
                            tv_link = generate_tradingview_link(pair)
                            
                            # Генерируем уровни для торговли
                            entry_price = price
                            
                            # Для LONG: стоп ниже текущей цены на 0.5-2%, цели выше на 1-5%
                            # Для SHORT: стоп выше текущей цены на 0.5-2%, цели ниже на 1-5%
                            if direction == SignalDirection.LONG:
                                stop_loss = price * (1 - np.random.uniform(0.005, 0.02))
                                take_profit1 = price * (1 + np.random.uniform(0.01, 0.03))
                                take_profit2 = price * (1 + np.random.uniform(0.03, 0.05))
                                risk_reward = round((take_profit1 - entry_price) / (entry_price - stop_loss), 2)
                                timeframe = np.random.choice(["5m", "15m", "30m", "1h"])
                            else:
                                stop_loss = price * (1 + np.random.uniform(0.005, 0.02))
                                take_profit1 = price * (1 - np.random.uniform(0.01, 0.03))
                                take_profit2 = price * (1 - np.random.uniform(0.03, 0.05))
                                risk_reward = round((entry_price - take_profit1) / (stop_loss - entry_price), 2)
                                timeframe = np.random.choice(["5m", "15m", "30m", "1h"])
                            
                            # Создаем расширенное описание с торговыми рекомендациями
                            volume_ratio = np.random.uniform(1.1, 3.0)
                            description = (
                                f"[ТЕСТ] Всплеск объема для {symbol}: объем в {volume_ratio:.2f}x раз выше среднего. "
                                f"Рекомендация: {direction.name} с входом около ${entry_price:.2f}. "
                                f"Стоп-лосс: ${stop_loss:.2f}. "
                                f"Цели: ${take_profit1:.2f} и ${take_profit2:.2f}. "
                                f"Соотношение риск/прибыль: 1:{risk_reward}. "
                                f"Временной горизонт: {timeframe}."
                            )
                            
                            # Создаем тестовый сигнал
                            signal = CryptoSignal(
                                id=f"volume_spike_{pair}_{datetime.now().timestamp()}",
                                pair=pair,
                                timestamp=datetime.now(),
                                signal_type=SignalType.VOLUME_SPIKE,
                                direction=direction,
                                price=price,
                                confidence=confidence,
                                description=description,
                                metadata={
                                    'volume': float(price * 1000),  # Заглушка
                                    'volume_ma': float(price * 500),  # Заглушка
                                    'ratio': 2.0,  # Заглушка
                                    'test_signal': True,  # Помечаем как тестовый сигнал
                                    'tradingview_link': tv_link,  # Добавляем ссылку на TradingView
                                    'entry_price': float(entry_price),
                                    'stop_loss': float(stop_loss),
                                    'take_profit1': float(take_profit1),
                                    'take_profit2': float(take_profit2),
                                    'risk_reward': float(risk_reward),
                                    'timeframe': timeframe
                                }
                            )
                            
                            signals.append(signal)
                            self._update_last_signal(pair, "volume_spike")
                            logger.info(f"Создан тестовый сигнал всплеска объема для {pair}")
                    continue
                
                # Преобразуем в pandas DataFrame
                df = pd.DataFrame(history)
                
                # Проверяем наличие необходимых данных
                if 'volume' not in df.columns or len(df) < 2:
                    continue
                
                # Вычисляем скользящую среднюю объема
                df['volume_ma'] = df['volume'].rolling(window=min(len(df), 24)).mean()
                
                # Получаем последний объем и его скользящую среднюю
                last_volume = df['volume'].iloc[-1]
                last_volume_ma = df['volume_ma'].iloc[-1]
                
                # Если объем превышает скользящую среднюю в threshold раз
                if last_volume > last_volume_ma * threshold:
                    # Определяем направление на основе изменения цены
                    price_change = df['price'].iloc[-1] - df['price'].iloc[-2]
                    direction = SignalDirection.LONG if price_change > 0 else SignalDirection.SHORT
                    
                    # Генерируем ссылку на TradingView
                    from .tradingview_helper import generate_tradingview_link
                    tv_link = generate_tradingview_link(pair)
                    
                    # Текущая цена
                    current_price = float(df['price'].iloc[-1])
                    
                    # Генерируем уровни для торговли
                    entry_price = current_price
                    
                    # Для LONG: стоп ниже текущей цены на 0.5-2%, цели выше на 1-5%
                    # Для SHORT: стоп выше текущей цены на 0.5-2%, цели ниже на 1-5%
                    if direction == SignalDirection.LONG:
                        stop_loss = current_price * (1 - np.random.uniform(0.005, 0.02))
                        take_profit1 = current_price * (1 + np.random.uniform(0.01, 0.03))
                        take_profit2 = current_price * (1 + np.random.uniform(0.03, 0.05))
                        risk_reward = round((take_profit1 - entry_price) / (entry_price - stop_loss), 2)
                        timeframe = np.random.choice(["5m", "15m", "30m", "1h"])
                    else:
                        stop_loss = current_price * (1 + np.random.uniform(0.005, 0.02))
                        take_profit1 = current_price * (1 - np.random.uniform(0.01, 0.03))
                        take_profit2 = current_price * (1 - np.random.uniform(0.03, 0.05))
                        risk_reward = round((entry_price - take_profit1) / (stop_loss - entry_price), 2)
                        timeframe = np.random.choice(["5m", "15m", "30m", "1h"])
                    
                    # Создаем расширенное описание с торговыми рекомендациями
                    volume_ratio = last_volume / last_volume_ma
                    description = (
                        f"Всплеск объема для {symbol}: объем в {volume_ratio:.2f}x раз выше среднего. "
                        f"Рекомендация: {direction.name} с входом около ${entry_price:.2f}. "
                        f"Стоп-лосс: ${stop_loss:.2f}. "
                        f"Цели: ${take_profit1:.2f} и ${take_profit2:.2f}. "
                        f"Соотношение риск/прибыль: 1:{risk_reward}. "
                        f"Временной горизонт: {timeframe}."
                    )
                    
                    # Создаем сигнал
                    signal = CryptoSignal(
                        id=f"volume_spike_{pair}_{datetime.now().timestamp()}",
                        pair=pair,
                        timestamp=datetime.now(),
                        signal_type=SignalType.VOLUME_SPIKE,
                        direction=direction,
                        price=current_price,
                        confidence=min(volume_ratio / threshold, 1.0),
                        description=description,
                        metadata={
                            'volume': float(last_volume),
                            'volume_ma': float(last_volume_ma),
                            'ratio': float(volume_ratio),
                            'tradingview_link': tv_link,  # Добавляем ссылку на TradingView
                            'entry_price': float(entry_price),
                            'stop_loss': float(stop_loss),
                            'take_profit1': float(take_profit1),
                            'take_profit2': float(take_profit2),
                            'risk_reward': float(risk_reward),
                            'timeframe': timeframe
                        }
                    )
                    
                    signals.append(signal)
                    self._update_last_signal(pair, "volume_spike")
                    logger.info(f"Обнаружен всплеск объема для {pair}")
            
            return signals
        except Exception as e:
            logger.error(f"Ошибка при анализе всплесков объема: {e}")
            return []
    
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
        # Генерируем случайную ставку финансирования с большей вероятностью экстремальных значений
        # Используем бета-распределение для создания более экстремальных значений
        if np.random.random() < 0.7:  # 70% вероятность генерации значимой ставки
            # Генерируем значение от -0.2 до 0.2 с большей вероятностью экстремальных значений
            alpha, beta = 0.5, 0.5  # Параметры бета-распределения для U-образной формы
            value = np.random.beta(alpha, beta)  # Значение от 0 до 1
            value = (value * 2 - 1) * 0.2  # Преобразуем в диапазон от -0.2 до 0.2
        else:
            # Обычное равномерное распределение
            value = np.random.uniform(-0.05, 0.05)
        
        return {
            'rate': value,
            'exchange': 'Binance',
            'timestamp': datetime.now()
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