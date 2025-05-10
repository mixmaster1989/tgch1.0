from .clustering import PriceClusterAnalyzer
from .volatility import VolatilityAnalyzer
from ..risk.confidence import ConfidenceCalculator

class SmartMoneySignal:
    def __init__(self):
        self.cluster_analyzer = PriceClusterAnalyzer()
        self.volatility_analyzer = VolatilityAnalyzer()
        self.confidence_calculator = ConfidenceCalculator()

    def generate_signal(self, pair, historical_data):
        """Генерирует комплексный трейдинг-сигнал"""
        # Анализ кластеров цен
        clusters = self._analyze_clusters(pair)
        
        # Расчет волатильности и временного горизонта
        volatility = self.volatility_analyzer.calculate_atr(historical_data)
        time_horizon = self.volatility_analyzer.calculate_horizon(volatility)
        
        # Определение направления сигнала
        direction = self._determine_direction(clusters)
        
        # Расчет уровней входа, стопа и тейков
        entry, stop, tp1, tp2 = self._calculate_levels(clusters, volatility, direction)
        
        # Расчет уверенности в сигнале
        confidence = self.confidence_calculator.calculate_confidence({
            'pair': pair,
            'direction': direction,
            'entry': entry
        })
        
        # Расчет R:R (риск/прибыль)
        rr_ratio = self._calculate_rr_ratio(entry, stop, tp1, tp2, direction)
        
        return {
            'pair': pair,
            'direction': direction,
            'entry': entry,
            'stop': stop,
            'tp1': tp1,
            'tp2': tp2,
            'confidence': confidence,
            'rr_ratio': rr_ratio,
            'time_horizon': time_horizon
        }

    def _analyze_clusters(self, pair):
        """Анализ ценовых кластеров для определения ключевых уровней"""
        # Реализация анализа кластеров
        return {
            'price_mode': 30000.0,  # Пример значения
            'support_levels': [29500, 29000],
            'resistance_levels': [30500, 31000]
        }

    def _determine_direction(self, clusters):
        """Определение направления сигнала (long/short)"""
        # Реализация определения направления
        return 'long'  # Пример значения

    def _calculate_levels(self, clusters, volatility, direction):
        """Расчет уровней входа, стопа и тейков"""
        # Использование уровней кластеров и волатильности
        return calculate_levels(clusters, volatility, direction)

    def _calculate_rr_ratio(self, entry, stop, tp1, tp2, direction):
        """Рассчитывает соотношение риск/прибыль"""
        if direction == 'long':
            risk = entry - stop
            profit = max(tp1, tp2) - entry
        else:
            risk = stop - entry
            profit = entry - max(tp1, tp2)
        
        return profit / risk if risk > 0 else 0