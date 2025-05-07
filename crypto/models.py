"""
Модели данных для криптомодуля
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

class SignalType(Enum):
    """Типы сигналов"""
    VOLUME_SPIKE = "volume_spike"
    LARGE_ORDER = "large_order"
    FUNDING_RATE = "funding_rate"
    SMART_MONEY = "smart_money"

class SignalDirection(Enum):
    """Направления сигналов"""
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"

@dataclass
class CryptoSignal:
    """Модель для представления криптовалютного сигнала"""
    id: str  # Уникальный идентификатор сигнала
    pair: str  # Торговая пара (например, BTC/USDT)
    timestamp: datetime  # Время создания сигнала
    signal_type: SignalType  # Тип сигнала
    direction: SignalDirection  # Направление сигнала (long/short)
    price: float  # Цена в момент сигнала
    confidence: float  # Уровень уверенности (0.0-1.0)
    description: str  # Описание сигнала
    metadata: Dict[str, Any]  # Дополнительные данные
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует сигнал в словарь для сериализации
        
        Returns:
            Dict[str, Any]: Словарь с данными сигнала
        """
        return {
            'id': self.id,
            'pair': self.pair,
            'timestamp': self.timestamp.isoformat(),
            'signal_type': self.signal_type.value,
            'direction': self.direction.value,
            'price': self.price,
            'confidence': self.confidence,
            'description': self.description,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CryptoSignal':
        """
        Создает экземпляр сигнала из словаря
        
        Args:
            data: Словарь с данными сигнала
            
        Returns:
            CryptoSignal: Экземпляр сигнала
        """
        return cls(
            id=data['id'],
            pair=data['pair'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            signal_type=SignalType(data['signal_type']),
            direction=SignalDirection(data['direction']),
            price=data['price'],
            confidence=data['confidence'],
            description=data['description'],
            metadata=data['metadata']
        )

@dataclass
class MarketOverview:
    """Модель для представления обзора рынка"""
    timestamp: datetime  # Время создания обзора
    total_market_cap: float  # Общая капитализация рынка
    btc_dominance: float  # Доминирование BTC
    total_volume_24h: float  # Общий объем торгов за 24 часа
    top_gainers: List[Dict[str, Any]]  # Топ растущих монет
    top_losers: List[Dict[str, Any]]  # Топ падающих монет
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует обзор рынка в словарь для сериализации
        
        Returns:
            Dict[str, Any]: Словарь с данными обзора
        """
        return {
            'timestamp': self.timestamp.isoformat(),
            'total_market_cap': self.total_market_cap,
            'btc_dominance': self.btc_dominance,
            'total_volume_24h': self.total_volume_24h,
            'top_gainers': self.top_gainers,
            'top_losers': self.top_losers
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MarketOverview':
        """
        Создает экземпляр обзора рынка из словаря
        
        Args:
            data: Словарь с данными обзора
            
        Returns:
            MarketOverview: Экземпляр обзора рынка
        """
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            total_market_cap=data['total_market_cap'],
            btc_dominance=data['btc_dominance'],
            total_volume_24h=data['total_volume_24h'],
            top_gainers=data['top_gainers'],
            top_losers=data['top_losers']
        )