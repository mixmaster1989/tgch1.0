class ConfidenceCalculator:
    def calculate_confidence(self, signal):
        """Рассчитывает процент уверенности в сигнале"""
        volume_score = self._calculate_volume_score(signal)
        rsi_score = self._calculate_rsi_score(signal)
        density_score = self._calculate_density_score(signal)
        
        # Веса из конфигурации
        weights = {
            'volume': 0.4,
            'rsi': 0.3,
            'density': 0.3
        }
        
        total_confidence = (
            volume_score * weights['volume'] +
            rsi_score * weights['rsi'] +
            density_score * weights['density']
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