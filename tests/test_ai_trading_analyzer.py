#!/usr/bin/env python3
"""
Тест AI Trading Analyzer
"""

import asyncio
import json
from ai_trading_analyzer import AITradingAnalyzer

async def test_ai_trading_analyzer():
    """Тест AI Trading Analyzer"""
    print("=== ТЕСТ AI TRADING ANALYZER ===")
    
    try:
        analyzer = AITradingAnalyzer()
        
        # Тестируем анализ ETH
        symbol = "ETHUSDT"
        print(f"\n🤖 Тестируем анализ {symbol}...")
        
        # Получаем торговое решение
        result = await analyzer.analyze_and_decide(symbol)
        
        print(f"\n✅ Результат анализа:")
        print(f"   Символ: {result['symbol']}")
        print(f"   Финальное решение: {result['final_decision'].get('final_decision', 'N/A')}")
        print(f"   Уверенность: {result['final_decision'].get('confidence', 0):.2f}")
        print(f"   Следует торговать: {result['should_trade']}")
        
        # Детали решения
        if 'reason' in result['final_decision']:
            print(f"   Причина: {result['final_decision']['reason'][:200]}...")
        
        # Анализ экспертов
        if 'expert_analysis' in result['final_decision']:
            expert_analysis = result['final_decision']['expert_analysis']
            print(f"   Лучший эксперт: {expert_analysis.get('best_expert', 'N/A')}")
            print(f"   Согласие экспертов: {expert_analysis.get('expert_agreement', 'N/A')}")
            print(f"   Оценка рисков: {expert_analysis.get('risk_assessment', 'N/A')}")
        
        # Решения экспертов
        print(f"\n👨‍💼 Решения экспертов:")
        for decision in result['expert_decisions']:
            print(f"   {decision['expert']}: {decision['decision']} (уверенность: {decision['confidence']:.2f})")
            if 'reason' in decision:
                print(f"     Причина: {decision['reason'][:100]}...")
        
        # Данные
        print(f"\n📊 Данные:")
        data_summary = result['data_summary']
        print(f"   Настроение рынка: {data_summary.get('market_sentiment', 'N/A')}")
        print(f"   Уверенность Perplexity: {data_summary.get('perplexity_confidence', 'N/A')}")
        print(f"   Текущая цена: {data_summary.get('current_price', 'N/A')}")
        
        # Сохраняем результат в файл для анализа
        with open(f"trading_analysis_{symbol}_{result['timestamp'][:10]}.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Результат сохранен в файл")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_multiple_symbols():
    """Тест нескольких символов"""
    print("\n=== ТЕСТ НЕСКОЛЬКИХ СИМВОЛОВ ===")
    
    try:
        analyzer = AITradingAnalyzer()
        
        symbols = ["BTCUSDT", "ETHUSDT"]
        
        for symbol in symbols:
            print(f"\n🔍 Анализ {symbol}...")
            
            result = await analyzer.analyze_and_decide(symbol)
            
            decision = result['final_decision'].get('final_decision', 'HOLD')
            confidence = result['final_decision'].get('confidence', 0)
            should_trade = result['should_trade']
            
            print(f"   Решение: {decision}")
            print(f"   Уверенность: {confidence:.2f}")
            print(f"   Торговать: {should_trade}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте множественных символов: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов AI Trading Analyzer...")
    
    # Запускаем тесты
    async def run_tests():
        success1 = await test_ai_trading_analyzer()
        success2 = await test_multiple_symbols()
        
        if success1 and success2:
            print("\n🎉 Все тесты прошли успешно!")
        else:
            print("\n❌ Некоторые тесты не прошли")
    
    asyncio.run(run_tests())
