class ConfidenceCalculator:
    def calculate_confidence(self, signal, config=None):
        """Рассчитывает процент уверенности в сигнале"""
        if config is None:
            config = {
                'volume_weight': 0.4,
                'rsi_weight': 0.3,
                'density_weight': 0.3
            }
        
        volume_score = self._calculate_volume_score(signal)
        rsi_score = self._calculate_rsi_score(signal)
        density_score = self._calculate_density_score(signal)
        
        total_confidence = (
            volume_score * config['volume_weight'] +
            rsi_score * config['rsi_weight'] +
            density_score * config['density_weight']
        )
        
        return min(100, max(0, int(total_confidence * 100) / 100))

    def _calculate_volume_score(self, signal):
        """Оценка по объему торгов"""
        # Реальная реализация будет использовать данные из Cryptorank
        return 0.8  # Заглушка для примера

    def _calculate_rsi_score(self, signal):
        """Оценка по RSI"""
        # Реальная реализация будет использовать технический анализ
        return 0.7  # Заглушка для примера

    def _calculate_density_score(self, signal):
        """Оценка по плотности ценовых уровней"""
        # Реальная реализация будет использовать кластерный анализ
        return 0.75  # Заглушка для примера