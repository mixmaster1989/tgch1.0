#!/usr/bin/env python3
"""
Быстрое исправление анализатора
"""

from market_analyzer import MarketAnalyzer

def main():
    analyzer = MarketAnalyzer()
    
    # Получаем данные
    market_data = analyzer.get_market_data()
    print(f"Всего пар: {len(market_data)}")
    
    # Проверяем первые 10 пар
    for i, ticker in enumerate(market_data[:10]):
        symbol = ticker['symbol']
        price_change = float(ticker['priceChangePercent'])
        volume = float(ticker['quoteVolume'])
        
        print(f"{i+1}. {symbol}")
        print(f"   Изменение: {price_change:.3f}%")
        print(f"   Объем: {volume:.0f}")
        print(f"   Проходит фильтр: {abs(price_change) <= 25.0 and volume >= 10000}")
        print()

if __name__ == "__main__":
    main()