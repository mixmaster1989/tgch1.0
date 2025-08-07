"""
Анализатор корреляций для торгового бота MEX
Модуль для расчета корреляций между активами и анализа рыночных связей
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union
import logging
from collections import defaultdict
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """Класс для анализа корреляций между активами"""
    
    def __init__(self, lookback_period: int = 30):
        """
        Инициализация анализатора корреляций
        
        Args:
            lookback_period: Период для расчета корреляций (дни)
        """
        self.lookback_period = lookback_period
        self.price_data = defaultdict(list)  # Хранение исторических цен
        self.correlation_cache = {}  # Кэш корреляций
        self.last_update = {}  # Время последнего обновления
        self.cache_duration = 300  # 5 минут кэш
        
        # Основные активы для корреляции
        self.major_assets = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT']
        
    def add_price_data(self, symbol: str, price: float, timestamp: int):
        """
        Добавление новой цены для символа
        
        Args:
            symbol: Торговый символ
            price: Цена
            timestamp: Временная метка
        """
        try:
            # Добавляем данные
            self.price_data[symbol].append({
                'price': float(price),
                'timestamp': int(timestamp)
            })
            
            # Отладочная информация (только для тестов)
            # Убираем избыточное логирование накопления данных
            
            # Ограничиваем количество записей
            max_records = self.lookback_period * 24 * 60  # По минутам
            if len(self.price_data[symbol]) > max_records:
                self.price_data[symbol] = self.price_data[symbol][-max_records:]
            
            # Очищаем кэш для этого символа
            self._clear_symbol_cache(symbol)
            
        except Exception as e:
            logger.error(f"Ошибка добавления данных для {symbol}: {e}")
    
    def calculate_correlations(self, symbol: str) -> Dict:
        """
        Расчет корреляций для символа
        
        Args:
            symbol: Торговый символ
            
        Returns:
            Dict с корреляциями
        """
        try:
            # Проверяем кэш
            if self._is_cache_valid(symbol):
                return self.correlation_cache.get(symbol, {})
            
            if symbol not in self.price_data or len(self.price_data[symbol]) < 2:  # Уменьшаем требования до 2
                logger.warning(f"Недостаточно данных для {symbol} (нужно 2, есть {len(self.price_data.get(symbol, []))})")
                return self._get_empty_correlations(symbol)
            
            # Получаем данные символа
            symbol_data = self._prepare_price_series(symbol)
            if symbol_data is None:
                return self._get_empty_correlations(symbol)
            
            correlations = {
                'symbol': symbol,
                'timestamp': int(time.time() * 1000),
                'correlations': {},
                'correlation_matrix': {},
                'market_correlation': 0.0,
                'volatility_rank': 0,
                'correlation_strength': 'neutral'
            }
            
            # Корреляции с основными активами
            for major_asset in self.major_assets:
                if major_asset != symbol and major_asset in self.price_data:
                    major_data = self._prepare_price_series(major_asset)
                    if major_data is not None:
                        corr = self._calculate_pearson_correlation(symbol_data, major_data)
                        correlations['correlations'][major_asset] = corr
            
            # Корреляция с рынком (BTC)
            if 'BTCUSDT' in correlations['correlations']:
                correlations['market_correlation'] = correlations['correlations']['BTCUSDT']
            
            # Анализ силы корреляции
            correlations['correlation_strength'] = self._analyze_correlation_strength(
                correlations['correlations']
            )
            
            # Ранг волатильности
            correlations['volatility_rank'] = self._calculate_volatility_rank(symbol)
            
            # Корреляционная матрица для топ активов
            correlations['correlation_matrix'] = self._build_correlation_matrix()
            
            # Кэшируем результат
            self.correlation_cache[symbol] = correlations
            self.last_update[symbol] = time.time()
            
            return correlations
            
        except Exception as e:
            logger.error(f"Ошибка расчета корреляций для {symbol}: {e}")
            return self._get_empty_correlations(symbol)
    
    def _prepare_price_series(self, symbol: str) -> Optional[pd.Series]:
        """Подготовка временного ряда цен"""
        try:
            if symbol not in self.price_data:
                return None
            
            data = self.price_data[symbol]
            if len(data) < 10:
                return None
            
            # Создаем DataFrame
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Ресемплируем по часам для стабильности
            df_resampled = df['price'].resample('1H').last().dropna()
            
            return df_resampled
            
        except Exception as e:
            logger.error(f"Ошибка подготовки данных для {symbol}: {e}")
            return None
    
    def _calculate_pearson_correlation(self, series1: pd.Series, series2: pd.Series) -> float:
        """Расчет корреляции Пирсона"""
        try:
            # Объединяем ряды по времени
            combined = pd.concat([series1, series2], axis=1).dropna()
            
            if len(combined) < 5:
                return 0.0
            
            # Рассчитываем корреляцию
            correlation = combined.iloc[:, 0].corr(combined.iloc[:, 1])
            
            return float(correlation) if not pd.isna(correlation) else 0.0
            
        except Exception as e:
            logger.error(f"Ошибка расчета корреляции: {e}")
            return 0.0
    
    def _analyze_correlation_strength(self, correlations: Dict) -> str:
        """Анализ силы корреляции"""
        try:
            if not correlations:
                return 'neutral'
            
            # Средняя корреляция
            avg_corr = np.mean(list(correlations.values()))
            
            if avg_corr > 0.7:
                return 'strong_positive'
            elif avg_corr > 0.3:
                return 'moderate_positive'
            elif avg_corr < -0.7:
                return 'strong_negative'
            elif avg_corr < -0.3:
                return 'moderate_negative'
            else:
                return 'weak'
                
        except Exception as e:
            logger.error(f"Ошибка анализа силы корреляции: {e}")
            return 'neutral'
    
    def _calculate_volatility_rank(self, symbol: str) -> int:
        """Расчет ранга волатильности"""
        try:
            if symbol not in self.price_data:
                return 0
            
            data = self.price_data[symbol]
            if len(data) < 20:
                return 0
            
            # Рассчитываем волатильность
            prices = [d['price'] for d in data[-20:]]
            returns = np.diff(np.log(prices))
            volatility = np.std(returns) * np.sqrt(24 * 365)  # Годовая волатильность
            
            # Ранг от 1 до 5
            if volatility > 0.8:
                return 5  # Очень высокая
            elif volatility > 0.6:
                return 4  # Высокая
            elif volatility > 0.4:
                return 3  # Средняя
            elif volatility > 0.2:
                return 2  # Низкая
            else:
                return 1  # Очень низкая
                
        except Exception as e:
            logger.error(f"Ошибка расчета волатильности для {symbol}: {e}")
            return 0
    
    def _build_correlation_matrix(self) -> Dict:
        """Построение корреляционной матрицы"""
        try:
            matrix = {}
            symbols_with_data = [s for s in self.major_assets if s in self.price_data and len(self.price_data[s]) > 10]
            
            for symbol1 in symbols_with_data:
                matrix[symbol1] = {}
                series1 = self._prepare_price_series(symbol1)
                
                for symbol2 in symbols_with_data:
                    if symbol1 == symbol2:
                        matrix[symbol1][symbol2] = 1.0
                    else:
                        series2 = self._prepare_price_series(symbol2)
                        if series1 is not None and series2 is not None:
                            corr = self._calculate_pearson_correlation(series1, series2)
                            matrix[symbol1][symbol2] = corr
                        else:
                            matrix[symbol1][symbol2] = 0.0
            
            return matrix
            
        except Exception as e:
            logger.error(f"Ошибка построения матрицы корреляций: {e}")
            return {}
    
    def _is_cache_valid(self, symbol: str) -> bool:
        """Проверка валидности кэша"""
        if symbol not in self.last_update:
            return False
        
        return (time.time() - self.last_update[symbol]) < self.cache_duration
    
    def _clear_symbol_cache(self, symbol: str):
        """Очистка кэша для символа"""
        self.correlation_cache.pop(symbol, None)
        self.last_update.pop(symbol, None)
    
    def _get_empty_correlations(self, symbol: str) -> Dict:
        """Пустые корреляции по умолчанию"""
        return {
            'symbol': symbol,
            'timestamp': int(time.time() * 1000),
            'correlations': {},
            'correlation_matrix': {},
            'market_correlation': 0.0,
            'volatility_rank': 0,
            'correlation_strength': 'neutral'
        }
    
    def get_portfolio_correlation(self, portfolio: Dict[str, float]) -> Dict:
        """
        Расчет корреляции портфеля
        
        Args:
            portfolio: Dict {symbol: weight}
            
        Returns:
            Dict с анализом портфеля
        """
        try:
            if not portfolio:
                return {}
            
            portfolio_corr = 0.0
            total_weight = sum(portfolio.values())
            
            if total_weight == 0:
                return {}
            
            # Нормализуем веса
            normalized_weights = {k: v/total_weight for k, v in portfolio.items()}
            
            # Рассчитываем средневзвешенную корреляцию с BTC
            for symbol, weight in normalized_weights.items():
                if symbol in self.correlation_cache:
                    btc_corr = self.correlation_cache[symbol].get('market_correlation', 0.0)
                    portfolio_corr += weight * btc_corr
            
            # Анализ диверсификации
            diversification_score = 1.0 - abs(portfolio_corr)
            
            return {
                'portfolio_correlation': portfolio_corr,
                'diversification_score': diversification_score,
                'risk_level': 'high' if abs(portfolio_corr) > 0.7 else 'medium' if abs(portfolio_corr) > 0.4 else 'low',
                'recommendation': self._get_diversification_recommendation(portfolio_corr)
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета корреляции портфеля: {e}")
            return {}
    
    def _get_diversification_recommendation(self, correlation: float) -> str:
        """Рекомендации по диверсификации"""
        if abs(correlation) > 0.8:
            return "Добавить активы с низкой корреляцией с BTC"
        elif abs(correlation) > 0.6:
            return "Рассмотреть альтернативные активы"
        elif abs(correlation) > 0.4:
            return "Умеренная диверсификация"
        else:
            return "Хорошо диверсифицированный портфель"
    
    def get_correlation_alerts(self, symbol: str, threshold: float = 0.8) -> List[Dict]:
        """
        Получение алертов по корреляциям
        
        Args:
            symbol: Торговый символ
            threshold: Порог для алертов
            
        Returns:
            List с алертами
        """
        try:
            alerts = []
            
            if symbol not in self.correlation_cache:
                return alerts
            
            correlations = self.correlation_cache[symbol]['correlations']
            
            for asset, corr in correlations.items():
                if abs(corr) > threshold:
                    alerts.append({
                        'symbol': symbol,
                        'correlated_asset': asset,
                        'correlation': corr,
                        'type': 'high_correlation',
                        'message': f"Высокая корреляция с {asset}: {corr:.3f}",
                        'timestamp': int(time.time() * 1000)
                    })
            
            return alerts
            
        except Exception as e:
            logger.error(f"Ошибка получения алертов для {symbol}: {e}")
            return []
    
    def clear_all_data(self):
        """Очистка всех данных"""
        self.price_data.clear()
        self.correlation_cache.clear()
        self.last_update.clear()


# Глобальный экземпляр для использования в других модулях
correlation_analyzer = CorrelationAnalyzer()


def add_price_to_correlation_analyzer(symbol: str, price: float, timestamp: int):
    """Удобная функция для добавления цены"""
    correlation_analyzer.add_price_data(symbol, price, timestamp)


def get_correlations_for_symbol(symbol: str) -> Dict:
    """Удобная функция для получения корреляций"""
    return correlation_analyzer.calculate_correlations(symbol)


if __name__ == "__main__":
    # Тест корреляционного анализатора
    analyzer = CorrelationAnalyzer()
    
    # Добавляем тестовые данные
    base_time = int(time.time() * 1000)
    for i in range(100):
        timestamp = base_time + i * 60000  # Каждую минуту
        
        # BTC с трендом
        btc_price = 45000 + i * 10 + np.random.normal(0, 100)
        analyzer.add_price_data('BTCUSDT', btc_price, timestamp)
        
        # ETH с высокой корреляцией с BTC
        eth_price = 3000 + i * 0.7 + np.random.normal(0, 10)
        analyzer.add_price_data('ETHUSDT', eth_price, timestamp)
        
        # ADA с низкой корреляцией
        ada_price = 0.5 + np.sin(i * 0.1) * 0.1 + np.random.normal(0, 0.02)
        analyzer.add_price_data('ADAUSDT', ada_price, timestamp)
    
    # Тестируем расчеты
    btc_corr = analyzer.calculate_correlations('BTCUSDT')
    eth_corr = analyzer.calculate_correlations('ETHUSDT')
    ada_corr = analyzer.calculate_correlations('ADAUSDT')
    
    print("Тест корреляционного анализатора:")
    print(f"BTC корреляции: {btc_corr['correlations']}")
    print(f"ETH корреляции: {eth_corr['correlations']}")
    print(f"ADA корреляции: {ada_corr['correlations']}")
    print(f"Матрица корреляций: {btc_corr['correlation_matrix']}") 