#!/usr/bin/env python3
"""
Анти-хайп фильтр для защиты от покупок на пиках
Адаптивная логика на основе ATR, RSI и EMA
"""

import numpy as np
from typing import Dict, List, Optional
from mex_api import MexAPI
from technical_indicators import TechnicalIndicators
import logging

logger = logging.getLogger(__name__)

class AntiHypeFilter:
    def __init__(self):
        self.mex_api = MexAPI()
        self.tech_indicators = TechnicalIndicators()
        
        # Параметры фильтра
        self.atr_impulse_multiplier = 3.0  # Для блокировки импульса вверх
        self.atr_dca_multiplier = 2.0      # Для DCA на падении
        self.rsi_overbought = 65           # Порог перекупленности
        self.rsi_oversold = 45             # Порог перепроданности
        self.rsi_neutral = 55              # Нейтральный RSI
        self.ema_deviation = 0.03          # 3% отклонение от EMA20
        
        # Кэш для избежания повторных запросов
        self.cache = {}
        self.cache_ttl = 300  # 5 минут
        
        # Кэш результатов проверки
        self.result_cache = {}
        self.result_cache_ttl = 120  # 2 минуты кэш результатов
    
    def _get_klines_cached(self, symbol: str, interval: str, limit: int = 100) -> List:
        """Получить свечи с кэшированием"""
        cache_key = f"{symbol}_{interval}_{limit}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        klines = self.mex_api.get_klines(symbol, interval, limit)
        self.cache[cache_key] = klines
        return klines
    
    def _calculate_atr(self, klines: List, period: int = 14) -> float:
        """Рассчитать ATR (Average True Range)"""
        if len(klines) < period + 1:
            return 0.0
        
        try:
            highs = [float(k[2]) for k in klines[-period-1:]]
            lows = [float(k[3]) for k in klines[-period-1:]]
            closes = [float(k[4]) for k in klines[-period-1:]]
            
            true_ranges = []
            for i in range(1, len(highs)):
                tr1 = highs[i] - lows[i]
                tr2 = abs(highs[i] - closes[i-1])
                tr3 = abs(lows[i] - closes[i-1])
                true_ranges.append(max(tr1, tr2, tr3))
            
            return sum(true_ranges) / len(true_ranges) if true_ranges else 0.0
        except Exception as e:
            logger.error(f"Ошибка расчета ATR: {e}")
            return 0.0
    
    def _calculate_rsi(self, klines: List, period: int = 14) -> float:
        """Рассчитать RSI"""
        if len(klines) < period + 1:
            return 50.0
        
        try:
            closes = [float(k[4]) for k in klines[-period-1:]]
            
            gains = []
            losses = []
            
            for i in range(1, len(closes)):
                change = closes[i] - closes[i-1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = sum(gains) / len(gains) if gains else 0
            avg_loss = sum(losses) / len(losses) if losses else 0
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            return rsi
        except Exception as e:
            logger.error(f"Ошибка расчета RSI: {e}")
            return 50.0
    
    def _calculate_ema(self, klines: List, period: int) -> float:
        """Рассчитать EMA"""
        if len(klines) < period:
            return 0.0
        
        try:
            closes = [float(k[4]) for k in klines[-period:]]
            multiplier = 2 / (period + 1)
            ema = closes[0]
            
            for close in closes[1:]:
                ema = (close * multiplier) + (ema * (1 - multiplier))
            
            return ema
        except Exception as e:
            logger.error(f"Ошибка расчета EMA: {e}")
            return 0.0
    
    def _get_price_change_4h(self, klines_4h: List) -> float:
        """Получить изменение цены за 4 часа в %"""
        if len(klines_4h) < 2:
            return 0.0
        
        try:
            current_price = float(klines_4h[-1][4])  # Последняя цена закрытия
            price_4h_ago = float(klines_4h[-2][4])   # Цена 4 часа назад
            
            change_percent = ((current_price - price_4h_ago) / price_4h_ago) * 100
            return change_percent
        except Exception as e:
            logger.error(f"Ошибка расчета изменения цены: {e}")
            return 0.0
    
    def _get_cached_result(self, symbol: str) -> Optional[Dict]:
        """Получить кэшированный результат"""
        import time
        cache_key = f"result_{symbol}"
        if cache_key in self.result_cache:
            cached_time, result = self.result_cache[cache_key]
            if time.time() - cached_time < self.result_cache_ttl:
                return result
            else:
                del self.result_cache[cache_key]
        return None
    
    def _cache_result(self, symbol: str, result: Dict):
        """Кэшировать результат"""
        import time
        cache_key = f"result_{symbol}"
        self.result_cache[cache_key] = (time.time(), result)
    
    def check_buy_permission(self, symbol: str) -> Dict:
        """Основная функция проверки разрешения на покупку"""
        # Проверяем кэш результатов
        cached_result = self._get_cached_result(symbol)
        if cached_result:
            logger.info(f"📋 Используем кэшированный результат для {symbol}")
            return cached_result
        
        try:
            logger.info(f"🔍 Проверка анти-хайп фильтра для {symbol}")
            
            # Получаем данные (используем поддерживаемые интервалы)
            klines_1h = self._get_klines_cached(symbol, '1h', 50)
            klines_4h = self._get_klines_cached(symbol, '4h', 50)  # Используем 4h
            
            # Fallback на 15m если 1h/4h не работают
            if not klines_1h:
                klines_1h = self._get_klines_cached(symbol, '15m', 50)
            if not klines_4h:
                klines_4h = self._get_klines_cached(symbol, '60m', 50)  # Fallback на 60m
            
            if not klines_1h or not klines_4h:
                logger.warning(f"Нет данных свечей для {symbol}")
                result = {'allowed': True, 'multiplier': 1.0, 'reason': 'no_data'}
                self._cache_result(symbol, result)
                return result
            
            # Текущая цена
            current_price = float(klines_1h[-1][4])
            
            # Рассчитываем индикаторы
            atr_4h = self._calculate_atr(klines_4h, 14)
            rsi_1h = self._calculate_rsi(klines_1h, 14)
            ema20_1h = self._calculate_ema(klines_1h, 20)
            ema200_4h = self._calculate_ema(klines_4h, 200)
            
            # Изменение цены за 4 часа
            price_change_4h = self._get_price_change_4h(klines_4h)
            
            logger.info(f"📊 {symbol}: цена=${current_price:.4f}, ATR={atr_4h:.4f}, RSI={rsi_1h:.1f}")
            logger.info(f"📊 {symbol}: изменение 4ч={price_change_4h:.2f}%, EMA20=${ema20_1h:.4f}")
            
            # 1. ПРОВЕРКА ИМПУЛЬСА ВВЕРХ (блокировка)
            atr_threshold = (atr_4h / current_price) * 100 * self.atr_impulse_multiplier
            if price_change_4h > atr_threshold:
                result = {
                    'allowed': False, 
                    'multiplier': 0.0, 
                    'reason': f'hype_block_impulse_{price_change_4h:.1f}%'
                }
                logger.warning(f"🚫 {symbol}: Импульс вверх {price_change_4h:.2f}% > {atr_threshold:.2f}% (3×ATR)")
                self._cache_result(symbol, result)
                return result
            
            # 2. ПРОВЕРКА ПЕРЕКУПЛЕННОСТИ (блокировка)
            if rsi_1h > self.rsi_overbought and current_price > ema20_1h * (1 + self.ema_deviation):
                result = {
                    'allowed': False, 
                    'multiplier': 0.0, 
                    'reason': f'hype_block_overbought_RSI{rsi_1h:.0f}'
                }
                logger.warning(f"🚫 {symbol}: Перекупленность RSI={rsi_1h:.1f} и цена выше EMA20+3%")
                self._cache_result(symbol, result)
                return result
            
            # 3. ПРОВЕРКА МЕДВЕЖЬЕГО ТРЕНДА (блокировка)
            if current_price < ema200_4h:
                result = {
                    'allowed': False, 
                    'multiplier': 0.0, 
                    'reason': 'bear_trend_below_ema200'
                }
                logger.warning(f"🚫 {symbol}: Цена ниже EMA200 (медвежий тренд)")
                self._cache_result(symbol, result)
                return result
            
            # 4. ПРОВЕРКА DCA НА ПАДЕНИИ (усиление)
            atr_dca_threshold = (atr_4h / current_price) * 100 * self.atr_dca_multiplier
            if price_change_4h < -atr_dca_threshold and rsi_1h < self.rsi_oversold:
                result = {
                    'allowed': True, 
                    'multiplier': 2.0, 
                    'reason': f'dca_boost_fall_{abs(price_change_4h):.1f}%'
                }
                logger.info(f"🚀 {symbol}: DCA усиление! Падение {price_change_4h:.2f}% и RSI={rsi_1h:.1f}")
                self._cache_result(symbol, result)
                return result
            
            # 5. БАЗОВЫЕ ПОКУПКИ (норма)
            if rsi_1h < self.rsi_neutral:
                result = {
                    'allowed': True, 
                    'multiplier': 1.0, 
                    'reason': f'normal_buy_RSI{rsi_1h:.0f}'
                }
                logger.info(f"✅ {symbol}: Нормальная покупка, RSI={rsi_1h:.1f}")
                self._cache_result(symbol, result)
                return result
            
            # 6. НЕЙТРАЛЬНАЯ ЗОНА (небольшое ограничение)
            logger.info(f"⚠️ {symbol}: Нейтральная зона, RSI={rsi_1h:.1f}")
            result = {
                'allowed': True, 
                'multiplier': 0.7, 
                'reason': f'neutral_zone_RSI{rsi_1h:.0f}'
            }
            self._cache_result(symbol, result)
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка анти-хайп фильтра для {symbol}: {e}")
            result = {'allowed': True, 'multiplier': 1.0, 'reason': 'error_fallback'}
            self._cache_result(symbol, result)
            return result
    
    def get_filter_status(self, symbols: List[str]) -> Dict:
        """Получить статус фильтра для нескольких символов"""
        results = {}
        for symbol in symbols:
            results[symbol] = self.check_buy_permission(symbol)
        return results