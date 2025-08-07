"""
Технические индикаторы для торгового бота MEX
Модуль для расчета всех необходимых технических индикаторов
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """Класс для расчета технических индикаторов"""
    
    def __init__(self):
        """Инициализация калькулятора индикаторов"""
        self.cache = {}  # Кэш для оптимизации расчетов
        
    def calculate_all_indicators(self, klines_data: List[List], symbol: str) -> Dict:
        """
        Расчет всех технических индикаторов для символа
        
        Args:
            klines_data: Список свечей [timestamp, open, high, low, close, volume]
            symbol: Торговый символ
            
        Returns:
            Dict с всеми индикаторами
        """
        try:
            # Конвертируем в DataFrame для удобства
            df = self._prepare_dataframe(klines_data)
            
            if df.empty:
                logger.warning(f"Нет данных для расчета индикаторов: {symbol}")
                return {}
            
            indicators = {
                'symbol': symbol,
                'timestamp': int(df.index[-1].timestamp() * 1000),
                'price': float(df['close'].iloc[-1]),
                'volume': float(df['volume'].iloc[-1])
            }
            
            # Базовые индикаторы
            indicators.update(self._calculate_rsi(df))
            indicators.update(self._calculate_moving_averages(df))
            indicators.update(self._calculate_macd(df))
            indicators.update(self._calculate_bollinger_bands(df))
            indicators.update(self._calculate_atr(df))
            indicators.update(self._calculate_volume_indicators(df))
            
            # Кэшируем результат
            self.cache[symbol] = indicators
            
            return indicators
            
        except Exception as e:
            logger.error(f"Ошибка расчета индикаторов для {symbol}: {e}")
            return {}
    
    def _prepare_dataframe(self, klines_data: List[List]) -> pd.DataFrame:
        """Подготовка DataFrame из данных свечей"""
        if not klines_data:
            return pd.DataFrame()
            
        # MEX API возвращает список списков: [timestamp, open, high, low, close, volume, close_time, quote_volume]
        # Проверяем формат данных
        if not klines_data or not isinstance(klines_data[0], list):
            return pd.DataFrame()
        
        # Определяем количество колонок
        num_columns = len(klines_data[0])
        
        if num_columns == 6:
            # Старый формат: [timestamp, open, high, low, close, volume]
            df = pd.DataFrame(klines_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume'
            ])
        elif num_columns == 8:
            # MEX API формат: [timestamp, open, high, low, close, volume, close_time, quote_volume]
            df = pd.DataFrame(klines_data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_volume'
            ])
            # Оставляем только нужные колонки
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
        else:
            logger.error(f"Неизвестный формат данных: {num_columns} колонок")
            return pd.DataFrame()
        
        # Конвертируем типы
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df.set_index('timestamp', inplace=True)
        return df
    
    def _calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> Dict:
        """Расчет RSI (Relative Strength Index)"""
        try:
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return {
                'rsi_14': float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0,
                'rsi_trend': 'bullish' if rsi.iloc[-1] > 70 else 'bearish' if rsi.iloc[-1] < 30 else 'neutral'
            }
        except Exception as e:
            logger.error(f"Ошибка расчета RSI: {e}")
            return {'rsi_14': 50.0, 'rsi_trend': 'neutral'}
    
    def _calculate_moving_averages(self, df: pd.DataFrame) -> Dict:
        """Расчет скользящих средних"""
        try:
            sma_20 = df['close'].rolling(window=20).mean()
            sma_50 = df['close'].rolling(window=50).mean()
            ema_12 = df['close'].ewm(span=12).mean()
            ema_26 = df['close'].ewm(span=26).mean()
            
            return {
                'sma_20': float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else 0.0,
                'sma_50': float(sma_50.iloc[-1]) if not pd.isna(sma_50.iloc[-1]) else 0.0,
                'ema_12': float(ema_12.iloc[-1]) if not pd.isna(ema_12.iloc[-1]) else 0.0,
                'ema_26': float(ema_26.iloc[-1]) if not pd.isna(ema_26.iloc[-1]) else 0.0,
                'ma_trend': 'bullish' if sma_20.iloc[-1] > sma_50.iloc[-1] else 'bearish'
            }
        except Exception as e:
            logger.error(f"Ошибка расчета MA: {e}")
            return {
                'sma_20': 0.0, 'sma_50': 0.0, 'ema_12': 0.0, 'ema_26': 0.0, 'ma_trend': 'neutral'
            }
    
    def _calculate_macd(self, df: pd.DataFrame) -> Dict:
        """Расчет MACD (Moving Average Convergence Divergence)"""
        try:
            ema_12 = df['close'].ewm(span=12).mean()
            ema_26 = df['close'].ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()
            histogram = macd_line - signal_line
            
            return {
                'macd': {
                    'macd': float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else 0.0,
                    'signal': float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else 0.0,
                    'histogram': float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else 0.0
                },
                'macd_signal': 'buy' if histogram.iloc[-1] > 0 and histogram.iloc[-2] <= 0 else 
                              'sell' if histogram.iloc[-1] < 0 and histogram.iloc[-2] >= 0 else 'hold'
            }
        except Exception as e:
            logger.error(f"Ошибка расчета MACD: {e}")
            return {
                'macd': {'macd': 0.0, 'signal': 0.0, 'histogram': 0.0},
                'macd_signal': 'hold'
            }
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> Dict:
        """Расчет полос Боллинджера"""
        try:
            sma = df['close'].rolling(window=period).mean()
            std = df['close'].rolling(window=period).std()
            
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)
            
            current_price = df['close'].iloc[-1]
            band_width = upper_band.iloc[-1] - lower_band.iloc[-1]
            
            if band_width > 0:
                bb_position = (current_price - lower_band.iloc[-1]) / band_width
            else:
                bb_position = 0.5  # По умолчанию в середине
            
            return {
                'bollinger': {
                    'upper': float(upper_band.iloc[-1]) if not pd.isna(upper_band.iloc[-1]) else 0.0,
                    'middle': float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else 0.0,
                    'lower': float(lower_band.iloc[-1]) if not pd.isna(lower_band.iloc[-1]) else 0.0
                },
                'bb_position': float(bb_position) if not pd.isna(bb_position) else 0.5,
                'bb_signal': 'oversold' if bb_position < 0.2 else 'overbought' if bb_position > 0.8 else 'neutral'
            }
        except Exception as e:
            logger.error(f"Ошибка расчета Bollinger Bands: {e}")
            return {
                'bollinger': {'upper': 0.0, 'middle': 0.0, 'lower': 0.0},
                'bb_position': 0.5, 'bb_signal': 'neutral'
            }
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> Dict:
        """Расчет ATR (Average True Range)"""
        try:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            
            true_range = np.maximum(high_low, np.maximum(high_close, low_close))
            atr = true_range.rolling(window=period).mean()
            
            return {
                'atr_14': float(atr.iloc[-1]) if not pd.isna(atr.iloc[-1]) else 0.0,
                'volatility': 'high' if atr.iloc[-1] > atr.iloc[-5] * 1.5 else 
                             'low' if atr.iloc[-1] < atr.iloc[-5] * 0.5 else 'normal'
            }
        except Exception as e:
            logger.error(f"Ошибка расчета ATR: {e}")
            return {'atr_14': 0.0, 'volatility': 'normal'}
    
    def _calculate_volume_indicators(self, df: pd.DataFrame) -> Dict:
        """Расчет индикаторов объема"""
        try:
            volume_sma = df['volume'].rolling(window=20).mean()
            volume_ratio = df['volume'].iloc[-1] / volume_sma.iloc[-1] if volume_sma.iloc[-1] > 0 else 1.0
            
            # Volume Price Trend
            vpt = (df['volume'] * ((df['close'] - df['close'].shift(1)) / df['close'].shift(1))).cumsum()
            
            return {
                'volume_sma': float(volume_sma.iloc[-1]) if not pd.isna(volume_sma.iloc[-1]) else 0.0,
                'volume_ratio': float(volume_ratio),
                'volume_trend': 'high' if volume_ratio > 1.5 else 'low' if volume_ratio < 0.5 else 'normal',
                'vpt': float(vpt.iloc[-1]) if not pd.isna(vpt.iloc[-1]) else 0.0
            }
        except Exception as e:
            logger.error(f"Ошибка расчета Volume: {e}")
            return {
                'volume_sma': 0.0, 'volume_ratio': 1.0, 'volume_trend': 'normal', 'vpt': 0.0
            }
    
    def get_cached_indicators(self, symbol: str) -> Optional[Dict]:
        """Получение кэшированных индикаторов"""
        return self.cache.get(symbol)
    
    def clear_cache(self, symbol: Optional[str] = None):
        """Очистка кэша"""
        if symbol:
            self.cache.pop(symbol, None)
        else:
            self.cache.clear()
    
    def get_signal_summary(self, indicators: Dict) -> Dict:
        """Получение сводки сигналов"""
        if not indicators:
            return {'overall_signal': 'neutral', 'confidence': 0.0}
        
        signals = []
        confidence = 0.0
        
        # RSI сигналы
        rsi = indicators.get('rsi_14', 50)
        if rsi < 30:
            signals.append('buy')
            confidence += 0.2
        elif rsi > 70:
            signals.append('sell')
            confidence += 0.2
        
        # MACD сигналы
        macd_signal = indicators.get('macd_signal', 'hold')
        if macd_signal != 'hold':
            signals.append(macd_signal)
            confidence += 0.2
        
        # Bollinger Bands сигналы
        bb_signal = indicators.get('bb_signal', 'neutral')
        if bb_signal == 'oversold':
            signals.append('buy')
            confidence += 0.15
        elif bb_signal == 'overbought':
            signals.append('sell')
            confidence += 0.15
        
        # MA тренд
        ma_trend = indicators.get('ma_trend', 'neutral')
        if ma_trend == 'bullish':
            signals.append('buy')
            confidence += 0.1
        elif ma_trend == 'bearish':
            signals.append('sell')
            confidence += 0.1
        
        # Определяем общий сигнал
        buy_count = signals.count('buy')
        sell_count = signals.count('sell')
        
        if buy_count > sell_count:
            overall_signal = 'buy'
        elif sell_count > buy_count:
            overall_signal = 'sell'
        else:
            overall_signal = 'hold'
        
        return {
            'overall_signal': overall_signal,
            'confidence': min(confidence, 1.0),
            'buy_signals': buy_count,
            'sell_signals': sell_count,
            'total_signals': len(signals)
        }


# Глобальный экземпляр для использования в других модулях
technical_indicators = TechnicalIndicators()


def calculate_indicators_for_symbol(klines_data: List[List], symbol: str) -> Dict:
    """
    Удобная функция для расчета индикаторов
    
    Args:
        klines_data: Данные свечей
        symbol: Торговый символ
        
    Returns:
        Dict с индикаторами и сигналами
    """
    indicators = technical_indicators.calculate_all_indicators(klines_data, symbol)
    if indicators:
        indicators['signals'] = technical_indicators.get_signal_summary(indicators)
    return indicators


if __name__ == "__main__":
    # Тестовые данные
    test_klines = [
        [1640995200000, "46200.00", "46200.00", "46100.00", "46150.00", "100.5"],
        [1640995260000, "46150.00", "46250.00", "46100.00", "46200.00", "150.2"],
        [1640995320000, "46200.00", "46300.00", "46150.00", "46250.00", "200.1"],
        [1640995380000, "46250.00", "46400.00", "46200.00", "46350.00", "180.3"],
        [1640995440000, "46350.00", "46500.00", "46300.00", "46400.00", "220.7"]
    ]
    
    result = calculate_indicators_for_symbol(test_klines, "BTCUSDT")
    print("Тест технических индикаторов:")
    print(result) 