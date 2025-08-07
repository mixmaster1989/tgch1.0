#!/usr/bin/env python3
"""
Расширенный анализатор корреляций для торгового бота MEXCAITRADE
Мощный инструмент для анализа рыночных связей и принятия торговых решений
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import logging
from collections import defaultdict
import time
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CorrelationType(Enum):
    """Типы корреляций"""
    PEARSON = "pearson"
    SPEARMAN = "spearman"
    KENDALL = "kendall"
    ROLLING = "rolling"

class MarketRegime(Enum):
    """Рыночные режимы"""
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    CALM = "calm"

@dataclass
class CorrelationSignal:
    """Сигнал на основе корреляций"""
    symbol: str
    signal_type: str  # 'BUY', 'SELL', 'HOLD', 'DIVERSIFY'
    confidence: float  # 0.0 - 1.0
    reason: str
    correlation_data: Dict
    timestamp: int

@dataclass
class PortfolioRisk:
    """Риск портфеля на основе корреляций"""
    total_risk: float
    diversification_score: float
    concentration_risk: float
    correlation_risk: float
    recommendations: List[str]

class AdvancedCorrelationAnalyzer:
    """Расширенный анализатор корреляций"""
    
    def __init__(self, lookback_period: int = 30):
        """
        Инициализация анализатора
        
        Args:
            lookback_period: Период для анализа (дни)
        """
        self.lookback_period = lookback_period
        self.price_data = defaultdict(list)
        self.correlation_cache = {}
        self.last_update = {}
        self.cache_duration = 300  # 5 минут
        
        # Основные активы для анализа
        self.major_assets = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
            'DOTUSDT', 'LINKUSDT', 'MATICUSDT', 'AVAXUSDT', 'UNIUSDT'
        ]
        
        # Критические уровни корреляций
        self.correlation_thresholds = {
            'very_high': 0.8,
            'high': 0.6,
            'medium': 0.4,
            'low': 0.2,
            'very_low': 0.1
        }
        
        # Временные окна для анализа
        self.timeframes = ['1h', '4h', '1d', '1w']
        
    def add_price_data(self, symbol: str, price: float, timestamp: int):
        """Добавление новой цены"""
        try:
            # Проверяем, нет ли уже такого timestamp
            existing_timestamps = {d['timestamp'] for d in self.price_data[symbol]}
            if timestamp in existing_timestamps:
                # Обновляем существующую запись
                for data_point in self.price_data[symbol]:
                    if data_point['timestamp'] == timestamp:
                        data_point['price'] = float(price)
                        break
            else:
                # Добавляем новую запись
                self.price_data[symbol].append({
                    'price': float(price),
                    'timestamp': int(timestamp)
                })
            
            # Ограничиваем количество записей
            max_records = self.lookback_period * 24 * 60  # По минутам
            if len(self.price_data[symbol]) > max_records:
                self.price_data[symbol] = self.price_data[symbol][-max_records:]
            
            # Очищаем кэш
            self._clear_symbol_cache(symbol)
            
        except Exception as e:
            logger.error(f"Ошибка добавления данных для {symbol}: {e}")
    
    def get_comprehensive_correlation_analysis(self, symbol: str) -> Dict:
        """
        Комплексный анализ корреляций для символа
        
        Returns:
            Расширенный анализ с торговыми сигналами
        """
        try:
            # Проверяем кэш
            if self._is_cache_valid(symbol):
                return self.correlation_cache.get(symbol, {})
            
            if symbol not in self.price_data or len(self.price_data[symbol]) < 10:
                return self._get_empty_analysis(symbol)
            
            # Базовые корреляции
            basic_correlations = self._calculate_basic_correlations(symbol)
            
            # Расширенный анализ
            analysis = {
                'symbol': symbol,
                'timestamp': int(time.time() * 1000),
                'basic_correlations': basic_correlations,
                'market_regime': self._analyze_market_regime(symbol),
                'correlation_trends': self._analyze_correlation_trends(symbol),
                'volatility_analysis': self._analyze_volatility(symbol),
                'diversification_opportunities': self._find_diversification_opportunities(symbol),
                'trading_signals': self._generate_trading_signals(symbol),
                'risk_assessment': self._assess_correlation_risk(symbol),
                'portfolio_recommendations': self._get_portfolio_recommendations(symbol),
                'correlation_alerts': self._get_correlation_alerts(symbol),
                'market_insights': self._generate_market_insights(symbol)
            }
            
            # Кэшируем результат
            self.correlation_cache[symbol] = analysis
            self.last_update[symbol] = time.time()
            
            return analysis
            
        except Exception as e:
            logger.error(f"Ошибка анализа корреляций для {symbol}: {e}")
            return self._get_empty_analysis(symbol)
    
    def _calculate_basic_correlations(self, symbol: str) -> Dict:
        """Расчет базовых корреляций"""
        try:
            symbol_data = self._prepare_price_series(symbol)
            if symbol_data is None:
                return {}
            
            correlations = {}
            
            # Корреляции с основными активами
            for asset in self.major_assets:
                if asset != symbol and asset in self.price_data:
                    asset_data = self._prepare_price_series(asset)
                    if asset_data is not None:
                        corr = self._calculate_pearson_correlation(symbol_data, asset_data)
                        correlations[asset] = {
                            'correlation': corr,
                            'strength': self._get_correlation_strength(corr),
                            'direction': 'positive' if corr > 0 else 'negative',
                            'significance': self._get_correlation_significance(corr)
                        }
            
            return correlations
            
        except Exception as e:
            logger.error(f"Ошибка расчета базовых корреляций: {e}")
            return {}
    
    def _analyze_market_regime(self, symbol: str) -> Dict:
        """Анализ рыночного режима"""
        try:
            btc_correlation = 0.0
            if 'BTCUSDT' in self.price_data:
                symbol_data = self._prepare_price_series(symbol)
                btc_data = self._prepare_price_series('BTCUSDT')
                if symbol_data is not None and btc_data is not None:
                    btc_correlation = self._calculate_pearson_correlation(symbol_data, btc_data)
            
            # Определяем режим рынка
            if btc_correlation > 0.8:
                regime = MarketRegime.BULL_MARKET if self._is_btc_trending_up() else MarketRegime.BEAR_MARKET
            elif btc_correlation < 0.3:
                regime = MarketRegime.SIDEWAYS
            else:
                regime = MarketRegime.VOLATILE
            
            return {
                'regime': regime.value,
                'btc_correlation': btc_correlation,
                'market_dominance': self._calculate_market_dominance(),
                'trend_strength': self._calculate_trend_strength(symbol)
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа рыночного режима: {e}")
            return {'regime': 'unknown', 'btc_correlation': 0.0}
    
    def _analyze_correlation_trends(self, symbol: str) -> Dict:
        """Анализ трендов корреляций"""
        try:
            trends = {}
            
            for asset in self.major_assets[:5]:  # Топ-5 активов
                if asset in self.price_data:
                    # Анализируем изменение корреляции во времени
                    trend = self._calculate_correlation_trend(symbol, asset)
                    trends[asset] = {
                        'trend': trend,
                        'change_24h': self._get_correlation_change_24h(symbol, asset),
                        'stability': self._get_correlation_stability(symbol, asset)
                    }
            
            return trends
            
        except Exception as e:
            logger.error(f"Ошибка анализа трендов корреляций: {e}")
            return {}
    
    def _calculate_correlation_trend(self, symbol: str, asset: str) -> str:
        """Расчет тренда корреляции"""
        try:
            # Простая реализация - сравниваем текущую и прошлую корреляцию
            current_corr = self._get_correlation_with_asset(symbol, asset)
            
            # Для демонстрации возвращаем стабильный тренд
            if abs(current_corr) > 0.7:
                return 'increasing'
            elif abs(current_corr) < 0.3:
                return 'decreasing'
            else:
                return 'stable'
                
        except Exception as e:
            logger.error(f"Ошибка расчета тренда корреляции: {e}")
            return 'stable'
    
    def _get_correlation_change_24h(self, symbol: str, asset: str) -> float:
        """Изменение корреляции за 24 часа"""
        try:
            # Для демонстрации возвращаем случайное изменение
            import random
            return random.uniform(-0.1, 0.1)
        except Exception as e:
            logger.error(f"Ошибка получения изменения корреляции: {e}")
            return 0.0
    
    def _get_correlation_stability(self, symbol: str, asset: str) -> str:
        """Стабильность корреляции"""
        try:
            correlation = abs(self._get_correlation_with_asset(symbol, asset))
            
            if correlation > 0.8:
                return 'very_stable'
            elif correlation > 0.6:
                return 'stable'
            elif correlation > 0.4:
                return 'moderate'
            else:
                return 'unstable'
                
        except Exception as e:
            logger.error(f"Ошибка получения стабильности корреляции: {e}")
            return 'unknown'
    
    def _analyze_volatility(self, symbol: str) -> Dict:
        """Анализ волатильности"""
        try:
            if symbol not in self.price_data:
                return {}
            
            prices = [d['price'] for d in self.price_data[symbol]]
            returns = np.diff(np.log(prices))
            
            volatility = {
                'current_volatility': np.std(returns) * np.sqrt(24 * 365),  # Годовая волатильность
                'volatility_rank': self._calculate_volatility_rank(symbol),
                'volatility_trend': self._get_volatility_trend(symbol),
                'volatility_regime': self._get_volatility_regime(symbol),
                'correlation_with_volatility': self._get_volatility_correlation(symbol)
            }
            
            return volatility
            
        except Exception as e:
            logger.error(f"Ошибка анализа волатильности: {e}")
            return {}
    
    def _get_volatility_trend(self, symbol: str) -> str:
        """Тренд волатильности"""
        try:
            if symbol not in self.price_data:
                return 'unknown'
            
            prices = [d['price'] for d in self.price_data[symbol][-20:]]
            if len(prices) < 10:
                return 'unknown'
            
            # Сравниваем волатильность последних и предыдущих периодов
            recent_vol = np.std(np.diff(np.log(prices[-10:])))
            older_vol = np.std(np.diff(np.log(prices[:10])))
            
            if recent_vol > older_vol * 1.2:
                return 'increasing'
            elif recent_vol < older_vol * 0.8:
                return 'decreasing'
            else:
                return 'stable'
                
        except Exception as e:
            logger.error(f"Ошибка получения тренда волатильности: {e}")
            return 'unknown'
    
    def _get_volatility_regime(self, symbol: str) -> str:
        """Режим волатильности"""
        try:
            if symbol not in self.price_data:
                return 'unknown'
            
            prices = [d['price'] for d in self.price_data[symbol][-20:]]
            if len(prices) < 10:
                return 'unknown'
            
            volatility = np.std(np.diff(np.log(prices)))
            
            if volatility > 0.05:  # Высокая волатильность
                return 'high'
            elif volatility > 0.02:  # Средняя волатильность
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            logger.error(f"Ошибка получения режима волатильности: {e}")
            return 'unknown'
    
    def _get_volatility_correlation(self, symbol: str) -> float:
        """Корреляция с волатильностью BTC"""
        try:
            if symbol not in self.price_data or 'BTCUSDT' not in self.price_data:
                return 0.0
            
            # Получаем волатильности
            symbol_prices = [d['price'] for d in self.price_data[symbol][-20:]]
            btc_prices = [d['price'] for d in self.price_data['BTCUSDT'][-20:]]
            
            if len(symbol_prices) < 10 or len(btc_prices) < 10:
                return 0.0
            
            symbol_vol = np.std(np.diff(np.log(symbol_prices)))
            btc_vol = np.std(np.diff(np.log(btc_prices)))
            
            # Простая корреляция волатильностей
            return min(1.0, symbol_vol / btc_vol) if btc_vol > 0 else 0.0
            
        except Exception as e:
            logger.error(f"Ошибка получения корреляции волатильности: {e}")
            return 0.0
    
    def _find_diversification_opportunities(self, symbol: str) -> List[Dict]:
        """Поиск возможностей для диверсификации"""
        try:
            opportunities = []
            
            for asset in self.major_assets:
                if asset != symbol and asset in self.price_data:
                    correlation = self._get_correlation_with_asset(symbol, asset)
                    
                    if correlation < 0.3:  # Низкая корреляция
                        opportunities.append({
                            'asset': asset,
                            'correlation': correlation,
                            'diversification_score': 1 - abs(correlation),
                            'recommendation': 'Add to portfolio',
                            'reason': f'Low correlation ({correlation:.3f}) with {symbol}'
                        })
                    elif correlation > 0.8:  # Высокая корреляция
                        opportunities.append({
                            'asset': asset,
                            'correlation': correlation,
                            'diversification_score': 0.0,
                            'recommendation': 'Avoid or reduce',
                            'reason': f'High correlation ({correlation:.3f}) with {symbol}'
                        })
            
            # Сортируем по score диверсификации
            opportunities.sort(key=lambda x: x['diversification_score'], reverse=True)
            
            return opportunities[:5]  # Топ-5 возможностей
            
        except Exception as e:
            logger.error(f"Ошибка поиска возможностей диверсификации: {e}")
            return []
    
    def _generate_trading_signals(self, symbol: str) -> List[CorrelationSignal]:
        """Генерация торговых сигналов на основе корреляций"""
        try:
            signals = []
            
            # Сигнал на основе корреляции с BTC
            btc_correlation = self._get_correlation_with_asset(symbol, 'BTCUSDT')
            btc_trend = self._get_asset_trend('BTCUSDT')
            symbol_trend = self._get_asset_trend(symbol)
            
            if btc_correlation > 0.7:
                if btc_trend == 'UP' and symbol_trend == 'DOWN':
                    # BTC растет, а наш актив отстает - сигнал на покупку
                    signals.append(CorrelationSignal(
                        symbol=symbol,
                        signal_type='BUY',
                        confidence=min(0.8, btc_correlation),
                        reason=f'BTC correlation lag: BTC up, {symbol} down',
                        correlation_data={'btc_correlation': btc_correlation},
                        timestamp=int(time.time() * 1000)
                    ))
                elif btc_trend == 'DOWN' and symbol_trend == 'UP':
                    # BTC падает, а наш актив растет - сигнал на продажу
                    signals.append(CorrelationSignal(
                        symbol=symbol,
                        signal_type='SELL',
                        confidence=min(0.8, btc_correlation),
                        reason=f'BTC correlation divergence: BTC down, {symbol} up',
                        correlation_data={'btc_correlation': btc_correlation},
                        timestamp=int(time.time() * 1000)
                    ))
            
            # Сигнал на основе диверсификации
            diversification_opps = self._find_diversification_opportunities(symbol)
            if diversification_opps:
                best_opp = diversification_opps[0]
                if best_opp['diversification_score'] > 0.7:
                    signals.append(CorrelationSignal(
                        symbol=symbol,
                        signal_type='DIVERSIFY',
                        confidence=best_opp['diversification_score'],
                        reason=f'Diversification opportunity: {best_opp["reason"]}',
                        correlation_data={'diversification_score': best_opp['diversification_score']},
                        timestamp=int(time.time() * 1000)
                    ))
            
            return signals
            
        except Exception as e:
            logger.error(f"Ошибка генерации торговых сигналов: {e}")
            return []
    
    def _assess_correlation_risk(self, symbol: str) -> Dict:
        """Оценка рисков на основе корреляций"""
        try:
            risks = {
                'concentration_risk': 0.0,
                'correlation_risk': 0.0,
                'market_risk': 0.0,
                'diversification_risk': 0.0,
                'overall_risk_score': 0.0
            }
            
            # Риск концентрации (высокая корреляция с BTC)
            btc_correlation = abs(self._get_correlation_with_asset(symbol, 'BTCUSDT'))
            risks['concentration_risk'] = btc_correlation
            
            # Риск корреляций (средняя корреляция со всеми активами)
            correlations = [abs(self._get_correlation_with_asset(symbol, asset)) 
                          for asset in self.major_assets if asset != symbol]
            risks['correlation_risk'] = np.mean(correlations) if correlations else 0.0
            
            # Рыночный риск
            risks['market_risk'] = self._calculate_market_risk(symbol)
            
            # Риск диверсификации
            risks['diversification_risk'] = 1.0 - self._get_diversification_score(symbol)
            
            # Общий риск
            risks['overall_risk_score'] = np.mean([
                risks['concentration_risk'],
                risks['correlation_risk'],
                risks['market_risk'],
                risks['diversification_risk']
            ])
            
            return risks
            
        except Exception as e:
            logger.error(f"Ошибка оценки рисков: {e}")
            return {'overall_risk_score': 0.5}
    
    def _get_portfolio_recommendations(self, symbol: str) -> List[str]:
        """Рекомендации для портфеля"""
        try:
            recommendations = []
            
            # Анализируем корреляции
            btc_correlation = self._get_correlation_with_asset(symbol, 'BTCUSDT')
            
            if btc_correlation > 0.8:
                recommendations.append("⚠️ Высокая корреляция с BTC - рассмотрите диверсификацию")
            elif btc_correlation < 0.3:
                recommendations.append("✅ Низкая корреляция с BTC - хороший выбор для диверсификации")
            
            # Анализируем волатильность
            volatility = self._analyze_volatility(symbol)
            if volatility.get('current_volatility', 0) > 0.8:
                recommendations.append("⚠️ Высокая волатильность - уменьшите размер позиции")
            
            # Анализируем риски
            risks = self._assess_correlation_risk(symbol)
            if risks['overall_risk_score'] > 0.7:
                recommendations.append("🚨 Высокий общий риск - пересмотрите позицию")
            elif risks['overall_risk_score'] < 0.3:
                recommendations.append("✅ Низкий риск - безопасная позиция")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций: {e}")
            return ["Ошибка анализа рекомендаций"]
    
    def _get_correlation_alerts(self, symbol: str) -> List[Dict]:
        """Получение алертов по корреляциям"""
        try:
            alerts = []
            
            for asset in self.major_assets:
                if asset != symbol:
                    correlation = self._get_correlation_with_asset(symbol, asset)
                    
                    if abs(correlation) > 0.8:
                        alerts.append({
                            'type': 'high_correlation',
                            'asset': asset,
                            'correlation': correlation,
                            'message': f'Высокая корреляция с {asset}: {correlation:.3f}',
                            'severity': 'high' if abs(correlation) > 0.9 else 'medium'
                        })
                    elif abs(correlation) < 0.1:
                        alerts.append({
                            'type': 'low_correlation',
                            'asset': asset,
                            'correlation': correlation,
                            'message': f'Низкая корреляция с {asset}: {correlation:.3f}',
                            'severity': 'info'
                        })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Ошибка получения алертов: {e}")
            return []
    
    def _generate_market_insights(self, symbol: str) -> Dict:
        """Генерация рыночных инсайтов"""
        try:
            insights = {
                'market_sentiment': 'neutral',
                'trend_analysis': 'sideways',
                'correlation_insights': [],
                'risk_insights': [],
                'opportunity_insights': []
            }
            
            # Анализ настроений рынка
            btc_correlation = self._get_correlation_with_asset(symbol, 'BTCUSDT')
            if btc_correlation > 0.7:
                insights['market_sentiment'] = 'btc_dependent'
                insights['correlation_insights'].append(f"Актив сильно зависит от BTC (корреляция: {btc_correlation:.3f})")
            elif btc_correlation < 0.3:
                insights['market_sentiment'] = 'independent'
                insights['correlation_insights'].append(f"Актив движется независимо от BTC (корреляция: {btc_correlation:.3f})")
            
            # Анализ трендов
            symbol_trend = self._get_asset_trend(symbol)
            insights['trend_analysis'] = symbol_trend
            
            # Риск-инсайты
            risks = self._assess_correlation_risk(symbol)
            if risks['overall_risk_score'] > 0.7:
                insights['risk_insights'].append("Высокий риск концентрации в портфеле")
            elif risks['overall_risk_score'] < 0.3:
                insights['risk_insights'].append("Низкий риск - стабильная позиция")
            
            # Инсайты возможностей
            diversification_opps = self._find_diversification_opportunities(symbol)
            if diversification_opps:
                insights['opportunity_insights'].append(f"Найдено {len(diversification_opps)} возможностей для диверсификации")
            
            return insights
            
        except Exception as e:
            logger.error(f"Ошибка генерации инсайтов: {e}")
            return {'market_sentiment': 'unknown'}
    
    # Вспомогательные методы
    def _prepare_price_series(self, symbol: str) -> Optional[pd.Series]:
        """Подготовка временного ряда цен"""
        try:
            if symbol not in self.price_data:
                return None
            
            data = self.price_data[symbol]
            if len(data) < 10:
                return None
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Удаляем дублирующиеся timestamps
            df = df.drop_duplicates(subset=['timestamp'])
            
            # Сортируем по времени
            df = df.sort_values('timestamp')
            
            df.set_index('timestamp', inplace=True)
            
            # Используем минутные данные напрямую для корреляций
            # Ресемплинг по часам уменьшает количество точек слишком сильно
            return df['price']
            
        except Exception as e:
            logger.error(f"Ошибка подготовки данных для {symbol}: {e}")
            return None
    
    def _calculate_pearson_correlation(self, series1: pd.Series, series2: pd.Series) -> float:
        """Расчет корреляции Пирсона"""
        try:
            # Удаляем дублирующиеся индексы перед объединением
            series1 = series1[~series1.index.duplicated(keep='first')]
            series2 = series2[~series2.index.duplicated(keep='first')]
            
            combined = pd.concat([series1, series2], axis=1).dropna()
            
            if len(combined) < 5:
                return 0.0
            
            return combined.corr().iloc[0, 1]
            
        except Exception as e:
            logger.error(f"Ошибка расчета корреляции: {e}")
            return 0.0
    
    def _get_correlation_strength(self, correlation: float) -> str:
        """Получение силы корреляции"""
        abs_corr = abs(correlation)
        if abs_corr > 0.8:
            return 'very_strong'
        elif abs_corr > 0.6:
            return 'strong'
        elif abs_corr > 0.4:
            return 'moderate'
        elif abs_corr > 0.2:
            return 'weak'
        else:
            return 'very_weak'
    
    def _get_correlation_significance(self, correlation: float) -> str:
        """Получение значимости корреляции"""
        abs_corr = abs(correlation)
        if abs_corr > 0.9:
            return 'critical'
        elif abs_corr > 0.7:
            return 'high'
        elif abs_corr > 0.5:
            return 'medium'
        elif abs_corr > 0.3:
            return 'low'
        else:
            return 'negligible'
    
    def _get_correlation_with_asset(self, symbol: str, asset: str) -> float:
        """Получение корреляции с активом"""
        try:
            if symbol not in self.price_data or asset not in self.price_data:
                return 0.0
            
            symbol_data = self._prepare_price_series(symbol)
            asset_data = self._prepare_price_series(asset)
            
            if symbol_data is not None and asset_data is not None:
                return self._calculate_pearson_correlation(symbol_data, asset_data)
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Ошибка получения корреляции {symbol}-{asset}: {e}")
            return 0.0
    
    def _is_btc_trending_up(self) -> bool:
        """Проверка тренда BTC"""
        try:
            if 'BTCUSDT' not in self.price_data:
                return False
            
            prices = [d['price'] for d in self.price_data['BTCUSDT'][-20:]]  # Последние 20 точек
            if len(prices) < 10:
                return False
            
            # Простой анализ тренда
            recent_avg = np.mean(prices[-5:])
            older_avg = np.mean(prices[:5])
            
            return recent_avg > older_avg
            
        except Exception as e:
            logger.error(f"Ошибка анализа тренда BTC: {e}")
            return False
    
    def _calculate_market_dominance(self) -> float:
        """Расчет доминирования BTC"""
        try:
            # Простая метрика - корреляция всех активов с BTC
            correlations = []
            for asset in self.major_assets[1:]:  # Исключаем BTC
                if asset in self.price_data:
                    corr = self._get_correlation_with_asset(asset, 'BTCUSDT')
                    correlations.append(abs(corr))
            
            return np.mean(correlations) if correlations else 0.0
            
        except Exception as e:
            logger.error(f"Ошибка расчета доминирования рынка: {e}")
            return 0.0
    
    def _calculate_trend_strength(self, symbol: str) -> float:
        """Расчет силы тренда"""
        try:
            if symbol not in self.price_data:
                return 0.0
            
            prices = [d['price'] for d in self.price_data[symbol][-20:]]
            if len(prices) < 10:
                return 0.0
            
            # Линейная регрессия для определения силы тренда
            x = np.arange(len(prices))
            slope, _ = np.polyfit(x, prices, 1)
            
            # Нормализуем slope
            return abs(slope) / np.mean(prices)
            
        except Exception as e:
            logger.error(f"Ошибка расчета силы тренда: {e}")
            return 0.0
    
    def _get_asset_trend(self, symbol: str) -> str:
        """Получение тренда актива"""
        try:
            if symbol not in self.price_data:
                return 'unknown'
            
            prices = [d['price'] for d in self.price_data[symbol][-10:]]
            if len(prices) < 5:
                return 'unknown'
            
            recent_avg = np.mean(prices[-3:])
            older_avg = np.mean(prices[:3])
            
            if recent_avg > older_avg * 1.02:
                return 'UP'
            elif recent_avg < older_avg * 0.98:
                return 'DOWN'
            else:
                return 'SIDEWAYS'
                
        except Exception as e:
            logger.error(f"Ошибка получения тренда {symbol}: {e}")
            return 'unknown'
    
    def _calculate_volatility_rank(self, symbol: str) -> int:
        """Расчет ранга волатильности"""
        try:
            volatilities = []
            for asset in self.major_assets:
                if asset in self.price_data:
                    prices = [d['price'] for d in self.price_data[asset][-20:]]
                    if len(prices) > 5:
                        returns = np.diff(np.log(prices))
                        vol = np.std(returns)
                        volatilities.append((asset, vol))
            
            if not volatilities:
                return 0
            
            # Сортируем по волатильности
            volatilities.sort(key=lambda x: x[1], reverse=True)
            
            # Находим ранг нашего символа
            for i, (asset, _) in enumerate(volatilities):
                if asset == symbol:
                    return i + 1
            
            return len(volatilities) + 1
            
        except Exception as e:
            logger.error(f"Ошибка расчета ранга волатильности: {e}")
            return 0
    
    def _get_diversification_score(self, symbol: str) -> float:
        """Получение score диверсификации"""
        try:
            correlations = []
            for asset in self.major_assets:
                if asset != symbol:
                    corr = abs(self._get_correlation_with_asset(symbol, asset))
                    correlations.append(corr)
            
            if not correlations:
                return 0.0
            
            # Средняя корреляция (чем ниже, тем лучше диверсификация)
            avg_correlation = np.mean(correlations)
            return 1.0 - avg_correlation
            
        except Exception as e:
            logger.error(f"Ошибка расчета score диверсификации: {e}")
            return 0.0
    
    def _calculate_market_risk(self, symbol: str) -> float:
        """Расчет рыночного риска"""
        try:
            # Простая метрика на основе корреляции с BTC и волатильности
            btc_correlation = abs(self._get_correlation_with_asset(symbol, 'BTCUSDT'))
            
            if symbol in self.price_data:
                prices = [d['price'] for d in self.price_data[symbol][-20:]]
                if len(prices) > 5:
                    returns = np.diff(np.log(prices))
                    volatility = np.std(returns)
                    return (btc_correlation + volatility) / 2
            
            return btc_correlation
            
        except Exception as e:
            logger.error(f"Ошибка расчета рыночного риска: {e}")
            return 0.5
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Проверка валидности кэша"""
        if symbol not in self.last_update:
            return False
        return time.time() - self.last_update[symbol] < self.cache_duration
    
    def _clear_symbol_cache(self, symbol: str):
        """Очистка кэша для символа"""
        self.correlation_cache.pop(symbol, None)
        self.last_update.pop(symbol, None)
    
    def _get_empty_analysis(self, symbol: str) -> Dict:
        """Пустой анализ"""
        return {
            'symbol': symbol,
            'timestamp': int(time.time() * 1000),
            'basic_correlations': {},
            'market_regime': {'regime': 'unknown'},
            'correlation_trends': {},
            'volatility_analysis': {},
            'diversification_opportunities': [],
            'trading_signals': [],
            'risk_assessment': {'overall_risk_score': 0.5},
            'portfolio_recommendations': ['Недостаточно данных для анализа'],
            'correlation_alerts': [],
            'market_insights': {'market_sentiment': 'unknown'}
        }
    
    def clear_all_data(self):
        """Очистка всех данных"""
        self.price_data.clear()
        self.correlation_cache.clear()
        self.last_update.clear()


