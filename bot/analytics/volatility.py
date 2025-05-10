import numpy as np

class VolatilityAnalyzer:
    def calculate_atr(self, historical_data, period=14):
        """Рассчитывает Average True Range (ATR)"""
        tr_values = []
        
        for i in range(1, len(historical_data)):
            high = historical_data[i]['high']
            low = historical_data[i]['low']
            prev_close = historical_data[i-1]['close']
            
            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close)
            )
            tr_values.append(tr)
        
        atr = np.mean(tr_values[-period:])
        return atr

    def calculate_horizon(self, volatility):
        """Определяет временной горизонт сигнала"""
        if volatility < 3:
            return "4H"
        elif volatility < 7:
            return "1H"
        else:
            return "30M"