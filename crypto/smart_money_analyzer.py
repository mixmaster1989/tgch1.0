import logging
import asyncio
import numpy as np
import sys
import traceback
from datetime import datetime, timedelta
from .config import crypto_config
from .data_sources import DataSourceManager

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

class SmartMoneyAnalyzer:
    """
    Анализатор активности Smart Money на криптовалютном рынке
    """
    def __init__(self, data_manager):
        """
        Инициализация анализатора
        
        Args:
            data_manager (DataSourceManager): Менеджер источников данных
        """
        self.data_manager = data_manager
        self.binance = data_manager.get_source("binance")
        self.whale_alert = data_manager.get_source("whale_alert")
        
        # Загрузка конфигурации
        self.config = crypto_config
        self.pairs = self.config.get('monitoring', {}).get('pairs', ['BTCUSDT', 'ETHUSDT'])
        self.timeframes = self.config.get('monitoring', {}).get('timeframes', ['1h', '4h', '1d'])
        self.volume_threshold = self.config.get('monitoring', {}).get('volume_threshold', 1000000)
        self.whale_threshold = self.config.get('monitoring', {}).get('whale_threshold', 500000)
        
        # Настройки Smart Money
        self.oi_change_threshold = self.config.get('smart_money', {}).get('oi_change_threshold', 5)
        self.funding_rate_threshold = self.config.get('smart_money', {}).get('funding_rate_threshold', 0.1)
        
        # Кэш для хранения данных
        self.klines_cache = {}
        self.oi_cache = {}
        self.funding_rate_cache = {}
        self.last_volume_spike = {}
        self.last_whale_alert = {}
    
    async def analyze_pair(self, pair):
        """
        Анализирует торговую пару на наличие активности Smart Money
        
        Args:
            pair (str): Торговая пара (например, BTCUSDT)
            
        Returns:
            dict: Результаты анализа
        """
        logger.info(f"Анализ пары {pair}")
        
        results = {
            "pair": pair,
            "timestamp": datetime.now().timestamp(),
            "price": None,
            "signals": [],
            "details": {}
        }
        
        # Получаем текущую цену
        price = await self.binance.get_ticker_price(pair)
        if price:
            results["price"] = price
        
        # Анализируем объемы
        volume_signals = await self.analyze_volumes(pair)
        if volume_signals:
            results["signals"].extend(volume_signals)
            results["details"]["volume"] = volume_signals
        
        # Анализируем Open Interest
        oi_signals = await self.analyze_open_interest(pair)
        if oi_signals:
            results["signals"].extend(oi_signals)
            results["details"]["open_interest"] = oi_signals
        
        # Анализируем Funding Rate
        funding_signals = await self.analyze_funding_rate(pair)
        if funding_signals:
            results["signals"].extend(funding_signals)
            results["details"]["funding_rate"] = funding_signals
        
        # Анализируем транзакции китов
        whale_signals = await self.analyze_whale_transactions(pair)
        if whale_signals:
            results["signals"].extend(whale_signals)
            results["details"]["whale_transactions"] = whale_signals
        
        # Анализируем книгу ордеров
        orderbook_signals = await self.analyze_order_book(pair)
        if orderbook_signals:
            results["signals"].extend(orderbook_signals)
            results["details"]["order_book"] = orderbook_signals
        
        return results
    
    async def analyze_volumes(self, pair):
        """
        Анализирует объемы торгов для выявления всплесков
        
        Args:
            pair (str): Торговая пара
            
        Returns:
            list: Сигналы по объемам
        """
        signals = []
        
        for timeframe in self.timeframes:
            # Получаем свечи
            klines = await self.binance.get_klines(pair, timeframe, limit=100)
            if not klines:
                continue
            
            # Извлекаем объемы
            volumes = [k["volume"] * k["close"] for k in klines]  # Объем в USD
            
            # Рассчитываем средний объем за последние 20 свечей
            avg_volume = np.mean(volumes[-20:])
            current_volume = volumes[-1]
            
            # Проверяем на всплеск объема
            if current_volume > avg_volume * 2 and current_volume > self.volume_threshold:
                # Определяем направление (бычье или медвежье)
                current_candle = klines[-1]
                is_bullish = current_candle["close"] > current_candle["open"]
                direction = "long" if is_bullish else "short"
                
                # Проверяем, не было ли недавно сигнала по этой паре и таймфрейму
                cache_key = f"{pair}_{timeframe}"
                last_alert_time = self.last_volume_spike.get(cache_key, 0)
                current_time = datetime.now().timestamp()
                
                # Если прошло достаточно времени с последнего сигнала
                cooldown = self.config.get('signals', {}).get('notification_cooldown', 3600)
                if current_time - last_alert_time > cooldown:
                    signal = {
                        "type": "volume_spike",
                        "direction": direction,
                        "timeframe": timeframe,
                        "volume": current_volume,
                        "avg_volume": avg_volume,
                        "ratio": current_volume / avg_volume,
                        "timestamp": current_time
                    }
                    signals.append(signal)
                    
                    # Обновляем время последнего сигнала
                    self.last_volume_spike[cache_key] = current_time
                    
                    logger.info(f"Обнаружен всплеск объема на {pair} ({timeframe}): {current_volume:.2f} USD, в {current_volume/avg_volume:.2f} раз выше среднего")
        
        return signals
    
    async def analyze_open_interest(self, pair):
        """
        Анализирует изменения Open Interest
        
        Args:
            pair (str): Торговая пара
            
        Returns:
            list: Сигналы по Open Interest
        """
        signals = []
        
        # Получаем текущий Open Interest
        current_oi = await self.binance.get_open_interest(pair)
        if not current_oi:
            return signals
        
        # Получаем предыдущее значение из кэша
        previous_oi = self.oi_cache.get(pair, None)
        
        # Обновляем кэш
        self.oi_cache[pair] = current_oi
        
        # Если у нас есть предыдущее значение, рассчитываем изменение
        if previous_oi:
            change_percent = ((current_oi - previous_oi) / previous_oi) * 100
            
            # Если изменение превышает порог
            if abs(change_percent) > self.oi_change_threshold:
                direction = "long" if change_percent > 0 else "short"
                
                signal = {
                    "type": "open_interest_change",
                    "direction": direction,
                    "current_oi": current_oi,
                    "previous_oi": previous_oi,
                    "change_percent": change_percent,
                    "timestamp": datetime.now().timestamp()
                }
                signals.append(signal)
                
                logger.info(f"Обнаружено изменение Open Interest на {pair}: {change_percent:.2f}%")
        
        return signals
    
    async def analyze_funding_rate(self, pair):
        """
        Анализирует Funding Rate
        
        Args:
            pair (str): Торговая пара
            
        Returns:
            list: Сигналы по Funding Rate
        """
        signals = []
        
        # Получаем текущий Funding Rate
        funding_rate = await self.binance.get_funding_rate(pair)
        if not funding_rate:
            return signals
        
        # Если Funding Rate превышает порог
        if abs(funding_rate) > self.funding_rate_threshold:
            direction = "short" if funding_rate > 0 else "long"
            
            signal = {
                "type": "funding_rate",
                "direction": direction,
                "funding_rate": funding_rate,
                "timestamp": datetime.now().timestamp()
            }
            signals.append(signal)
            
            logger.info(f"Обнаружен высокий Funding Rate на {pair}: {funding_rate:.4f}")
        
        return signals
    
    async def analyze_whale_transactions(self, pair):
        """
        Анализирует транзакции китов
        
        Args:
            pair (str): Торговая пара
            
        Returns:
            list: Сигналы по транзакциям китов
        """
        signals = []
        
        # Извлекаем символ без USDT
        symbol = pair.replace("USDT", "").lower()
        
        # Получаем транзакции китов
        transactions = await self.whale_alert.get_transactions(
            min_value=self.whale_threshold,
            limit=10
        )
        
        for tx in transactions:
            # Проверяем, относится ли транзакция к нашей паре
            if tx.get("symbol", "").lower() == symbol:
                # Проверяем, не было ли недавно сигнала по этой транзакции
                tx_id = tx.get("id", "")
                if tx_id in self.last_whale_alert:
                    continue
                
                # Определяем тип транзакции
                tx_type = tx.get("transaction_type", "")
                direction = None
                
                if "transfer" in tx_type:
                    # Перевод между кошельками
                    from_owner = tx.get("from", {}).get("owner_type", "")
                    to_owner = tx.get("to", {}).get("owner_type", "")
                    
                    if from_owner == "exchange" and to_owner != "exchange":
                        direction = "long"  # Вывод с биржи (возможно, для долгосрочного хранения)
                    elif from_owner != "exchange" and to_owner == "exchange":
                        direction = "short"  # Ввод на биржу (возможно, для продажи)
                
                if direction:
                    signal = {
                        "type": "whale_transaction",
                        "direction": direction,
                        "amount": tx.get("amount", 0),
                        "amount_usd": tx.get("amount_usd", 0),
                        "transaction_type": tx_type,
                        "timestamp": tx.get("timestamp", datetime.now().timestamp())
                    }
                    signals.append(signal)
                    
                    # Сохраняем ID транзакции в кэш
                    self.last_whale_alert[tx_id] = datetime.now().timestamp()
                    
                    logger.info(f"Обнаружена транзакция кита для {symbol}: {tx.get('amount', 0)} {symbol.upper()} (${tx.get('amount_usd', 0):,.2f})")
        
        return signals
    
    async def analyze_order_book(self, pair):
        """
        Анализирует книгу ордеров для выявления зон ликвидности
        
        Args:
            pair (str): Торговая пара
            
        Returns:
            list: Сигналы по книге ордеров
        """
        signals = []
        
        # Получаем книгу ордеров
        order_book = await self.binance.get_order_book(pair, limit=500)
        if not order_book:
            return signals
        
        # Извлекаем биды и аски
        bids = order_book["bids"]  # [[price, quantity], ...]
        asks = order_book["asks"]  # [[price, quantity], ...]
        
        # Группируем ордера по ценовым уровням
        bid_levels = self._group_orders_by_price(bids)
        ask_levels = self._group_orders_by_price(asks)
        
        # Находим уровни с наибольшим объемом
        top_bid_levels = sorted(bid_levels.items(), key=lambda x: x[1], reverse=True)[:5]
        top_ask_levels = sorted(ask_levels.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Получаем текущую цену
        current_price = await self.binance.get_ticker_price(pair)
        if not current_price:
            return signals
        
        # Анализируем крупные уровни поддержки (биды)
        for price_level, volume in top_bid_levels:
            price = float(price_level)
            # Если объем на уровне превышает порог и уровень близок к текущей цене
            if volume > self.volume_threshold and price < current_price and price > current_price * 0.95:
                signal = {
                    "type": "liquidity_zone",
                    "direction": "long",
                    "price_level": price,
                    "volume": volume,
                    "distance_percent": ((current_price - price) / current_price) * 100,
                    "timestamp": datetime.now().timestamp()
                }
                signals.append(signal)
                
                logger.info(f"Обнаружена зона ликвидности (поддержка) на {pair}: {price} с объемом {volume:.2f}")
        
        # Анализируем крупные уровни сопротивления (аски)
        for price_level, volume in top_ask_levels:
            price = float(price_level)
            # Если объем на уровне превышает порог и уровень близок к текущей цене
            if volume > self.volume_threshold and price > current_price and price < current_price * 1.05:
                signal = {
                    "type": "liquidity_zone",
                    "direction": "short",
                    "price_level": price,
                    "volume": volume,
                    "distance_percent": ((price - current_price) / current_price) * 100,
                    "timestamp": datetime.now().timestamp()
                }
                signals.append(signal)
                
                logger.info(f"Обнаружена зона ликвидности (сопротивление) на {pair}: {price} с объемом {volume:.2f}")
        
        return signals
    
    def _group_orders_by_price(self, orders, precision=1):
        """
        Группирует ордера по ценовым уровням
        
        Args:
            orders (list): Список ордеров [[price, quantity], ...]
            precision (int): Точность округления цены
            
        Returns:
            dict: Сгруппированные ордера {price_level: total_volume}
        """
        grouped = {}
        
        for price, qty in orders:
            # Округляем цену до указанной точности
            rounded_price = round(price, precision)
            price_level = str(rounded_price)
            
            # Добавляем объем к соответствующему ценовому уровню
            if price_level in grouped:
                grouped[price_level] += qty * price  # Объем в USD
            else:
                grouped[price_level] = qty * price
        
        return grouped
    
    async def detect_order_blocks(self, pair, timeframe="1h"):
        """
        Обнаруживает блоки ордеров (Order Blocks)
        
        Args:
            pair (str): Торговая пара
            timeframe (str): Таймфрейм
            
        Returns:
            list: Обнаруженные блоки ордеров
        """
        order_blocks = []
        
        # Получаем свечи
        klines = await self.binance.get_klines(pair, timeframe, limit=100)
        if not klines:
            return order_blocks
        
        # Находим свечи с высоким объемом
        avg_volume = np.mean([k["volume"] for k in klines])
        
        for i in range(1, len(klines) - 1):
            prev_candle = klines[i-1]
            current_candle = klines[i]
            next_candle = klines[i+1]
            
            # Проверяем, является ли свеча разворотной
            is_bullish_reversal = (prev_candle["close"] < prev_candle["open"] and  # Предыдущая свеча медвежья
                                  current_candle["close"] > current_candle["open"] and  # Текущая свеча бычья
                                  current_candle["volume"] > avg_volume * 1.5)  # Объем выше среднего
            
            is_bearish_reversal = (prev_candle["close"] > prev_candle["open"] and  # Предыдущая свеча бычья
                                  current_candle["close"] < current_candle["open"] and  # Текущая свеча медвежья
                                  current_candle["volume"] > avg_volume * 1.5)  # Объем выше среднего
            
            if is_bullish_reversal:
                order_block = {
                    "type": "bullish_order_block",
                    "timeframe": timeframe,
                    "high": current_candle["high"],
                    "low": current_candle["low"],
                    "volume": current_candle["volume"],
                    "timestamp": current_candle["open_time"]
                }
                order_blocks.append(order_block)
                
                logger.info(f"Обнаружен бычий Order Block на {pair} ({timeframe}): {current_candle['low']} - {current_candle['high']}")
            
            elif is_bearish_reversal:
                order_block = {
                    "type": "bearish_order_block",
                    "timeframe": timeframe,
                    "high": current_candle["high"],
                    "low": current_candle["low"],
                    "volume": current_candle["volume"],
                    "timestamp": current_candle["open_time"]
                }
                order_blocks.append(order_block)
                
                logger.info(f"Обнаружен медвежий Order Block на {pair} ({timeframe}): {current_candle['low']} - {current_candle['high']}")
        
        return order_blocks
    
    async def run_analysis(self):
        """
        Запускает анализ для всех пар
        
        Returns:
            dict: Результаты анализа по всем парам
        """
        results = {}
        
        for pair in self.pairs:
            try:
                pair_results = await self.analyze_pair(pair)
                results[pair] = pair_results
            except Exception as e:
                logger.error(f"Ошибка при анализе пары {pair}: {e}")
        
        return results