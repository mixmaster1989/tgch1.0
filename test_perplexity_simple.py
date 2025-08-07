#!/usr/bin/env python3
"""
Простой тест Perplexity анализатора
"""

import asyncio
from perplexity_analyzer import PerplexityAnalyzer
from openrouter_manager import OpenRouterManager

def test_openrouter_status():
    """Проверить статус OpenRouter ключей"""
    print("=== ПРОВЕРКА OPENROUTER СТАТУСА ===")
    
    try:
        openrouter = OpenRouterManager()
        status = openrouter.get_status()
        
        print(f"Golden key доступен: {status['golden_key_available']}")
        print(f"Silver ключей всего: {status['silver_keys_total']}")
        print(f"Silver ключей заблокировано: {status['silver_keys_failed']}")
        print(f"Silver ключей доступно: {status['silver_keys_available']}")
        
        return status['silver_keys_available'] > 0
        
    except Exception as e:
        print(f"❌ Ошибка проверки статуса: {e}")
        return False

async def test_simple_perplexity():
    """Простой тест Perplexity анализатора"""
    print("\n=== ПРОСТОЙ ТЕСТ PERPLEXITY ===")
    
    try:
        analyzer = PerplexityAnalyzer()
        
        # Тестируем только анализ новостей для ETH
        symbol = "ETHUSDT"
        print(f"🔍 Тестируем анализ новостей для {symbol}...")
        
        news = await analyzer.analyze_coin_news(symbol)
        
        if news and "news_analysis" in news:
            news_data = news["news_analysis"]
            print(f"✅ Новости получены успешно!")
            print(f"   Настроение: {news_data.get('sentiment', 'N/A')}")
            print(f"   Impact Score: {news_data.get('impact_score', 'N/A')}")
            print(f"   Уверенность: {news_data.get('confidence', 'N/A')}")
            
            if "key_events" in news_data:
                print(f"   Ключевых событий: {len(news_data['key_events'])}")
                for i, event in enumerate(news_data['key_events'][:2]):  # Показываем первые 2
                    print(f"     {i+1}. {event.get('title', 'N/A')}")
            
            return True
        else:
            print(f"❌ Ошибка получения новостей: {news}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Простой тест Perplexity анализатора...")
    
    # Проверяем статус OpenRouter
    if not test_openrouter_status():
        print("❌ Нет доступных ключей OpenRouter")
        exit(1)
    
    # Запускаем простой тест
    success = asyncio.run(test_simple_perplexity())
    
    if success:
        print("\n🎉 Тест прошел успешно!")
    else:
        print("\n❌ Тест не прошел")
