"""
Модуль для расчета уровней входа, тейк-профита и стоп-лосса.
"""
import yaml
import numpy as np

class LevelsCalculator:
    def __init__(self):
        # Загрузка конфигурации
        with open('configs/thresholds.yaml', 'r') as f:
            self.config = yaml.safe_load(f)['risk_management']

    def calculate_levels(self, entry_price: float, volatility: float, signal_type: str) -> dict:
        """
        Расчет уровней входа, стопа и тейков на основе волатильности
        """
        # Расчет уровней на основе ATR
        atr = volatility  # Предполагается, что волатильность передается как ATR

        # Расчет стоп-лосса
        stop_distance = atr * self.config['stop_multiplier']
        stop_price = entry_price * (1 - stop_distance if signal_type == 'Long' else 1 + stop_distance)

        # Расчет тейк-профитов
        tp1_distance = atr * self.config['tp1_multiplier']
        tp1_price = entry_price * (1 + tp1_distance if signal_type == 'Long' else 1 - tp1_distance)

        tp2_distance = atr * self.config['tp2_multiplier']
        tp2_price = entry_price * (1 + tp2_distance if signal_type == 'Long' else 1 - tp2_distance)

        # Расчет R:R
        rr_ratio = ((tp1_price - entry_price) + (tp2_price - entry_price)) / abs(entry_price - stop_price)

        return {
            'entry': entry_price,
            'stop': stop_price,
            'tp1': tp1_price,
            'tp2': tp2_price,
            'rr_ratio': rr_ratio
        }