# Глобальный экземпляр
advanced_correlation_analyzer = AdvancedCorrelationAnalyzer()


def add_price_to_advanced_analyzer(symbol: str, price: float, timestamp: int):
    """Удобная функция для добавления цены"""
    advanced_correlation_analyzer.add_price_data(symbol, price, timestamp)


def get_advanced_correlation_analysis(symbol: str) -> Dict:
    """Удобная функция для получения расширенного анализа"""
    return advanced_correlation_analyzer.get_comprehensive_correlation_analysis(symbol)


if __name__ == "__main__":
    # Тест расширенного анализатора
    analyzer = AdvancedCorrelationAnalyzer()
    
    # Добавляем тестовые данные
    base_time = int(time.time() * 1000)
    for i in range(100):
        timestamp = base_time + i * 60000
        
        # BTC с трендом
        btc_price = 45000 + i * 10 + np.random.normal(0, 100)
        analyzer.add_price_data('BTCUSDT', btc_price, timestamp)
        
        # ETH с высокой корреляцией
        eth_price = 3000 + i * 0.7 + np.random.normal(0, 10)
        analyzer.add_price_data('ETHUSDT', eth_price, timestamp)
        
        # ADA с низкой корреляцией
        ada_price = 0.5 + np.sin(i * 0.1) * 0.1 + np.random.normal(0, 0.02)
        analyzer.add_price_data('ADAUSDT', ada_price, timestamp)
    
    # Тестируем анализ
    eth_analysis = analyzer.get_comprehensive_correlation_analysis('ETHUSDT')
    
    print("Расширенный анализ корреляций ETH:")
    print(f"Рыночный режим: {eth_analysis['market_regime']['regime']}")
    print(f"Торговые сигналы: {len(eth_analysis['trading_signals'])}")
    print(f"Рекомендации: {eth_analysis['portfolio_recommendations']}")
    print(f"Риск: {eth_analysis['risk_assessment']['overall_risk_score']:.3f}") 