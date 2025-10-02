#!/usr/bin/env python3
"""
Анти-хайп фильтр для ребалансировщика BTC/ETH
Менее строгий, но защищает от покупок на пиках
"""

import numpy as np
from typing import Dict, List, Optional
from mex_api import MexAPI
from technical_indicators import TechnicalIndicators
import logging

logger = logging.getLogger(__name__)

class RebalancerAntiHypeFilter:
    def __init__(self):
        self.mex_api = MexAPI()
        self.tech_indicators = TechnicalIndicators()
        
        # Параметры фильтра - УСИЛЕНЫ НА 10% ДЛЯ АЛЬТ-СЕЗОНА
        self.atr_impulse_multiplier = 2.7  # Усилено с 3.0 (более строгая блокировка импульса)
        self.atr_dca_multiplier = 1.35     # Усилено с 1.5 (более строгий DCA)
        self.rsi_overbought = 63           # Усилено с 70 (более ранняя блокировка перекупленности)
        self.rsi_oversold = 38             # Усилено с 35 (более строгий порог перепроданности)
        self.rsi_neutral = 50              # Усилено с 55 (более строгий нейтральный RSI)
        self.ema_deviation = 0.027         # Усилено с 0.03 (более строгое отклонение от EMA20)
        
        # УСИЛЕННЫЕ ПАРАМЕТРЫ ПРОТИВ ХАЙПОВ
        self.max_historical_deviation = 0.018  # Усилено с 0.02 (более строгая блокировка от исторического максимума)
        self.recent_high_threshold = 0.009     # Усилено с 0.01 (более строгое ограничение от недавнего максимума)
        self.volume_hype_threshold = 2.7       # Усилено с 3.0 (более строгая блокировка по объему)
        
        # ДОПОЛНИТЕЛЬНЫЙ ФИЛЬТР ПРОТИВ ХАЙПА - ЗАПРЕТ ПОКУПОК БЛИЗКО К ДНЕВНОМУ ХАЮ
        self.daily_high_safety_margin = 0.01  # 1% безопасная дистанция от дневного хая
        self.daily_high_block_threshold = 0.002  # 0.2% от хая = полная блокировка
        
        # Кэш для избежания повторных запросов
        self.cache = {}
        self.cache_ttl = 300  # 5 минут
    
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
    
    def _get_historical_max(self, klines: List, days: int = 30) -> float:
        """Получить исторический максимум за N дней"""
        try:
            if len(klines) < days:
                return 0.0
            
            highs = [float(k[2]) for k in klines[-days:]]
            return max(highs) if highs else 0.0
        except Exception as e:
            logger.error(f"Ошибка получения исторического максимума: {e}")
            return 0.0
    
    def _get_recent_high(self, klines: List, hours: int = 24) -> float:
        """Получить недавний максимум за N часов"""
        try:
            if len(klines) < hours:
                return 0.0
            
            highs = [float(k[2]) for k in klines[-hours:]]
            return max(highs) if highs else 0.0
        except Exception as e:
            logger.error(f"Ошибка получения недавнего максимума: {e}")
            return 0.0
    
    def _get_ath(self, symbol: str, max_days: int = 1000) -> float:
        """Получить ATH (All-Time High) по дневным свечам.
        Берем максимум High из доступных дневных свечей (до max_days).
        """
        try:
            daily_klines = self.mex_api.get_klines(symbol, '1d', max_days)
            if not daily_klines:
                return 0.0
            highs = [float(k[2]) for k in daily_klines]
            return max(highs) if highs else 0.0
        except Exception as e:
            logger.error(f"Ошибка получения ATH: {e}")
            return 0.0
    
    def _check_volume_hype(self, klines: List, period: int = 20) -> bool:
        """Проверить хайп по объему"""
        try:
            if len(klines) < period:
                return False
            
            volumes = [float(k[5]) for k in klines[-period:]]
            current_volume = volumes[-1]
            avg_volume = sum(volumes[:-1]) / len(volumes[:-1])
            
            return current_volume > avg_volume * self.volume_hype_threshold
        except Exception as e:
            logger.error(f"Ошибка проверки объема: {e}")
            return False
    
    def _check_daily_high_protection(self, symbol: str, current_price: float) -> Dict:
        """Проверка защиты от покупок близко к дневному хаю"""
        try:
            # Получаем дневные свечи
            daily_klines = self.mex_api.get_klines(symbol, '1d', 7)
            if not daily_klines or len(daily_klines) < 1:
                logger.warning(f"⚠️ Нет дневных свечей для {symbol}")
                return {'blocked': False, 'reason': 'no_daily_data'}
            
            # Находим дневной хай
            daily_high = max([float(k[2]) for k in daily_klines])  # high price
            
            # Рассчитываем расстояние от хая
            distance_from_high = (daily_high - current_price) / daily_high
            distance_percent = distance_from_high * 100
            
            logger.info(f"📊 {symbol}: дневной хай=${daily_high:.4f}, текущая цена=${current_price:.4f}, дистанция={distance_percent:.2f}%")
            
            # Полная блокировка если слишком близко к хаю
            if distance_from_high < self.daily_high_block_threshold:
                logger.warning(f"🚫 {symbol}: ПОЛНАЯ БЛОКИРОВКА! Слишком близко к дневному хаю: {distance_percent:.2f}% < {self.daily_high_block_threshold*100:.1f}%")
                return {
                    'blocked': True, 
                    'reason': f'rebalancer_daily_high_too_close_{distance_percent:.1f}%',
                    'daily_high': daily_high,
                    'current_price': current_price,
                    'distance_percent': distance_percent,
                    'block_type': 'daily_high_full_block'
                }
            
            # Ограничение если близко к хаю
            if distance_from_high < self.daily_high_safety_margin:
                logger.warning(f"⚠️ {symbol}: ОГРАНИЧЕНИЕ! Близко к дневному хаю: {distance_percent:.2f}% < {self.daily_high_safety_margin*100:.1f}%")
                return {
                    'blocked': False, 
                    'reason': f'rebalancer_daily_high_close_{distance_percent:.1f}%',
                    'daily_high': daily_high,
                    'current_price': current_price,
                    'distance_percent': distance_percent,
                    'block_type': 'daily_high_restriction',
                    'multiplier': 0.2  # Очень сильное ограничение для ребалансировки
                }
            
            # Безопасная зона
            logger.info(f"✅ {symbol}: Безопасная зона от дневного хая: {distance_percent:.2f}%")
            return {
                'blocked': False, 
                'reason': f'rebalancer_daily_high_safe_{distance_percent:.1f}%',
                'daily_high': daily_high,
                'current_price': current_price,
                'distance_percent': distance_percent,
                'block_type': 'daily_high_safe',
                'multiplier': 1.0
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки дневного хая для {symbol}: {e}")
            return {'blocked': False, 'reason': 'daily_high_check_error'}
    
    def check_buy_permission(self, symbol: str) -> Dict:
        """Проверить разрешение на покупку для ребалансировщика"""
        try:
            # Получаем данные
            klines_1h = self._get_klines_cached(symbol, '1h', 100)
            klines_4h = self._get_klines_cached(symbol, '4h', 100)  # Используем 4h
            
            if not klines_1h or not klines_4h:
                return {
                    'allowed': True, 
                    'multiplier': 1.0, 
                    'reason': 'no_data_fallback',
                    'daily_high': None,
                    'current_price': None,
                    'distance_percent': None,
                    'block_type': 'no_data_fallback'
                }
            
            # Рассчитываем индикаторы
            current_price = float(klines_1h[-1][4])
            
            # Проверяем защиту от покупок близко к дневному хаю
            daily_high_protection = self._check_daily_high_protection(symbol, current_price)
            if daily_high_protection['blocked']:
                logger.warning(f"🚫 РЕБАЛАНСИРОВКА {symbol}: {daily_high_protection['reason']}")
                # Формируем результат с информацией о дневном хае для Telegram
                result = {
                    'allowed': False, 
                    'multiplier': 0.0, 
                    'reason': daily_high_protection['reason'],
                    'daily_high': daily_high_protection['daily_high'],
                    'current_price': daily_high_protection['current_price'],
                    'distance_percent': daily_high_protection['distance_percent'],
                    'block_type': 'rebalancer_daily_high_full_block'
                }
                return result
            
            # Применяем множитель от дневного хая если есть ограничение
            daily_high_multiplier = daily_high_protection.get('multiplier', 1.0)
            
            atr_4h = self._calculate_atr(klines_4h, 14)
            rsi_1h = self._calculate_rsi(klines_1h, 14)
            ema20_1h = self._calculate_ema(klines_1h, 20)
            ema200_4h = self._calculate_ema(klines_4h, 200)
            
            # Изменение цены за 4 часа
            price_4h_ago = float(klines_4h[-2][4]) if len(klines_4h) > 1 else current_price
            price_change_4h = ((current_price - price_4h_ago) / price_4h_ago) * 100
            
            # Исторические максимумы: используем настоящий ATH по дневным свечам
            ath_all_time = self._get_ath(symbol, 1000)
            recent_high = self._get_recent_high(klines_1h, 24)
            volume_hype = self._check_volume_hype(klines_1h, 20)
            
            logger.info(f"🔄 РЕБАЛАНСИРОВКА {symbol}: цена=${current_price:.4f}, ATR={atr_4h:.4f}, RSI={rsi_1h:.1f}")
            logger.info(f"🔄 РЕБАЛАНСИРОВКА {symbol}: изменение 4ч={price_change_4h:.2f}%, EMA20=${ema20_1h:.4f}")
            logger.info(f"🔄 РЕБАЛАНСИРОВКА {symbol}: ATH=${ath_all_time:.4f}, недавний макс=${recent_high:.4f}")
            logger.info(f"🔄 РЕБАЛАНСИРОВКА {symbol}: объем хайп={'ДА' if volume_hype else 'НЕТ'}")
            
            # 0. ПРОВЕРКА ATH (БЛОКИРОВКА)
            if ath_all_time > 0 and current_price > ath_all_time * (1 - self.max_historical_deviation):
                logger.warning(f"🚫 РЕБАЛАНСИРОВКА {symbol}: БЛИЗКО К ATH! Цена ${current_price:.4f} vs ATH ${ath_all_time:.4f}")
                return {
                    'allowed': False, 
                    'multiplier': 0.0, 
                    'reason': f'rebalancer_ath_block_{current_price:.0f}vs{ath_all_time:.0f}',
                    'daily_high': daily_high_protection.get('daily_high'),
                    'current_price': current_price,
                    'distance_percent': daily_high_protection.get('distance_percent'),
                    'block_type': 'ath_block'
                }
            
            # 1. ПРОВЕРКА НЕДАВНЕГО МАКСИМУМА (ОГРАНИЧЕНИЕ) - МЕНЕЕ СТРОГОЕ
            if recent_high > 0 and current_price > recent_high * (1 - self.recent_high_threshold):
                final_multiplier = 0.5 * daily_high_multiplier
                logger.warning(f"⚠️ РЕБАЛАНСИРОВКА {symbol}: БЛИЗКО К НЕДАВНЕМУ МАКСИМУМУ! Цена ${current_price:.4f} vs недавний ${recent_high:.4f}")
                return {
                    'allowed': True, 
                    'multiplier': final_multiplier,  # Менее строгое ограничение
                    'reason': f'rebalancer_recent_high_limit_{current_price:.0f}vs{recent_high:.0f}',
                    'daily_high': daily_high_protection.get('daily_high'),
                    'current_price': current_price,
                    'distance_percent': daily_high_protection.get('distance_percent'),
                    'block_type': 'recent_high_limit'
                }
            
            # 2. ПРОВЕРКА ОБЪЕМА ХАЙПА (БЛОКИРОВКА) - МЕНЕЕ СТРОГАЯ
            if volume_hype:
                logger.warning(f"🚫 РЕБАЛАНСИРОВКА {symbol}: ХАЙП ПО ОБЪЕМУ! Объем в {self.volume_hype_threshold}x выше среднего")
                return {
                    'allowed': False, 
                    'multiplier': 0.0, 
                    'reason': f'rebalancer_volume_hype_block_{self.volume_hype_threshold}x',
                    'daily_high': daily_high_protection.get('daily_high'),
                    'current_price': current_price,
                    'distance_percent': daily_high_protection.get('distance_percent'),
                    'block_type': 'volume_hype_block'
                }
            
            # 3. ПРОВЕРКА ИМПУЛЬСА ВВЕРХ (блокировка) - МЕНЕЕ СТРОГАЯ
            atr_threshold = (atr_4h / current_price) * 100 * self.atr_impulse_multiplier
            if price_change_4h > atr_threshold:
                logger.warning(f"🚫 РЕБАЛАНСИРОВКА {symbol}: Импульс вверх {price_change_4h:.2f}% > {atr_threshold:.2f}% (3×ATR)")
                return {
                    'allowed': False, 
                    'multiplier': 0.0, 
                    'reason': f'rebalancer_hype_block_impulse_{price_change_4h:.1f}%',
                    'daily_high': daily_high_protection.get('daily_high'),
                    'current_price': current_price,
                    'distance_percent': daily_high_protection.get('distance_percent'),
                    'block_type': 'impulse_block'
                }
            
            # 4. ПРОВЕРКА ПЕРЕКУПЛЕННОСТИ (блокировка) - МЕНЕЕ СТРОГАЯ
            if rsi_1h > self.rsi_overbought and current_price > ema20_1h * (1 + self.ema_deviation):
                logger.warning(f"🚫 РЕБАЛАНСИРОВКА {symbol}: Перекупленность RSI={rsi_1h:.1f} и цена выше EMA20+3%")
                return {
                    'allowed': False, 
                    'multiplier': 0.0, 
                    'reason': f'rebalancer_hype_block_overbought_RSI{rsi_1h:.0f}',
                    'daily_high': daily_high_protection.get('daily_high'),
                    'current_price': current_price,
                    'distance_percent': daily_high_protection.get('distance_percent'),
                    'block_type': 'overbought_block'
                }
            
            # 5. ПРОВЕРКА МЕДВЕЖЬЕГО ТРЕНДА (блокировка) - МЕНЕЕ СТРОГАЯ
            if current_price < ema200_4h * 0.95:  # Допускаем 5% ниже EMA200
                logger.warning(f"🚫 РЕБАЛАНСИРОВКА {symbol}: Цена сильно ниже EMA200 (медвежий тренд)")
                return {
                    'allowed': False, 
                    'multiplier': 0.0, 
                    'reason': 'rebalancer_bear_trend_below_ema200',
                    'daily_high': daily_high_protection.get('daily_high'),
                    'current_price': current_price,
                    'distance_percent': daily_high_protection.get('distance_percent'),
                    'block_type': 'bear_trend_block'
                }
            
            # 6. ПРОВЕРКА DCA НА ПАДЕНИИ (усиление) - МЕНЕЕ СТРОГОЕ
            atr_dca_threshold = (atr_4h / current_price) * 100 * self.atr_dca_multiplier
            if price_change_4h < -atr_dca_threshold and rsi_1h < self.rsi_oversold:
                final_multiplier = 1.5 * daily_high_multiplier
                logger.info(f"🚀 РЕБАЛАНСИРОВКА {symbol}: DCA усиление! Падение {price_change_4h:.2f}% и RSI={rsi_1h:.1f}, множитель={final_multiplier:.2f}")
                return {
                    'allowed': True, 
                    'multiplier': final_multiplier, 
                    'reason': f'rebalancer_dca_boost_fall_{abs(price_change_4h):.1f}%',
                    'daily_high': daily_high_protection.get('daily_high'),
                    'current_price': current_price,
                    'distance_percent': daily_high_protection.get('distance_percent'),
                    'block_type': 'dca_boost'
                }
            
            # 7. БАЗОВЫЕ ПОКУПКИ (норма) - МЕНЕЕ СТРОГИЕ
            if rsi_1h < self.rsi_neutral:
                final_multiplier = 1.0 * daily_high_multiplier
                logger.info(f"✅ РЕБАЛАНСИРОВКА {symbol}: Нормальная покупка, RSI={rsi_1h:.1f}, множитель={final_multiplier:.2f}")
                return {
                    'allowed': True, 
                    'multiplier': final_multiplier, 
                    'reason': f'rebalancer_normal_buy_RSI{rsi_1h:.0f}',
                    'daily_high': daily_high_protection.get('daily_high'),
                    'current_price': current_price,
                    'distance_percent': daily_high_protection.get('distance_percent'),
                    'block_type': 'normal_buy'
                }
            
            # 8. НЕЙТРАЛЬНАЯ ЗОНА (умеренное ограничение) - МЕНЕЕ СТРОГОЕ
            final_multiplier = 0.7 * daily_high_multiplier
            logger.info(f"⚠️ РЕБАЛАНСИРОВКА {symbol}: Нейтральная зона, RSI={rsi_1h:.1f}, множитель={final_multiplier:.2f}")
            return {
                'allowed': True, 
                'multiplier': final_multiplier,  # Менее строгое ограничение
                'reason': f'rebalancer_neutral_zone_RSI{rsi_1h:.0f}',
                'daily_high': daily_high_protection.get('daily_high'),
                'current_price': current_price,
                'distance_percent': daily_high_protection.get('distance_percent'),
                'block_type': 'neutral_zone'
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка анти-хайп фильтра ребалансировщика для {symbol}: {e}")
            return {
                'allowed': True, 
                'multiplier': 1.0, 
                'reason': 'rebalancer_error_fallback',
                'daily_high': None,
                'current_price': None,
                'distance_percent': None,
                'block_type': 'rebalancer_error_fallback'
            }
    
    def get_filter_status(self, symbols: List[str]) -> Dict:
        """Получить статус фильтра для нескольких символов"""
        results = {}
        for symbol in symbols:
            results[symbol] = self.check_buy_permission(symbol)
        return results

if __name__ == "__main__":
    # Тест фильтра
    filter = RebalancerAntiHypeFilter()
    
    test_symbols = ['BTCUSDC', 'ETHUSDC']
    for symbol in test_symbols:
        result = filter.check_buy_permission(symbol)
        print(f"{symbol}: {result}") 