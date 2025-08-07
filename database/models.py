"""
Модели данных для PostgreSQL
Структура таблиц для хранения торговых данных
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection

@dataclass
class PriceData:
    """Модель данных цены"""
    symbol: str
    price: float
    timestamp: int
    source: str
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class KlineData:
    """Модель данных свечи"""
    symbol: str
    interval: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    timestamp: int
    close_time: int
    quote_volume: float
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class TechnicalIndicator:
    """Модель технических индикаторов"""
    symbol: str
    interval: str
    rsi_14: float
    sma_20: float
    ema_12: float
    macd: Dict
    bollinger: Dict
    atr_14: float
    volume_sma: float
    signals: Dict
    timestamp: int
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        # Сериализуем сложные объекты
        data['macd'] = json.dumps(data['macd'])
        data['bollinger'] = json.dumps(data['bollinger'])
        data['signals'] = json.dumps(data['signals'])
        return data

@dataclass
class CorrelationData:
    """Модель корреляционных данных"""
    symbol: str
    correlations: Dict
    correlation_matrix: Dict
    market_correlation: float
    volatility_rank: int
    correlation_strength: str
    timestamp: int
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        # Сериализуем сложные объекты
        data['correlations'] = json.dumps(data['correlations'])
        data['correlation_matrix'] = json.dumps(data['correlation_matrix'])
        return data

@dataclass
class MarketData:
    """Модель рыночных данных"""
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    quote_volume_24h: float
    high_24h: float
    low_24h: float
    timestamp: int
    source: str
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class AccountData:
    """Модель данных аккаунта"""
    balances: Dict
    positions: List[Dict]
    open_orders: List[Dict]
    total_usdt: float
    timestamp: int
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        # Сериализуем сложные объекты
        data['balances'] = json.dumps(data['balances'])
        data['positions'] = json.dumps(data['positions'])
        data['open_orders'] = json.dumps(data['open_orders'])
        return data

@dataclass
class NewsData:
    """Модель новостных данных"""
    symbol: str
    news: List[Dict]
    sentiment: str
    impact_score: float
    timestamp: int
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['news'] = json.dumps(data['news'])
        return data

@dataclass
class OrderBookData:
    """Модель данных стакана заявок"""
    symbol: str
    bids: List[List[float]]  # [price, quantity]
    asks: List[List[float]]  # [price, quantity]
    spread: float
    spread_percent: float
    bid_volume: float
    ask_volume: float
    volume_ratio: float
    liquidity_score: float
    timestamp: int
    source: str
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        # Сериализуем списки bids и asks
        data['bids'] = json.dumps(data['bids'])
        data['asks'] = json.dumps(data['asks'])
        return data

@dataclass
class TradeData:
    """Модель данных сделки"""
    symbol: str
    price: float
    quantity: float
    side: str  # 'BUY' или 'SELL'
    timestamp: int
    source: str
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class TradeHistoryData:
    """Модель истории сделок"""
    symbol: str
    trades: List[Dict]
    buy_volume: float
    sell_volume: float
    volume_ratio: float
    avg_trade_size: float
    timestamp: int
    source: str
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        # Сериализуем список сделок
        data['trades'] = json.dumps(data['trades'])
        return data


class DatabaseModels:
    """Класс для работы с моделями данных в БД"""
    
    def __init__(self):
        self.db = get_db_connection()
    
    def create_tables(self):
        """Создание всех таблиц"""
        self._create_prices_table()
        self._create_klines_table()
        self._create_indicators_table()
        self._create_correlations_table()
        self._create_market_data_table()
        self._create_account_data_table()
        self._create_news_data_table()
        self._create_orderbook_table()
        self._create_trades_table()
        self._create_trade_history_table()
        print("✅ Все таблицы созданы")
    
    def _create_prices_table(self):
        """Создание таблицы цен"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prices (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    price DECIMAL(20,8) NOT NULL,
                    timestamp BIGINT NOT NULL,
                    source VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_prices_symbol_timestamp 
                ON prices(symbol, timestamp);
            """)
    
    def _create_klines_table(self):
        """Создание таблицы свечей"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS klines (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    interval VARCHAR(10) NOT NULL,
                    open DECIMAL(20,8) NOT NULL,
                    high DECIMAL(20,8) NOT NULL,
                    low DECIMAL(20,8) NOT NULL,
                    close DECIMAL(20,8) NOT NULL,
                    volume DECIMAL(20,8) NOT NULL,
                    timestamp BIGINT NOT NULL,
                    close_time BIGINT NOT NULL,
                    quote_volume DECIMAL(20,8) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_klines_symbol_interval_timestamp 
                ON klines(symbol, interval, timestamp);
            """)
    
    def _create_indicators_table(self):
        """Создание таблицы технических индикаторов"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS technical_indicators (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    interval VARCHAR(10) NOT NULL,
                    rsi_14 DECIMAL(10,4),
                    sma_20 DECIMAL(20,8),
                    ema_12 DECIMAL(20,8),
                    macd JSONB,
                    bollinger JSONB,
                    atr_14 DECIMAL(20,8),
                    volume_sma DECIMAL(20,8),
                    signals JSONB,
                    timestamp BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_indicators_symbol_interval_timestamp 
                ON technical_indicators(symbol, interval, timestamp);
            """)
    
    def _create_correlations_table(self):
        """Создание таблицы корреляций"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS correlations (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    correlations JSONB,
                    correlation_matrix JSONB,
                    market_correlation DECIMAL(10,4),
                    volatility_rank INTEGER,
                    correlation_strength VARCHAR(20),
                    timestamp BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_correlations_symbol_timestamp 
                ON correlations(symbol, timestamp);
            """)
    
    def _create_market_data_table(self):
        """Создание таблицы рыночных данных"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS market_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    price DECIMAL(20,8) NOT NULL,
                    change_24h DECIMAL(10,4),
                    volume_24h DECIMAL(20,8),
                    quote_volume_24h DECIMAL(20,8),
                    high_24h DECIMAL(20,8),
                    low_24h DECIMAL(20,8),
                    timestamp BIGINT NOT NULL,
                    source VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_market_data_symbol_timestamp 
                ON market_data(symbol, timestamp);
            """)
    
    def _create_account_data_table(self):
        """Создание таблицы данных аккаунта"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS account_data (
                    id SERIAL PRIMARY KEY,
                    balances JSONB,
                    positions JSONB,
                    open_orders JSONB,
                    total_usdt DECIMAL(20,8),
                    timestamp BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_account_data_timestamp 
                ON account_data(timestamp);
            """)
    
    def _create_news_data_table(self):
        """Создание таблицы новостных данных"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    news JSONB,
                    sentiment VARCHAR(20),
                    impact_score DECIMAL(5,4),
                    timestamp BIGINT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_news_data_symbol_timestamp 
                ON news_data(symbol, timestamp);
            """)
    
    def _create_orderbook_table(self):
        """Создание таблицы Order Book данных"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS orderbook_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    bids JSONB,
                    asks JSONB,
                    spread DECIMAL(20,8),
                    spread_percent DECIMAL(10,6),
                    bid_volume DECIMAL(20,8),
                    ask_volume DECIMAL(20,8),
                    volume_ratio DECIMAL(10,4),
                    liquidity_score DECIMAL(5,4),
                    timestamp BIGINT NOT NULL,
                    source VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_orderbook_symbol_timestamp 
                ON orderbook_data(symbol, timestamp);
            """)
    
    def _create_trades_table(self):
        """Создание таблицы данных сделок"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    price DECIMAL(20,8) NOT NULL,
                    quantity DECIMAL(20,8) NOT NULL,
                    side VARCHAR(10) NOT NULL,
                    timestamp BIGINT NOT NULL,
                    source VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_trades_symbol_timestamp 
                ON trades_data(symbol, timestamp);
            """)
    
    def _create_trade_history_table(self):
        """Создание таблицы истории сделок"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trade_history_data (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    trades JSONB,
                    buy_volume DECIMAL(20,8),
                    sell_volume DECIMAL(20,8),
                    volume_ratio DECIMAL(10,4),
                    avg_trade_size DECIMAL(20,8),
                    timestamp BIGINT NOT NULL,
                    source VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_trade_history_symbol_timestamp 
                ON trade_history_data(symbol, timestamp);
            """)
    
    def drop_all_tables(self):
        """Удаление всех таблиц (для тестирования)"""
        tables = [
            'prices', 'klines', 'technical_indicators', 'correlations',
            'market_data', 'account_data', 'news_data', 'orderbook_data',
            'trades_data', 'trade_history_data'
        ]
        
        with self.db.get_cursor() as cursor:
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")
        
        print("🗑️ Все таблицы удалены")


# Глобальный экземпляр для использования в других модулях
db_models = DatabaseModels()


if __name__ == "__main__":
    # Тест создания таблиц
    models = DatabaseModels()
    models.create_tables()
    
    print("✅ Модели БД готовы к использованию") 