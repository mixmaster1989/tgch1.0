#!/usr/bin/env python3
"""
Тест торгового анализатора
"""

import sys
import traceback
from market_analyzer import MarketAnalyzer
from neural_analyzer import NeuralAnalyzer

def test_neural_analyzer():
    """Тест нейронного анализатора"""
    print("=== ТЕСТ НЕЙРОННОГО АНАЛИЗАТОРА ===")
    
    try:
        analyzer = NeuralAnalyzer()
        
        # Тестовые данные
        test_data = {
            'symbol': 'BTCUSDT',
            'current_price': 45000.0,
            'price_change_24h': 2.5,
            'volume_24h': 1000000,
            'rsi': 65,
            'trend': 'UP',
            'volume_ratio': 1.3
        }
        
        print(f"Анализ {test_data['symbol']}...")
        result = analyzer.analyze_market_data(
            test_data['symbol'], 
            test_data['current_price'], 
            test_data
        )
        
        print(f"Результат: {result}")
        return True
        
    except Exception as e:
        print(f"Ошибка в нейронном анализаторе: {e}")
        traceback.print_exc()
        return False

def test_market_analyzer():
    """Тест рыночного анализатора"""
    print("\n=== ТЕСТ РЫНОЧНОГО АНАЛИЗАТОРА ===")
    
    try:
        analyzer = MarketAnalyzer()
        
        print("Получение рыночных данных...")
        market_data = analyzer.get_market_data()
        print(f"Получено {len(market_data)} торговых пар")
        
        if len(market_data) > 0:
            print("Первые 3 пары:")
            for i, ticker in enumerate(market_data[:3]):
                print(f"  {i+1}. {ticker['symbol']} - {ticker['priceChangePercent']}%")
        
        print("\nФильтрация кандидатов...")
        candidates = analyzer.filter_trading_candidates(market_data[:20])  # Тестируем на первых 20
        print(f"Найдено {len(candidates)} кандидатов")
        
        if len(candidates) > 0:
            print("Топ кандидат:")
            top = candidates[0]
            print(f"  Символ: {top['symbol']}")
            print(f"  Скор: {top['score']}")
            print(f"  Причины: {', '.join(top['reasons'])}")
            
            print("\nТест ИИ анализа...")
            ai_result = analyzer.analyze_with_ai(top)
            print(f"  Рекомендация: {ai_result['recommendation']}")
            print(f"  Уверенность: {ai_result['confidence']}")
            print(f"  Анализ: {ai_result['analysis'][:100]}...")
        
        return True
        
    except Exception as e:
        print(f"Ошибка в рыночном анализаторе: {e}")
        traceback.print_exc()
        return False

def main():
    """Основная функция тестирования"""
    print("ДИАГНОСТИКА ТОРГОВОГО АНАЛИЗА")
    print("=" * 50)
    
    # Тест 1: Нейронный анализатор
    neural_ok = test_neural_analyzer()
    
    # Тест 2: Рыночный анализатор  
    market_ok = test_market_analyzer()
    
    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ ТЕСТОВ:")
    print(f"  Нейронный анализатор: {'OK' if neural_ok else 'FAIL'}")
    print(f"  Рыночный анализатор: {'OK' if market_ok else 'FAIL'}")
    
    if neural_ok and market_ok:
        print("\nВсе тесты прошли успешно!")
    else:
        print("\nЕсть проблемы, требующие исправления")

if __name__ == "__main__":
    main()