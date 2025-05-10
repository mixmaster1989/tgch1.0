"""
Корневой модуль Smart Money Crypto Trading Bot
Содержит основные компоненты бота
"""

# Экспорт основных классов для удобного импорта
from bot.analytics.smart_money import SmartMoneySignal
from bot.data.websocket_binance import BinanceWebSocketHandler
from bot.notification.signal_formatter import format_signal, get_keyboard
from bot.risk.confidence import ConfidenceCalculator

__all__ = [
    'SmartMoneySignal',
    'BinanceWebSocketHandler',
    'format_signal',
    'get_keyboard',
    'ConfidenceCalculator'
]