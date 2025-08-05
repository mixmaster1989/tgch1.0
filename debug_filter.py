#!/usr/bin/env python3
"""
Отладка фильтра кандидатов
"""

from market_analyzer import MarketAnalyzer

def main():
    analyzer = MarketAnalyzer()
    
    # Получаем данные
    market_data = analyzer.get_market_data()
    print(f"Всего пар: {len(market_data)}")
    
    # Тестируем первые 5 пар
    for i, ticker in enumerate(market_data[:5]):
        symbol = ticker['symbol']
        price_change = float(ticker['priceChangePercent'])
        volume = float(ticker['quoteVolume'])
        
        print(f"\n=== {symbol} ===")
        print(f"Изменение: {price_change:.3f}%")
        print(f"Объем: {volume:.0f}")
        
        # Базовый фильтр
        if abs(price_change) > 25.0 or volume < 10000:
            print("FAIL Не прошел базовый фильтр")
            continue
            
        print("OK Прошел базовый фильтр")
        
        # Получаем технические данные
        klines = analyzer.get_klines(symbol)
        if not klines:
            print("FAIL Нет данных klines")
            continue
            
        print(f"OK Получено {len(klines)} свечей")
        
        tech_data = analyzer.calculate_technical_indicators(klines)
        if not tech_data:
            print("FAIL Ошибка расчета индикаторов")
            continue
            
        print(f"OK RSI: {tech_data['rsi']:.1f}")
        print(f"OK Тренд: {tech_data['trend']}")
        print(f"OK Объем ratio: {tech_data['volume_ratio']:.2f}")
        
        # Подсчет скора
        score = 0
        reasons = []
        
        if tech_data['volume_ratio'] > 1.5:
            score += 2
            reasons.append("высокий_объем")
        
        if 30 < tech_data['rsi'] < 70:
            score += 1
            reasons.append("нормальный_rsi")
        elif tech_data['rsi'] < 35:
            score += 2
            reasons.append("перепродано")
        
        if tech_data['trend'] == 'UP' and tech_data['price_change_1h'] > 0:
            score += 2
            reasons.append("восходящий_тренд")
        
        if tech_data['current_price'] > tech_data['sma_20']:
            score += 1
            reasons.append("выше_sma20")
        
        print(f"Скор: {score}")
        print(f"Причины: {reasons}")
        print(f"Проходит (скор >= 1): {'OK' if score >= 1 else 'FAIL'}")

if __name__ == "__main__":
    main()