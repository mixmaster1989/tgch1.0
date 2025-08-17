#!/usr/bin/env python3
"""
Тест режима заглушек AI Trading Analyzer
Проверяет работу системы без траты кредитов OpenRouter
"""

import asyncio
from datetime import datetime
from ai_trading_analyzer import AITradingAnalyzer

async def test_stubs_mode():
    """Тест режима заглушек"""
    print("🔧 ТЕСТ РЕЖИМА ЗАГЛУШЕК AI TRADING ANALYZER")
    print("=" * 60)
    
    # Создаем анализатор
    ai_analyzer = AITradingAnalyzer()
    
    # Проверяем режим
    print(f"📊 Режим заглушек: {'ВКЛЮЧЕН' if ai_analyzer.STUBS_MODE else 'ВЫКЛЮЧЕН'}")
    print(f"💰 Экономия кредитов: {'ДА' if ai_analyzer.STUBS_MODE else 'НЕТ'}")
    print()
    
    # Создаем тестовые данные
    test_market_data = {
        "symbol": "ETHUSDT",
        "price": 3908.28,
        "change_24h": 0.0558,
        "volume_24h": 161764.47,
        "high_24h": 3968.0,
        "low_24h": 3694.7
    }
    
    test_perplexity_data = {
        "overall_sentiment": "positive",
        "overall_confidence": 0.8,
        "impact_score": 0.75,
        "news_analysis": {
            "sentiment": "positive",
            "key_events": ["Институциональный спрос растет", "Рост TVL в DeFi"]
        }
    }
    
    print("🤖 Запуск анализа с заглушками...")
    
    # Получаем торговое решение
    trading_decision = await ai_analyzer.analyze_and_decide(test_market_data, test_perplexity_data)
    
    print("\n📋 РЕЗУЛЬТАТЫ АНАЛИЗА:")
    print("-" * 40)
    
    # Решения экспертов
    expert_responses = trading_decision.get('expert_analysis', {}).get('responses', [])
    print("👨‍💼 РЕШЕНИЯ ЭКСПЕРТОВ:")
    for response in expert_responses:
        if isinstance(response, dict):
            expert_name = response.get('expert', 'UNKNOWN')
            decision = response.get('decision', 'UNKNOWN')
            confidence = response.get('confidence', 0.0)
            reason = response.get('reason', 'N/A')[:100] + "..." if len(response.get('reason', '')) > 100 else response.get('reason', 'N/A')
            print(f"   🔍 {expert_name.upper()}: {decision} (уверенность: {confidence:.2f})")
            print(f"      Причина: {reason}")
            print()
    
    # Финальное решение судьи
    final_decision = trading_decision.get('final_decision', {})
    print("⚖️ ФИНАЛЬНОЕ РЕШЕНИЕ СУДЬИ:")
    print(f"   Решение: {final_decision.get('final_decision', 'UNKNOWN')}")
    print(f"   Уверенность: {final_decision.get('confidence', 0.0):.2f}")
    print(f"   Причина: {final_decision.get('reason', 'N/A')[:150]}...")
    
    # Анализ экспертов
    expert_analysis = final_decision.get('expert_analysis', {})
    if expert_analysis:
        print(f"   Лучший эксперт: {expert_analysis.get('best_expert', 'N/A')}")
        print(f"   Согласие экспертов: {expert_analysis.get('expert_agreement', 'N/A')}")
        print(f"   Оценка рисков: {expert_analysis.get('risk_assessment', 'N/A')}")
    
    print("\n✅ ТЕСТ ЗАВЕРШЕН")
    print("💰 Кредиты OpenRouter НЕ потрачены!")
    print("🔧 Система готова к активации реальных нейронок")

if __name__ == "__main__":
    asyncio.run(test_stubs_mode())
