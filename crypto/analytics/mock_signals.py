"""
Модуль для генерации тестовых сигналов Smart Money
"""

import logging
import uuid
from datetime import datetime
from typing import List

from ..models import CryptoSignal, SignalType, SignalDirection

# Получаем логгер для модуля
logger = logging.getLogger('crypto.analytics.mock_signals')

class MockSignalGenerator:
    """
    Класс для генерации тестовых сигналов Smart Money
    """
   #ебать! 
    @staticmethod
    def generate_volume_spike_signals() -> List[CryptoSignal]:
        """
        Генерирует тестовые сигналы о всплесках объема
        
        Returns:
            List[CryptoSignal]: Список тестовых сигналов
        """
        signals = []
        
        # Создаем несколько тестовых сигналов для популярных монет
        test_data = [
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "price": 65000.0,
                "volume_24h": 45000000000.0,
                "avg_volume_7d": 30000000000.0,
                "price_change_24h": 2.5,
                "direction": SignalDirection.LONG
            },
            {
                "symbol": "ETH",
                "name": "Ethereum",
                "price": 3500.0,
                "volume_24h": 20000000000.0,
                "avg_volume_7d": 12000000000.0,
                "price_change_24h": 3.8,
                "direction": SignalDirection.LONG
            },
            {
                "symbol": "SOL",
                "name": "Solana",
                "price": 140.0,
                "volume_24h": 5000000000.0,
                "avg_volume_7d": 2000000000.0,
                "price_change_24h": 7.2,
                "direction": SignalDirection.LONG
            },
            {
                "symbol": "DOGE",
                "name": "Dogecoin",
                "price": 0.12,
                "volume_24h": 3000000000.0,
                "avg_volume_7d": 1000000000.0,
                "price_change_24h": 15.0,
                "direction": SignalDirection.LONG
            },
            {
                "symbol": "ADA",
                "name": "Cardano",
                "price": 0.45,
                "volume_24h": 1500000000.0,
                "avg_volume_7d": 800000000.0,
                "price_change_24h": -2.3,
                "direction": SignalDirection.SHORT
            }
        ]
        
        for data in test_data:
            volume_ratio = data["volume_24h"] / data["avg_volume_7d"]
            
            signal = CryptoSignal(
                id=str(uuid.uuid4()),
                pair=f"{data['symbol']}/USDT",
                timestamp=datetime.now(),
                signal_type=SignalType.VOLUME_SPIKE,
                direction=data["direction"],
                price=data["price"],
                confidence=min(volume_ratio / 1.5, 1.0),  # Нормализуем уверенность
                description=f"[ТЕСТОВЫЙ СИГНАЛ] Обнаружен всплеск объема для {data['name']} ({data['symbol']}). "
                           f"Текущий объем в {volume_ratio:.2f}x раз выше среднего за 7 дней.",
                metadata={
                    'volume_24h': data["volume_24h"],
                    'avg_volume_7d': data["avg_volume_7d"],
                    'volume_ratio': volume_ratio,
                    'price_change_24h': data["price_change_24h"],
                    'is_test': True
                }
            )
            
            signals.append(signal)
            logger.info(f"Создан тестовый сигнал о всплеске объема для {data['symbol']}")
        
        return signals
    
    @staticmethod
    def generate_price_breakout_signals() -> List[CryptoSignal]:
        """
        Генерирует тестовые сигналы о прорывах цены
        
        Returns:
            List[CryptoSignal]: Список тестовых сигналов
        """
        signals = []
        
        # Создаем несколько тестовых сигналов для популярных монет
        test_data = [
            {
                "symbol": "BNB",
                "name": "Binance Coin",
                "price": 580.0,
                "breakout_level": 550.0,
                "breakout_type": "сопротивления",
                "direction": SignalDirection.LONG
            },
            {
                "symbol": "XRP",
                "name": "Ripple",
                "price": 0.58,
                "breakout_level": 0.55,
                "breakout_type": "сопротивления",
                "direction": SignalDirection.LONG
            },
            {
                "symbol": "AVAX",
                "name": "Avalanche",
                "price": 35.0,
                "breakout_level": 38.0,
                "breakout_type": "поддержки",
                "direction": SignalDirection.SHORT
            }
        ]
        
        for data in test_data:
            breakout_percent = abs((data["price"] - data["breakout_level"]) / data["breakout_level"] * 100)
            
            signal = CryptoSignal(
                id=str(uuid.uuid4()),
                pair=f"{data['symbol']}/USDT",
                timestamp=datetime.now(),
                signal_type=SignalType.PRICE_BREAKOUT,
                direction=data["direction"],
                price=data["price"],
                confidence=min(breakout_percent / 5.0, 1.0),  # Нормализуем уверенность
                description=f"[ТЕСТОВЫЙ СИГНАЛ] Обнаружен прорыв уровня {data['breakout_type']} для {data['name']} ({data['symbol']}). "
                           f"Текущая цена: {data['price']:.4f}, уровень {data['breakout_type']}: {data['breakout_level']:.4f}, "
                           f"прорыв: {breakout_percent:.2f}%",
                metadata={
                    'current_price': data["price"],
                    'breakout_level': data["breakout_level"],
                    'breakout_percent': breakout_percent,
                    'breakout_type': data["breakout_type"],
                    'is_test': True
                }
            )
            
            signals.append(signal)
            logger.info(f"Создан тестовый сигнал о прорыве цены для {data['symbol']}")
        
        return signals