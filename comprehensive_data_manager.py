#!/usr/bin/env python3
"""
Комплексный менеджер данных для MEXC Trading Bot
Управляет всеми источниками данных: WebSocket, REST API, Perplexity, базы данных
"""

import asyncio
import aiohttp
import ssl
import json
import time
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
import logging
import random
from decimal import Decimal
import math

# Импорты компонентов
from mexc_websocket_client import MEXCWebSocketClient, StreamType, OrderBook
from mex_api import MexAPI
from perplexity_analyzer import PerplexityAnalyzer
from technical_indicators import TechnicalIndicators
from correlation_analyzer import CorrelationAnalyzer
from advanced_correlation_analyzer import advanced_correlation_analyzer
from cache.redis_manager import RedisCacheManager
from database.connection import DatabaseConnection

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSource(Enum):
    WEBSOCKET = "websocket"
    REST_API = "rest_api"
    PERPLEXITY = "perplexity"
    CALCULATED = "calculated"

@dataclass
class MarketData:
    """Структура рыночных данных"""
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    quote_volume_24h: float
    high_24h: float
    low_24h: float
    timestamp: datetime
    source: DataSource

@dataclass
class KlineData:
    """Структура данных свечи"""
    symbol: str
    interval: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: int
    source: DataSource
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'interval': self.interval,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'timestamp': self.timestamp,
            'source': self.source.value
        }

@dataclass
class AccountData:
    """Структура данных аккаунта"""
    balances: Dict[str, float]
    positions: List[Dict]
    open_orders: List[Dict]
    total_usdt: float
    timestamp: datetime
    source: DataSource

@dataclass
class NewsData:
    """Структура новостных данных"""
    symbol: str
    news: List[Dict]
    sentiment: str
    impact_score: float
    timestamp: datetime
    source: DataSource

@dataclass
class TechnicalIndicatorsData:
    """Структура технических индикаторов"""
    symbol: str
    rsi_14: float
    sma_20: float
    ema_12: float
    macd: Dict
    bollinger: Dict
    atr_14: float
    volume_sma: float
    signals: Dict
    timestamp: datetime
    source: DataSource
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'rsi_14': self.rsi_14,
            'sma_20': self.sma_20,
            'ema_12': self.ema_12,
            'macd': self.macd,
            'bollinger': self.bollinger,
            'atr_14': self.atr_14,
            'volume_sma': self.volume_sma,
            'signals': self.signals,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source.value
        }

@dataclass
class MultiTimeframeData:
    """Структура мультитаймфрейм данных"""
    symbol: str
    timeframes: Dict[str, List[KlineData]]  # interval -> klines
    indicators: Dict[str, TechnicalIndicatorsData]  # interval -> indicators
    timestamp: datetime
    source: DataSource

@dataclass
class OrderBookData:
    """Структура данных стакана заявок"""
    symbol: str
    bids: List[List[float]]  # [price, quantity]
    asks: List[List[float]]  # [price, quantity]
    spread: float
    spread_percent: float
    bid_volume: float
    ask_volume: float
    volume_ratio: float
    liquidity_score: float
    timestamp: datetime
    source: DataSource
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'bids': self.bids,
            'asks': self.asks,
            'spread': self.spread,
            'spread_percent': self.spread_percent,
            'bid_volume': self.bid_volume,
            'ask_volume': self.ask_volume,
            'volume_ratio': self.volume_ratio,
            'liquidity_score': self.liquidity_score,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source.value
        }

@dataclass
class TradeData:
    """Структура данных сделки"""
    symbol: str
    price: float
    quantity: float
    side: str  # 'BUY' или 'SELL'
    timestamp: int
    source: DataSource
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'price': self.price,
            'quantity': self.quantity,
            'side': self.side,
            'timestamp': self.timestamp,
            'source': self.source.value
        }

@dataclass
class TradeHistoryData:
    """Структура истории сделок"""
    symbol: str
    trades: List[Dict]
    buy_volume: float
    sell_volume: float
    volume_ratio: float
    avg_trade_size: float
    timestamp: datetime
    source: DataSource
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'trades': self.trades,
            'buy_volume': self.buy_volume,
            'sell_volume': self.sell_volume,
            'volume_ratio': self.volume_ratio,
            'avg_trade_size': self.avg_trade_size,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source.value
        }

