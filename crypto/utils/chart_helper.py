"""
Утилиты для работы с графиками и визуализацией данных
"""

import logging
from typing import Dict, Any, List, Optional
import time
import json

# Получаем логгер для модуля
logger = logging.getLogger('crypto.utils.chart_helper')

class ChartHelper:
    """
    Класс для работы с графиками и визуализацией данных
    """
    
    @staticmethod
    def get_tradingview_chart_url(symbol: str, timeframe: str = "1D") -> str:
        """
        Генерирует URL для графика TradingView
        
        Args:
            symbol: Символ криптовалюты (например, BTC)
            timeframe: Временной интервал (например, 1D, 4H, 1H)
            
        Returns:
            str: URL для графика TradingView
        """
        # Преобразуем символ в формат TradingView
        if symbol.endswith('/USDT'):
            symbol = symbol.replace('/USDT', '')
        
        # Формируем URL
        url = f"https://www.tradingview.com/chart/?symbol=BINANCE:{symbol}USDT&interval={timeframe}"
        
        return url
    
    @staticmethod
    def format_price_change(change: float) -> str:
        """
        Форматирует изменение цены с соответствующим эмодзи
        
        Args:
            change: Процентное изменение цены
            
        Returns:
            str: Отформатированная строка с изменением цены
        """
        if change > 0:
            return f"🟢 +{change:.2f}%"
        elif change < 0:
            return f"🔴 {change:.2f}%"
        else:
            return f"⚪ {change:.2f}%"
    
    @staticmethod
    def format_volume_change(current: float, average: float) -> str:
        """
        Форматирует изменение объема с соответствующим эмодзи
        
        Args:
            current: Текущий объем
            average: Средний объем
            
        Returns:
            str: Отформатированная строка с изменением объема
        """
        if average == 0:
            return "⚪ N/A"
        
        change_ratio = current / average
        
        if change_ratio > 2.0:
            return f"🔥 +{(change_ratio - 1) * 100:.1f}%"
        elif change_ratio > 1.2:
            return f"🟢 +{(change_ratio - 1) * 100:.1f}%"
        elif change_ratio < 0.8:
            return f"🔴 -{(1 - change_ratio) * 100:.1f}%"
        else:
            return f"⚪ {(change_ratio - 1) * 100:.1f}%"
    
    @staticmethod
    def format_large_number(number: float) -> str:
        """
        Форматирует большое число в читаемый формат
        
        Args:
            number: Число для форматирования
            
        Returns:
            str: Отформатированная строка
        """
        if number >= 1_000_000_000:
            return f"{number / 1_000_000_000:.2f}B"
        elif number >= 1_000_000:
            return f"{number / 1_000_000:.2f}M"
        elif number >= 1_000:
            return f"{number / 1_000:.2f}K"
        else:
            return f"{number:.2f}"