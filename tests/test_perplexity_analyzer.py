#!/usr/bin/env python3
"""
Тест расширенного Perplexity анализатора
"""

import asyncio
import json
from perplexity_analyzer import PerplexityAnalyzer

async def test_perplexity_analyzer():
    """Тест Perplexity анализатора"""
    print("=== ТЕСТ PERPLEXITY АНАЛИЗАТОРА ===")
    
    try:
        analyzer = PerplexityAnalyzer()
        
        # Тестируем анализ ETH
        symbol = "ETHUSDT"
        print(f"\n🔍 Тестируем анализ {symbol}...")
        
        # Комплексный анализ
        print("📊 Получаем комплексный анализ...")
        comprehensive = await analyzer.get_comprehensive_analysis(symbol)
        
        print(f"✅ Результат комплексного анализа:")
        print(f"   Символ: {comprehensive['symbol']}")
        print(f"   Общее настроение: {comprehensive['overall_sentiment']}")
        print(f"   Уверенность: {comprehensive['overall_confidence']:.2f}")
        print(f"   Impact Score: {comprehensive['impact_score']:.2f}")
        
        # Детальный вывод новостей
        if "news_analysis" in comprehensive and comprehensive["news_analysis"]:
            news_data = comprehensive["news_analysis"]["news_analysis"]
            print(f"   📰 Новости: {news_data.get('sentiment', 'N/A')}")
            print(f"   📊 Market Outlook: {news_data.get('market_outlook', 'N/A')}")
            if "key_events" in news_data:
                print(f"   📅 Ключевых событий: {len(news_data['key_events'])}")
                for i, event in enumerate(news_data['key_events'][:3]):  # Показываем первые 3
                    print(f"     {i+1}. {event.get('title', 'N/A')}")
                    print(f"        Impact: {event.get('impact', 'N/A')}, Sentiment: {event.get('sentiment', 'N/A')}")
                    print(f"        Summary: {event.get('summary', 'N/A')}")
        
        # Детальный вывод настроений
        if "sentiment_analysis" in comprehensive and comprehensive["sentiment_analysis"]:
            sentiment_data = comprehensive["sentiment_analysis"]["sentiment_analysis"]
            print(f"   😊 Социальные настроения: {sentiment_data.get('social_sentiment', 'N/A')}")
            print(f"   📈 Аналитики: {sentiment_data.get('analyst_sentiment', 'N/A')}")
            print(f"   🔗 Корреляции: {sentiment_data.get('correlation_analysis', 'N/A')}")
            print(f"   📝 Summary: {sentiment_data.get('summary', 'N/A')}")
        
        # Детальный вывод технического анализа
        if "technical_analysis" in comprehensive and comprehensive["technical_analysis"]:
            tech_data = comprehensive["technical_analysis"]["technical_analysis"]
            print(f"   ⚙️ Технический скор: {tech_data.get('technical_score', 'N/A')}")
            if "on_chain_metrics" in tech_data:
                on_chain = tech_data["on_chain_metrics"]
                print(f"   🔗 On-chain: адреса={on_chain.get('active_addresses', 'N/A')}, транзакции={on_chain.get('large_transactions', 'N/A')}")
            if "defi_metrics" in tech_data:
                defi = tech_data["defi_metrics"]
                print(f"   🏦 DeFi: TVL={defi.get('tvl_trend', 'N/A')}, Volume={defi.get('volume_trend', 'N/A')}")
            print(f"   📊 Анализ: {tech_data.get('analysis', 'N/A')}")
        
        # Тестируем отдельные компоненты
        print(f"\n🔍 Тестируем отдельные компоненты для {symbol}...")
        
        # Анализ новостей
        print("📰 Анализ новостей...")
        news = await analyzer.analyze_coin_news(symbol)
        if news:
            print(f"   ✅ Новости получены: {news.get('news_analysis', {}).get('sentiment', 'N/A')}")
        else:
            print("   ❌ Ошибка получения новостей")
        
        # Анализ настроений
        print("😊 Анализ настроений...")
        sentiment = await analyzer.analyze_market_sentiment(symbol)
        if sentiment:
            print(f"   ✅ Настроения получены: {sentiment.get('sentiment_analysis', {}).get('social_sentiment', 'N/A')}")
        else:
            print("   ❌ Ошибка получения настроений")
        
        # Технический анализ
        print("⚙️ Технический анализ...")
        technical = await analyzer.analyze_technical_factors(symbol)
        if technical:
            print(f"   ✅ Технический анализ получен: {technical.get('technical_analysis', {}).get('technical_score', 'N/A')}")
        else:
            print("   ❌ Ошибка технического анализа")
        
        # Закрываем анализатор
        analyzer.close()
        
        print(f"\n✅ Тест завершен успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_multiple_symbols():
    """Тест анализа нескольких символов"""
    print("\n=== ТЕСТ НЕСКОЛЬКИХ СИМВОЛОВ ===")
    
    try:
        analyzer = PerplexityAnalyzer()
        
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        
        for symbol in symbols:
            print(f"\n🔍 Анализ {symbol}...")
            
            # Быстрый анализ новостей
            news = await analyzer.analyze_coin_news(symbol)
            if news and "news_analysis" in news:
                sentiment = news["news_analysis"].get("sentiment", "N/A")
                confidence = news["news_analysis"].get("confidence", 0)
                print(f"   📰 Настроение: {sentiment}, Уверенность: {confidence:.2f}")
            else:
                print(f"   ❌ Ошибка анализа {symbol}")
        
        analyzer.close()
        print(f"\n✅ Тест множественных символов завершен!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в тесте множественных символов: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов Perplexity анализатора...")
    
    # Запускаем тесты
    async def run_tests():
        success1 = await test_perplexity_analyzer()
        success2 = await test_multiple_symbols()
        
        if success1 and success2:
            print("\n🎉 Все тесты прошли успешно!")
        else:
            print("\n❌ Некоторые тесты не прошли")
    
    asyncio.run(run_tests())