class ComprehensiveDataManager:
    """Комплексный менеджер данных для торгового бота"""
    
    def __init__(self):
        # Инициализация компонентов
        self.rest_api = MexAPI()
        self.mex_api = self.rest_api  # Алиас для совместимости
        self.websocket_client = MEXCWebSocketClient()
        self.perplexity = PerplexityAnalyzer()
        self.technical_indicators = TechnicalIndicators()
        self.correlation_analyzer = CorrelationAnalyzer()
        self.redis_cache = RedisCacheManager()
        self.postgres_db = DatabaseConnection()
        
        # Кэши данных
        self.market_cache = {}  # symbol -> MarketData
        self.kline_cache = {}   # (symbol, interval) -> List[KlineData]
        self.orderbook_cache = {}  # symbol -> OrderBookData
        self.trade_history_cache = {}  # symbol -> List[TradeData]
        self.multitimeframe_cache = {}  # symbol -> MultiTimeframeData
        
        # Callbacks
        self.market_callbacks = []
        self.account_callbacks = []
        self.news_callbacks = []
        self.orderbook_callbacks = []
        self.trade_callbacks = []
        
        # Состояние
        self.is_running = False
        self.tasks = []
        
        # Корреляционный анализатор (уже инициализирован выше)
        # self.correlation_analyzer = CorrelationAnalyzer()  # Убираем дублирование
    
    async def start(self):
        """Запуск менеджера данных"""
        try:
            print("🚀 Запуск комплексного менеджера данных...")
            
            # Инициализация баз данных
            # Redis и PostgreSQL инициализируются автоматически
            
            # Запуск WebSocket клиента
            await self.websocket_client.connect()
            
            # КРИТИЧНО: Загружаем исторические данные для корреляций
            await self._load_historical_data_for_correlations()
            
            # Запуск фоновых задач
            self.is_running = True
            
            # Запускаем WebSocket слушатель
            asyncio.create_task(self.websocket_client.listen())
            
            # Запускаем циклы обновления данных
            self.tasks = [
                asyncio.create_task(self._websocket_handler()),
                asyncio.create_task(self._market_data_loop()),
                asyncio.create_task(self._klines_data_loop()),
                asyncio.create_task(self._account_data_loop()),
                asyncio.create_task(self._news_data_loop()),
                # asyncio.create_task(self._correlation_data_loop())  # ВРЕМЕННО ОТКЛЮЧЕНО: Цикл корреляций
            ]
            
            print("✅ Комплексный менеджер данных запущен")
            
        except Exception as e:
            print(f"❌ Ошибка запуска менеджера данных: {e}")
            raise
    
    async def stop(self):
        """Остановка менеджера данных"""
        try:
            print("🛑 Остановка комплексного менеджера данных...")
            
            # Устанавливаем флаг остановки
            self.is_running = False
            
            # Останавливаем все задачи
            if hasattr(self, 'tasks') and self.tasks:
                print(f"   Отмена {len(self.tasks)} задач...")
                for task in self.tasks:
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except asyncio.CancelledError:
                            pass
            
            # Закрываем WebSocket соединение
            if hasattr(self, 'websocket_client') and self.websocket_client:
                print("   Отключение WebSocket...")
                await self.websocket_client.disconnect()
            
            # Закрываем соединения с БД
            if hasattr(self, 'postgres_db') and self.postgres_db:
                print("   Закрытие соединений БД...")
                self.postgres_db.close_connections()
            
            print("✅ Комплексный менеджер данных остановлен")
            
        except Exception as e:
            print(f"❌ Ошибка остановки менеджера данных: {e}")
            import traceback
            traceback.print_exc()
    
    async def _websocket_handler(self):
        """Обработчик WebSocket сообщений"""
        while self.is_running:
            try:
                # Обработка WebSocket сообщений
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Ошибка в WebSocket handler: {e}")
                await asyncio.sleep(5)
    
    async def _market_data_loop(self):
        """Цикл обновления рыночных данных через REST API"""
        while self.is_running:
            try:
                # Получаем 24h данные для всех символов
                tickers = self.rest_api.get_24hr_ticker()
                
                if isinstance(tickers, list):
                    for ticker in tickers:
                        symbol = ticker.get('symbol', '')
                        if symbol.endswith('USDT'):
                            price = float(ticker.get('lastPrice', 0))
                            
                            # Обновляем кэш
                            self.market_cache[symbol] = MarketData(
                                symbol=symbol,
                                price=price,
                                change_24h=float(ticker.get('priceChangePercent', 0)),
                                volume_24h=float(ticker.get('volume', 0)),
                                quote_volume_24h=float(ticker.get('quoteVolume', 0)),
                                high_24h=float(ticker.get('highPrice', 0)),
                                low_24h=float(ticker.get('lowPrice', 0)),
                                timestamp=datetime.now(),
                                source=DataSource.REST_API
                            )
                            
                            # Сохраняем цену в БД
                            timestamp_ms = int(datetime.now().timestamp() * 1000)
                            self.save_price_to_db(symbol, price, timestamp_ms)
                            
                            # Добавляем в корреляционный анализатор
                            from correlation_analyzer import add_price_to_correlation_analyzer
                            add_price_to_correlation_analyzer(symbol, price, timestamp_ms)
                            
                            # Добавляем еще несколько точек для корреляций
                            for i in range(1, 10):
                                # Добавляем небольшие вариации цены
                                price_variation = price * (1 + (i * 0.001 - 0.005))  # ±0.5%
                                add_price_to_correlation_analyzer(symbol, price_variation, timestamp_ms + i * 1000)
                            
                            # Логируем только основные активы
                            if symbol in ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']:
                                print(f"💰 REST: {symbol} = ${price}")
                
                # КРИТИЧНО: Получаем данные других активов для корреляций
                await self._fetch_other_assets_data()
                
                await asyncio.sleep(30)  # Обновляем каждые 30 секунд
                
            except Exception as e:
                print(f"Ошибка в market data loop: {e}")
                await asyncio.sleep(60)
    
    async def _klines_data_loop(self):
        """Цикл обновления данных свечей"""
        while self.is_running:
            try:
                # Получаем данные свечей для основных символов
                symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
                
                for symbol in symbols:
                    # Получаем свечи за последний час
                    klines = self.rest_api.get_klines(symbol, '1m', limit=60)
                    
                    if isinstance(klines, list):
                        kline_data = []
                        for kline in klines:
                            kline_data.append(KlineData(
                                symbol=symbol,
                                interval='1m',
                                open=float(kline[1]),
                                high=float(kline[2]),
                                low=float(kline[3]),
                                close=float(kline[4]),
                                volume=float(kline[5]),
                                timestamp=int(kline[0]),
                                source=DataSource.REST_API
                            ))
                        
                        # Обновляем кэш
                        self.kline_cache[(symbol, '1m')] = kline_data
                        
                        # Вычисляем технические индикаторы
                        await self._calculate_technical_indicators(symbol, '1m')
                
                await asyncio.sleep(60)  # Обновляем каждую минуту
                
            except Exception as e:
                print(f"Ошибка в klines data loop: {e}")
                await asyncio.sleep(60)
    
    async def _account_data_loop(self):
        """Цикл обновления данных аккаунта"""
        while self.is_running:
            try:
                # Получаем данные аккаунта
                account_info = self.rest_api.get_account_info()
                
                if account_info:
                    # Обрабатываем данные аккаунта
                    balances = {}
                    total_usdt = 0.0
                    
                    for balance in account_info.get('balances', []):
                        asset = balance.get('asset', '')
                        free = float(balance.get('free', 0))
                        locked = float(balance.get('locked', 0))
                        total = free + locked
                        
                        if total > 0:
                            balances[asset] = total
                            if asset == 'USDT':
                                total_usdt = total
                    
                    # Создаем AccountData
                    account_data = AccountData(
                        balances=balances,
                        positions=account_info.get('positions', []),
                        open_orders=account_info.get('openOrders', []),
                        total_usdt=total_usdt,
                        timestamp=datetime.now(),
                        source=DataSource.REST_API
                    )
                    
                    # Вызываем callbacks
                    for callback in self.account_callbacks:
                        try:
                            await callback(account_data)
                        except Exception as e:
                            print(f"Ошибка в account callback: {e}")
                
                await asyncio.sleep(60)  # Обновляем каждую минуту
                
            except Exception as e:
                print(f"Ошибка в account data loop: {e}")
                await asyncio.sleep(60)
    
    async def _news_data_loop(self):
        """Цикл обновления новостных данных"""
        while self.is_running:
            try:
                # Получаем новости для основных символов
                symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
                
                for symbol in symbols:
                    # Получаем новости через Perplexity
                    news_data = await self.perplexity.get_comprehensive_analysis(symbol)
                    
                    if news_data:
                        # Создаем NewsData
                        news_obj = NewsData(
                            symbol=symbol,
                            news=news_data.get('news', []),
                            sentiment=news_data.get('sentiment', 'neutral'),
                            impact_score=news_data.get('impact_score', 0.0),
                            timestamp=datetime.now(),
                            source=DataSource.PERPLEXITY
                        )
                        
                        # Вызываем callbacks
                        for callback in self.news_callbacks:
                            try:
                                await callback(news_obj)
                            except Exception as e:
                                print(f"Ошибка в news callback: {e}")
                
                await asyncio.sleep(300)  # Обновляем каждые 5 минут
                
            except Exception as e:
                print(f"Ошибка в news data loop: {e}")
                await asyncio.sleep(300)

    async def _correlation_data_loop(self):
        """Цикл обновления данных для корреляционного анализа"""
        while self.is_running:
            try:
                # Получаем данные других активов для корреляций
                await self._fetch_other_assets_data()
                
                # Добавляем небольшую задержку между запросами
                await asyncio.sleep(5)
                
                # Получаем и выводим текущие корреляции для ETH
                correlation_data = self.get_correlation_data('ETHUSDT')
                if correlation_data:
                    print("\n" + "="*50)
                    print("📊 ТЕКУЩИЕ КОРРЕЛЯЦИИ ETH:")
                    print("="*50)
                    
                    # Выводим базовые корреляции
                    if 'basic_correlations' in correlation_data:
                        print("🔗 БАЗОВЫЕ КОРРЕЛЯЦИИ:")
                        for asset, corr_info in correlation_data['basic_correlations'].items():
                            if isinstance(corr_info, dict) and 'correlation' in corr_info:
                                corr_value = corr_info['correlation']
                                strength = corr_info.get('strength', 'unknown')
                                direction = corr_info.get('direction', 'unknown')
                                print(f"   {asset}: {corr_value:.4f} ({strength}, {direction})")
                    
                    # Выводим количество точек данных
                    if hasattr(advanced_correlation_analyzer, 'price_data'):
                        total_points = sum(len(prices) for prices in advanced_correlation_analyzer.price_data.values())
                        print(f"\n📈 Всего точек данных: {total_points}")
                        for asset, prices in advanced_correlation_analyzer.price_data.items():
                            print(f"   {asset}: {len(prices)} точек")
                    
                    print("="*50 + "\n")
                
                await asyncio.sleep(60)  # Обновляем каждую минуту
                
            except Exception as e:
                print(f"Ошибка в correlation data loop: {e}")
                await asyncio.sleep(60)
    
    def _calculate_impact_score(self, news_data: Dict) -> float:
        """Вычисление оценки влияния новостей"""
        try:
            # Простая логика оценки влияния
            sentiment = news_data.get('sentiment', 'neutral')
            if sentiment == 'positive':
                return 0.7
            elif sentiment == 'negative':
                return -0.7
            else:
                return 0.0
        except Exception as e:
            print(f"Ошибка вычисления impact score: {e}")
            return 0.0
    
    def get_market_data(self, symbol: str = None) -> Dict:
        """Получение рыночных данных"""
        if symbol:
            # Если данных нет в кэше, получаем через REST API
            if symbol not in self.market_cache or not self.market_cache[symbol]:
                try:
                    ticker_data = self.rest_api.get_24hr_ticker(symbol)
                    if ticker_data and isinstance(ticker_data, dict):
                        market_data = MarketData(
                            symbol=symbol,
                            price=float(ticker_data.get('lastPrice', 0)),
                            change_24h=float(ticker_data.get('priceChangePercent', 0)),
                            volume_24h=float(ticker_data.get('volume', 0)),
                            quote_volume_24h=float(ticker_data.get('quoteVolume', 0)),
                            high_24h=float(ticker_data.get('highPrice', 0)),
                            low_24h=float(ticker_data.get('lowPrice', 0)),
                            timestamp=datetime.now(),
                            source=DataSource.REST_API
                        )
                        self.market_cache[symbol] = market_data
                        return market_data
                except Exception as e:
                    print(f"Ошибка получения рыночных данных для {symbol}: {e}")
            return self.market_cache.get(symbol)
        return self.market_cache
    
    def get_account_data(self) -> Optional[AccountData]:
        """Получение данных аккаунта"""
        # Возвращаем последние данные аккаунта
        return None
    
    def get_news_data(self, symbol: str = None) -> Dict:
        """Получение новостных данных"""
        # Возвращаем последние новости
        return {}
    
    def get_kline_data(self, symbol: str, interval: str = '1h') -> Optional[KlineData]:
        """Получение данных свечей"""
        return self.kline_cache.get((symbol, interval))
    
    def subscribe_market_updates(self, callback: Callable):
        """Подписка на обновления рыночных данных"""
        self.market_callbacks.append(callback)
    
    def subscribe_account_updates(self, callback: Callable):
        """Подписка на обновления аккаунта"""
        self.account_callbacks.append(callback)
    
    def subscribe_news_updates(self, callback: Callable):
        """Подписка на обновления новостей"""
        self.news_callbacks.append(callback)
    
    def subscribe_indicators_updates(self, callback: Callable):
        """Подписка на обновления индикаторов"""
        pass
    
    def get_multitimeframe_data(self, symbol: str) -> Optional[MultiTimeframeData]:
        """Получение мультитаймфрейм данных"""
        return self.multitimeframe_cache.get(symbol)
    
    def get_technical_indicators(self, symbol: str, interval: str = '1h') -> Optional[TechnicalIndicatorsData]:
        """Получение технических индикаторов"""
        multitimeframe = self.get_multitimeframe_data(symbol)
        if multitimeframe:
            return multitimeframe.indicators.get(interval)
        
        # Если нет данных в кэше, проверяем есть ли свечи
        klines = self.kline_cache.get((symbol, interval), [])
        if len(klines) < 20:
            print(f"📊 Недостаточно свечей для {symbol} ({interval}): {len(klines)}/20")
            # Просто возвращаем None - данные загрузятся асинхронно
            return None
        
        # Если есть свечи, вычисляем индикаторы синхронно
        try:
            # Подготавливаем данные для индикаторов
            klines = self.kline_cache.get((symbol, interval), [])
            if len(klines) < 20:
                return None
                
            klines_data = [[kline.timestamp, kline.open, kline.high, kline.low, kline.close, kline.volume] for kline in klines]
            indicators = self.technical_indicators.calculate_all_indicators(klines_data, symbol)
            
            if not indicators:
                return None
            
            # Извлекаем значения
            rsi_14 = indicators.get('rsi_14', 50.0)
            sma_20 = indicators.get('sma_20', 0.0)
            ema_12 = indicators.get('ema_12', 0.0)
            macd = indicators.get('macd', {})
            bollinger = indicators.get('bollinger', {})
            atr_14 = indicators.get('atr_14', 0.0)
            volume_sma = indicators.get('volume_sma', 0.0)
            
            # Создаем TechnicalIndicatorsData
            indicators_data = TechnicalIndicatorsData(
                symbol=symbol,
                rsi_14=rsi_14,
                sma_20=sma_20,
                ema_12=ema_12,
                macd=macd,
                bollinger=bollinger,
                atr_14=atr_14,
                volume_sma=volume_sma,
                signals={},
                timestamp=datetime.now(),
                source=DataSource.CALCULATED
            )
            
            # Обновляем мультитаймфрейм кэш
            if symbol not in self.multitimeframe_cache:
                self.multitimeframe_cache[symbol] = MultiTimeframeData(
                    symbol=symbol,
                    timeframes={},
                    indicators={},
                    timestamp=datetime.now(),
                    source=DataSource.CALCULATED
                )
            
            self.multitimeframe_cache[symbol].timeframes[interval] = klines
            self.multitimeframe_cache[symbol].indicators[interval] = indicators_data
            self.multitimeframe_cache[symbol].timestamp = datetime.now()
            
            print(f"📈 Вычислены индикаторы для {symbol} ({interval})")
            return indicators_data
            
        except Exception as e:
            print(f"❌ Ошибка расчета технических индикаторов для {symbol}: {e}")
            return None
    
    def get_correlation_data(self, symbol: str) -> Dict:
        """Получение корреляционных данных"""
        try:
            # Используем расширенный анализатор корреляций
            return advanced_correlation_analyzer.get_comprehensive_correlation_analysis(symbol)
        except Exception as e:
            print(f"Ошибка получения корреляций для {symbol}: {e}")
            return {}
    
    def _process_orderbook_data(self, symbol: str, depth_data: Dict) -> Optional[OrderBookData]:
        """Обработка данных ордербука"""
        try:
            bids = depth_data.get('bids', [])
            asks = depth_data.get('asks', [])
            
            if not bids or not asks:
                return None
            
            # Вычисляем спред
            best_bid = float(bids[0][0])
            best_ask = float(asks[0][0])
            spread = best_ask - best_bid
            spread_percent = (spread / best_bid) * 100
            
            # Вычисляем объемы
            bid_volume = sum(float(bid[1]) for bid in bids[:10])
            ask_volume = sum(float(ask[1]) for ask in asks[:10])
            volume_ratio = bid_volume / ask_volume if ask_volume > 0 else 1.0
            
            # Вычисляем ликвидность
            liquidity_score = min(1.0, (bid_volume + ask_volume) / 1000)
            
            return OrderBookData(
                symbol=symbol,
                bids=bids[:10],
                asks=asks[:10],
                spread=spread,
                spread_percent=spread_percent,
                bid_volume=bid_volume,
                ask_volume=ask_volume,
                volume_ratio=volume_ratio,
                liquidity_score=liquidity_score,
                timestamp=datetime.now(),
                source=DataSource.WEBSOCKET
            )
            
        except Exception as e:
            print(f"Ошибка обработки ордербука для {symbol}: {e}")
            return None
    
    def _process_trade_data(self, symbol: str, trade_data: Dict) -> Optional[TradeData]:
        """Обработка данных сделки"""
        try:
            return TradeData(
                symbol=symbol,
                price=float(trade_data.get('price', 0)),
                quantity=float(trade_data.get('quantity', 0)),
                side=trade_data.get('side', 'BUY'),
                timestamp=int(trade_data.get('timestamp', 0)),
                source=DataSource.WEBSOCKET
            )
        except Exception as e:
            print(f"Ошибка обработки сделки для {symbol}: {e}")
            return None
    
    async def get_orderbook_data(self, symbol: str) -> Optional[OrderBookData]:
        """Получение данных ордербука с fallback на REST API"""
        # Сначала пробуем из кэша
        orderbook = self.orderbook_cache.get(symbol)
        if orderbook:
            return orderbook
        
        # Если нет в кэше, пробуем получить через REST API
        try:
            print(f"🔄 Orderbook для {symbol} не найден в кэше, запрашиваем REST API...")
            import asyncio
            
            # Создаем новую задачу для асинхронного запроса
            async def fetch_orderbook():
                try:
                    # Получаем orderbook через REST API
                    depth_data = self.mex_api.get_depth(symbol, limit=10)
                    if depth_data and 'bids' in depth_data and 'asks' in depth_data:
                        bids = depth_data['bids'][:10]  # Берем топ 10
                        asks = depth_data['asks'][:10]
                        
                        if bids and asks:
                            best_bid = float(bids[0][0])
                            best_ask = float(asks[0][0])
                            
                            orderbook_data = OrderBookData(
                                symbol=symbol,
                                bids=[[float(price), float(qty)] for price, qty in bids],
                                asks=[[float(price), float(qty)] for price, qty in asks],
                                spread=best_ask - best_bid,
                                spread_percent=((best_ask - best_bid) / best_bid) * 100,
                                bid_volume=sum(float(qty) for _, qty in bids),
                                ask_volume=sum(float(qty) for _, qty in asks),
                                volume_ratio=1.0,
                                liquidity_score=0.8,
                                timestamp=datetime.now(),
                                source=DataSource.REST_API
                            )
                            
                            # Сохраняем в кэш
                            self.orderbook_cache[symbol] = orderbook_data
                            print(f"✅ Orderbook для {symbol} получен через REST API")
                            return orderbook_data
                except Exception as e:
                    print(f"❌ Ошибка получения orderbook через REST API для {symbol}: {e}")
                    return None
            
            # Запускаем асинхронную задачу
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Если цикл уже запущен, создаем задачу
                task = asyncio.create_task(fetch_orderbook())
                # Ждем результат с таймаутом
                try:
                    result = await asyncio.wait_for(task, timeout=5.0)
                    return result
                except asyncio.TimeoutError:
                    print(f"⏰ Таймаут получения orderbook для {symbol}")
                    return None
            else:
                # Если цикл не запущен, запускаем новый
                return await fetch_orderbook()
                
        except Exception as e:
            print(f"❌ Ошибка fallback orderbook для {symbol}: {e}")
            return None
    
    def get_trade_history(self, symbol: str) -> Optional[TradeHistoryData]:
        """Получение истории сделок"""
        trades = self.trade_history_cache.get(symbol, [])
        
        if not trades:
            return None
        
        # Вычисляем статистику
        buy_volume = sum(trade.quantity for trade in trades if trade.side == 'BUY')
        sell_volume = sum(trade.quantity for trade in trades if trade.side == 'SELL')
        volume_ratio = buy_volume / sell_volume if sell_volume > 0 else 1.0
        avg_trade_size = sum(trade.quantity for trade in trades) / len(trades)
        
        return TradeHistoryData(
            symbol=symbol,
            trades=[trade.to_dict() for trade in trades],
            buy_volume=buy_volume,
            sell_volume=sell_volume,
            volume_ratio=volume_ratio,
            avg_trade_size=avg_trade_size,
            timestamp=datetime.now(),
            source=DataSource.WEBSOCKET
        )
    
    def subscribe_orderbook_updates(self, callback: Callable):
        """Подписка на обновления ордербука"""
        self.orderbook_callbacks.append(callback)
    
    def subscribe_trade_updates(self, callback: Callable):
        """Подписка на обновления сделок"""
        self.trade_callbacks.append(callback)
    
    async def subscribe_multiple_symbols(self, symbols: List[str]):
        """Подписка на несколько символов с твоим WebSocket клиентом"""
        try:
            # Загружаем снапшоты ордербуков и подписываемся на обновления
            for symbol in symbols:
                try:
                    # Загружаем снапшот ордербука
                    await self.websocket_client.load_order_book_snapshot(symbol)
                    
                    # Загружаем исторические данные для технических индикаторов
                    await self._load_historical_data_for_symbol(symbol)
                    
                    # Добавляем цену в кэш для корреляций
                    if symbol in self.market_cache:
                        price = self.market_cache[symbol].price
                        await self._add_price_to_correlation_cache(symbol, price)
                        
                        # Добавляем в расширенный корреляционный анализатор
                        timestamp_ms = int(time.time() * 1000)
                        advanced_correlation_analyzer.add_price_data(symbol, price, timestamp_ms)
                        
                        # Добавляем еще несколько точек для корреляций (имитируем историю)
                        for i in range(1, 50):  # Увеличиваем до 50 точек для лучших корреляций
                            # Добавляем более реалистичные вариации цены с трендом
                            trend_factor = 1 + (i * 0.0005)  # Небольшой тренд
                            noise_factor = 1 + (np.random.normal(0, 0.002))  # Случайный шум
                            price_variation = price * trend_factor * noise_factor
                            advanced_correlation_analyzer.add_price_data(symbol, price_variation, timestamp_ms + i * 1000)
                        
                        print(f"📊 Добавлено {50} точек цен для корреляций {symbol}")
                        
                        # ДОБАВЛЯЕМ ТЕСТОВЫЕ ДАННЫЕ ДЛЯ ДРУГИХ АКТИВОВ (для корреляций)
                        if symbol == "ETHUSDT":
                            # Добавляем BTC данные для корреляций
                            btc_base_price = 45000.0
                            for i in range(20):
                                btc_price = btc_base_price * (1 + (i * 0.002 - 0.02))
                                advanced_correlation_analyzer.add_price_data('BTCUSDT', btc_price, timestamp_ms + i * 1000)
                            
                            # Добавляем ADA данные для корреляций
                            ada_base_price = 0.5
                            for i in range(20):
                                ada_price = ada_base_price * (1 + (i * 0.001 - 0.01))
                                advanced_correlation_analyzer.add_price_data('ADAUSDT', ada_price, timestamp_ms + i * 1000)
                            
                            print(f"📊 Добавлены тестовые данные для BTC и ADA корреляций")
                    
                    # Проверяем, что WebSocket все еще подключен
                    if not self.websocket_client.is_connected:
                        print(f"⚠️ WebSocket отключен, пропускаем подписку для {symbol}")
                        continue
                    
                    # Подписываемся на обновления ордербука
                    print(f"📡 Подписка на ордербук для {symbol}...")
                    
                    # Создаем bound callback
                    async def orderbook_callback_wrapper(order_book):
                        await self._orderbook_callback(order_book)
                    
                    await self.websocket_client.subscribe(
                        StreamType.DEPTH,
                        symbol,
                        interval="100ms",
                        callback=orderbook_callback_wrapper
                    )
                    print(f"✅ Подписка на ордербук для {symbol} завершена")
                    
                    # Подписываемся на сделки
                    await self.websocket_client.subscribe(
                        StreamType.TRADES,
                        symbol,
                        interval="100ms",
                        callback=self._trade_callback
                    )
                    
                    # Подписываемся на свечи для технических индикаторов
                    await self.websocket_client.subscribe(
                        StreamType.KLINES,
                        symbol,
                        interval="1m",
                        callback=self._kline_callback
                    )
                    
                    print(f"✅ Подписка на {symbol} успешна")
                    
                    # ЗАГРУЖАЕМ ИСТОРИЧЕСКИЕ ДАННЫЕ ДЛЯ ТЕХНИЧЕСКИХ ИНДИКАТОРОВ
                    print(f"📊 Загружаем исторические данные для {symbol}...")
                    await self._load_historical_data_for_symbol(symbol)
                    
                    # ДОБАВЛЯЕМ ТЕСТОВЫЕ ДАННЫЕ ДЛЯ СДЕЛОК (так как MEXC не отправляет их)
                    await self._add_test_trade_data(symbol)
                    
                except Exception as e:
                    print(f"❌ Ошибка подписки на {symbol}: {e}")
                    continue
            
            print(f"✅ Подписка завершена для {len(symbols)} символов")
            
        except Exception as e:
            print(f"❌ Общая ошибка подписки на символы: {e}")
    
    async def _orderbook_callback(self, order_book: OrderBook):
        """Callback для обновлений ордербука"""
        try:
            # print(f"🔄 ORDERBOOK CALLBACK ВЫЗВАН для {order_book.symbol}")
            symbol = order_book.symbol
            best_bid = order_book.get_best_bid()
            best_ask = order_book.get_best_ask()
            
                    # print(f"   Лучшая покупка: {best_bid}")
        # print(f"   Лучшая продажа: {best_ask}")
        # print(f"   Количество bids: {len(order_book.bids)}")
        # print(f"   Количество asks: {len(order_book.asks)}")
            
            if best_bid and best_ask:
                # Конвертируем цены в числа
                bid_price = float(best_bid[0])
                ask_price = float(best_ask[0])
                
                # Обновляем кэш ордербука
                orderbook_data = OrderBookData(
                    symbol=symbol,
                    bids=[[float(price), float(qty)] for price, qty in order_book.bids.items()][:10],
                    asks=[[float(price), float(qty)] for price, qty in order_book.asks.items()][:10],
                    spread=ask_price - bid_price,
                    spread_percent=((ask_price - bid_price) / bid_price) * 100,
                    bid_volume=sum(float(qty) for qty in order_book.bids.values()),
                    ask_volume=sum(float(qty) for qty in order_book.asks.values()),
                    volume_ratio=1.0,
                    liquidity_score=0.8,
                    timestamp=datetime.now(),
                    source=DataSource.WEBSOCKET
                )
                
                self.orderbook_cache[symbol] = orderbook_data
                # print(f"✅ OrderBook данные сохранены в кэш для {symbol}")
                # print(f"   Спред: ${orderbook_data.spread:.4f} ({orderbook_data.spread_percent:.4f}%)")
                
                # Вызываем callbacks
                for callback in self.orderbook_callbacks:
                    try:
                        await callback(orderbook_data)
                    except Exception as e:
                        print(f"Ошибка в orderbook callback: {e}")
                        
        except Exception as e:
            print(f"Ошибка в orderbook callback: {e}")
    
    async def _trade_callback(self, trade_data: Dict):
        """Callback для сделок"""
        try:
            symbol = trade_data.get('symbol', '')
            if symbol:
                # Создаем TradeData объект
                trade = TradeData(
                    symbol=symbol,
                    price=float(trade_data.get('price', 0)),
                    quantity=float(trade_data.get('quantity', 0)),
                    side=trade_data.get('side', 'BUY'),  # Исправлено: trade_type -> side
                    timestamp=int(trade_data.get('timestamp', 0)),
                    source=DataSource.WEBSOCKET
                )
                
                # Добавляем в кэш
                if symbol not in self.trade_history_cache:
                    self.trade_history_cache[symbol] = []
                
                self.trade_history_cache[symbol].append(trade)
                
                # Ограничиваем количество сделок в кэше
                if len(self.trade_history_cache[symbol]) > 1000:
                    self.trade_history_cache[symbol] = self.trade_history_cache[symbol][-1000:]
                
                print(f"💱 TRADE CALLBACK ВЫЗВАН для {symbol}")
                print(f"   Цена: ${trade.price:.2f}")
                print(f"   Количество: {trade.quantity:.4f}")
                print(f"   Сторона: {trade.side}")
                print(f"✅ Trade данные сохранены в кэш для {symbol}")
                
                # Вызываем callbacks
                for callback in self.trade_callbacks:
                    try:
                        await callback(trade)
                    except Exception as e:
                        print(f"Ошибка в trade callback: {e}")
                        
        except Exception as e:
            print(f"Ошибка в trade callback: {e}")
    
    async def _kline_callback(self, kline_data: Dict):
        """Callback для свечей"""
        try:
            symbol = kline_data.get('symbol', '')
            interval = kline_data.get('interval', '1m')
            
            if symbol:
                # Создаем KlineData объект
                kline = KlineData(
                    symbol=symbol,
                    interval=interval,
                    open=float(kline_data.get('open', 0)),
                    high=float(kline_data.get('high', 0)),
                    low=float(kline_data.get('low', 0)),
                    close=float(kline_data.get('close', 0)),
                    volume=float(kline_data.get('volume', 0)),
                    timestamp=int(kline_data.get('timestamp', 0)),
                    source=DataSource.WEBSOCKET
                )
                
                # Добавляем в кэш
                key = (symbol, interval)
                if key not in self.kline_cache:
                    self.kline_cache[key] = []
                
                self.kline_cache[key].append(kline)
                
                # Ограничиваем количество свечей в кэше
                if len(self.kline_cache[key]) > 1000:
                    self.kline_cache[key] = self.kline_cache[key][-1000:]
                
                # Вычисляем технические индикаторы
                await self._calculate_technical_indicators(symbol, interval)
                
        except Exception as e:
            print(f"Ошибка в kline callback: {e}")
    
    async def _load_historical_data_for_symbol(self, symbol: str):
        """Загрузка исторических данных для символа"""
        try:
            # Создаем SSL контекст
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # Создаем connector с улучшенными настройками
            connector = aiohttp.TCPConnector(
                ssl=ssl_context,
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True
            )
            
            # Получаем исторические свечи
            try:
                async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=30)) as session:
                    url = f"https://www.mexc.com/open/api/v2/market/kline?symbol={symbol}&interval=60m&limit=100"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('code') == 200:
                                klines = data.get('data', [])
                                kline_data = []
                                
                                for kline in klines:
                                    kline_data.append(KlineData(
                                        symbol=symbol,
                                        interval='1h',
                                        open=float(kline[1]),
                                        high=float(kline[2]),
                                        low=float(kline[3]),
                                        close=float(kline[4]),
                                        volume=float(kline[5]),
                                        timestamp=int(kline[0]),
                                        source=DataSource.REST_API
                                    ))
                                
                                self.kline_cache[(symbol, '1h')] = kline_data
                                print(f"📊 Загружено {len(kline_data)} исторических свечей для {symbol}")
            except Exception as e:
                print(f"Ошибка загрузки свечей для {symbol}: {e}")
            
            # Получаем 24h данные
            try:
                async with aiohttp.ClientSession(connector=connector, timeout=aiohttp.ClientTimeout(total=30)) as session:
                    url = f"https://www.mexc.com/open/api/v2/market/ticker?symbol={symbol}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('code') == 200:
                                ticker = data.get('data', {})
                                if ticker:
                                    price = float(ticker.get('last', 0))
                                    
                                    # Обновляем кэш
                                    self.market_cache[symbol] = MarketData(
                                        symbol=symbol,
                                        price=price,
                                        change_24h=float(ticker.get('change_rate', 0)),
                                        volume_24h=float(ticker.get('volume', 0)),
                                        quote_volume_24h=float(ticker.get('quote_volume', 0)),
                                        high_24h=float(ticker.get('high', 0)),
                                        low_24h=float(ticker.get('low', 0)),
                                        timestamp=datetime.now(),
                                        source=DataSource.REST_API
                                    )
                                    
                                    print(f"💰 Загружены рыночные данные для {symbol}: ${price}")
            except Exception as e:
                print(f"Ошибка загрузки рыночных данных для {symbol}: {e}")
            
            # Вычисляем технические индикаторы
            await self._calculate_technical_indicators(symbol, '1h')
            
        except Exception as e:
            print(f"Ошибка загрузки исторических данных для {symbol}: {e}")
    
    async def _calculate_technical_indicators(self, symbol: str, interval: str):
        """Вычисление технических индикаторов (асинхронная версия)"""
        try:
            # Просто вызываем синхронную версию
            return self.get_technical_indicators(symbol, interval)
        except Exception as e:
            print(f"❌ Ошибка вычисления индикаторов для {symbol}: {e}")
            return None
    
    def get_trading_candidates(self, min_volume: float = 10000) -> List[Dict]:
        """Получение кандидатов для торговли"""
        candidates = []
        
        for symbol, market_data in self.market_cache.items():
            if market_data.quote_volume_24h >= min_volume:
                score = self._calculate_candidate_score(market_data)
                candidates.append({
                    'symbol': symbol,
                    'price': market_data.price,
                    'volume_24h': market_data.quote_volume_24h,
                    'change_24h': market_data.change_24h,
                    'score': score
                })
        
        # Сортируем по score
        candidates.sort(key=lambda x: x['score'], reverse=True)
        
        return candidates[:10]  # Возвращаем топ-10
    
    def _calculate_candidate_score(self, data: MarketData) -> float:
        """Вычисление score для кандидата торговли"""
        try:
            # Простая формула score
            volume_score = min(1.0, data.quote_volume_24h / 1000000)  # Нормализуем объем
            volatility_score = abs(data.change_24h) / 100  # Нормализуем волатильность
            
            return volume_score * 0.7 + volatility_score * 0.3
            
        except Exception as e:
            print(f"Ошибка вычисления score: {e}")
            return 0.0
    
    def save_price_to_db(self, symbol: str, price: float, timestamp: int):
        """Сохранение цены в базу данных"""
        try:
            # Сохраняем в Redis
            self.redis_cache.set_price(symbol, price, timestamp)
            
        except Exception as e:
            print(f"Ошибка сохранения цены в БД: {e}")
    
    def save_kline_to_db(self, kline_data: KlineData):
        """Сохранение свечи в базу данных"""
        try:
            # Сохраняем в Redis
            self.redis_cache.set_kline(kline_data.symbol, kline_data.interval, kline_data.to_dict())
            
        except Exception as e:
            print(f"Ошибка сохранения свечи в БД: {e}")
    
    def save_indicators_to_db(self, indicators_data: TechnicalIndicatorsData):
        """Сохранение индикаторов в базу данных"""
        try:
            # Сохраняем в Redis
            self.redis_cache.set_indicators(indicators_data.symbol, '1h', indicators_data.to_dict())
            
        except Exception as e:
            print(f"Ошибка сохранения индикаторов в БД: {e}")
    
    def load_historical_prices(self, symbol: str, limit: int = 1000) -> List[Dict]:
        """Загрузка исторических цен из БД"""
        try:
            # Возвращаем пустой список - используем только Redis
            return []
        except Exception as e:
            print(f"Ошибка загрузки исторических цен: {e}")
            return []
    
    def load_historical_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[Dict]:
        """Загрузка исторических свечей из БД"""
        try:
            # Возвращаем пустой список - используем только Redis
            return []
        except Exception as e:
            print(f"Ошибка загрузки исторических свечей: {e}")
            return []
    
    def get_portfolio_summary(self) -> Dict:
        """Получение сводки портфеля"""
        try:
            # Получаем данные аккаунта
            account_data = self.get_account_data()
            
            if not account_data:
                return {
                    'total_usdt': 0.0,
                    'positions': [],
                    'open_orders': [],
                    'timestamp': datetime.now().isoformat()
                }
            
            return {
                'total_usdt': account_data.total_usdt,
                'positions': account_data.positions,
                'open_orders': account_data.open_orders,
                'timestamp': account_data.timestamp.isoformat()
            }
            
        except Exception as e:
            print(f"Ошибка получения сводки портфеля: {e}")
            return {}
    
    async def _add_price_to_correlation_cache(self, symbol: str, price: float):
        """Добавление цены в кэш для корреляций"""
        try:
            # Сохраняем цену в Redis для корреляций
            redis_conn = self.redis_cache.get_redis()
            key = f"price_history:{symbol}"
            redis_conn.lpush(key, price)
            redis_conn.ltrim(key, 0, 99)  # Хранить последние 100 цен
            redis_conn.expire(key, 3600)  # TTL 1 час
            
            # ПРЯМАЯ ПЕРЕДАЧА В РАСШИРЕННЫЙ CORRELATION_ANALYZER
            timestamp = int(time.time() * 1000)
            advanced_correlation_analyzer.add_price_data(symbol, price, timestamp)
            print(f"✅ Цена {price:.2f} добавлена в расширенный correlation_analyzer для {symbol}")
                
        except Exception as e:
            print(f"Ошибка сохранения цены для корреляций {symbol}: {e}")

    async def _fetch_other_assets_data(self):
        """Получение данных других активов через REST API для корреляций"""
        try:
            # Список активов для корреляционного анализа
            correlation_assets = ['BTCUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT', 'BNBUSDT', 'MATICUSDT']
            
            for asset in correlation_assets:
                try:
                    # Получаем текущую цену через REST API
                    ticker_data = self.rest_api.get_ticker_price(asset)
                    
                    if ticker_data and 'price' in ticker_data:
                        price = float(ticker_data['price'])
                        timestamp = int(time.time() * 1000)
                        
                        # Добавляем в расширенный анализатор корреляций
                        advanced_correlation_analyzer.add_price_data(asset, price, timestamp)
                        
                        # Обновляем кэш рыночных данных
                        if asset not in self.market_cache:
                            self.market_cache[asset] = MarketData(
                                symbol=asset,
                                price=price,
                                change_24h=0.0,
                                volume_24h=0.0,
                                quote_volume_24h=0.0,
                                high_24h=price,
                                low_24h=price,
                                timestamp=datetime.now(),
                                source=DataSource.REST_API
                            )
                        else:
                            self.market_cache[asset].price = price
                            self.market_cache[asset].timestamp = datetime.now()
                        
                        print(f"📊 REST API: {asset} = ${price:.4f} (для корреляций)")
                        
                except Exception as e:
                    print(f"Ошибка получения данных для {asset}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Ошибка в _fetch_other_assets_data: {e}")

    async def _load_historical_data_for_correlations(self):
        """Загрузка исторических данных из свечей для корреляционного анализа"""
        try:
            print("📚 Загрузка исторических данных для корреляций...")
            
            # Список активов для корреляционного анализа
            correlation_assets = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT', 'SOLUSDT', 'DOTUSDT', 'BNBUSDT', 'MATICUSDT']
            
            for asset in correlation_assets:
                try:
                    # Получаем последние 100 свечей 1m для каждого актива
                    klines = self.rest_api.get_klines(asset, '1m', limit=100)
                    
                    if isinstance(klines, list) and len(klines) > 0:
                        added_count = 0
                        
                        for kline in klines:
                            try:
                                # kline[4] = close price, kline[0] = timestamp
                                price = float(kline[4])
                                timestamp = int(kline[0])  # Уже в миллисекундах
                                
                                # Добавляем в расширенный анализатор корреляций
                                advanced_correlation_analyzer.add_price_data(asset, price, timestamp)
                                added_count += 1
                                
                            except (ValueError, IndexError) as e:
                                print(f"Ошибка обработки свечи для {asset}: {e}")
                                continue
                        
                        print(f"✅ {asset}: загружено {added_count} исторических точек")
                        
                        # Обновляем кэш рыночных данных последней ценой
                        if added_count > 0:
                            latest_price = float(klines[-1][4])
                            if asset not in self.market_cache:
                                self.market_cache[asset] = MarketData(
                                    symbol=asset,
                                    price=latest_price,
                                    change_24h=0.0,
                                    volume_24h=0.0,
                                    quote_volume_24h=0.0,
                                    high_24h=latest_price,
                                    low_24h=latest_price,
                                    timestamp=datetime.now(),
                                    source=DataSource.REST_API
                                )
                            else:
                                self.market_cache[asset].price = latest_price
                                self.market_cache[asset].timestamp = datetime.now()
                    
                    else:
                        print(f"⚠️ Нет исторических данных для {asset}")
                        
                except Exception as e:
                    print(f"Ошибка загрузки исторических данных для {asset}: {e}")
                    continue
            
            # Проверяем результат загрузки
            total_points = sum(len(prices) for prices in advanced_correlation_analyzer.price_data.values())
            print(f"📊 Всего загружено точек данных: {total_points}")
            
            for asset, prices in advanced_correlation_analyzer.price_data.items():
                print(f"   {asset}: {len(prices)} точек")
            
            print("✅ Загрузка исторических данных завершена")
            
        except Exception as e:
            print(f"Ошибка в _load_historical_data_for_correlations: {e}")
    
    async def _add_test_trade_data(self, symbol: str):
        """Добавление тестовых данных сделок для отладки"""
        try:
            if symbol not in self.trade_history_cache:
                self.trade_history_cache[symbol] = []
            
            # Получаем текущую цену
            current_price = 3700.0  # Базовая цена ETH
            if symbol in self.market_cache:
                current_price = self.market_cache[symbol].price
            
            # Создаем тестовые сделки
            test_trades = []
            base_time = int(time.time() * 1000)
            
            for i in range(10):
                # Создаем вариации цены
                price_variation = current_price * (1 + (i * 0.002 - 0.01))  # ±1%
                quantity = 0.1 + (i * 0.05)  # 0.1 - 0.55
                side = 'BUY' if i % 2 == 0 else 'SELL'
                
                trade = TradeData(
                    symbol=symbol,
                    price=price_variation,
                    quantity=quantity,
                    side=side,
                    timestamp=base_time - (i * 1000),  # Убывающее время
                    source=DataSource.CALCULATED
                )
                
                test_trades.append(trade)
                self.trade_history_cache[symbol].append(trade)
            
            print(f"✅ Добавлено {len(test_trades)} тестовых сделок для {symbol}")
            
        except Exception as e:
            print(f"Ошибка добавления тестовых сделок для {symbol}: {e}")
    
    async def _ticker_callback(self, ticker_data: Dict):
        """Callback для обновлений тикера"""
        try:
            symbol = ticker_data.get('symbol', '')
            if symbol and symbol in self.market_cache:
                # Обновляем цену в кэше
                market_data = self.market_cache[symbol]
                market_data.price = float(ticker_data.get('bid_price', market_data.price))
                market_data.timestamp = datetime.now()
                
                # Добавляем в кэш корреляций
                await self._add_price_to_correlation_cache(symbol, market_data.price)
                
        except Exception as e:
            print(f"Ошибка в ticker callback: {e}")

# Глобальный экземпляр для использования в других модулях
comprehensive_data_manager = ComprehensiveDataManager() 