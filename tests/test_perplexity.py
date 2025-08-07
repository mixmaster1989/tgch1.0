#!/usr/bin/env python3
"""
Тест Perplexity модели для сбора новостей о криптовалютах
"""

import requests
import json
import sys
import os

# Добавляем корневую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

def test_perplexity_news_search():
    """Тест поиска новостей о монете через Perplexity"""
    
    if not OPENROUTER_API_KEY:
        print("❌ Ошибка: OPENROUTER_API_KEY не найден в .env файле")
        return
    
    print("🔍 Тестирую Perplexity модель для поиска новостей...")
    print(f"📡 API Key: {OPENROUTER_API_KEY[:10]}...")
    
    # Промпт для поиска новостей о монете "pump"
    prompt = """
    Найди последние новости и события о криптовалюте "pump" за последние 7 дней.
    
    Собери следующую информацию:
    1. Последние новости и анонсы
    2. Изменения в цене и объеме торгов
    3. Партнерства или интеграции
    4. Технические обновления
    5. Регулятивные новости
    6. Социальные тренды и упоминания
    
    ВАЖНО: Верни ТОЛЬКО валидный JSON без дополнительного текста.
    
    {
        "symbol": "PUMP",
        "recent_news": [
            {
                "date": "YYYY-MM-DD",
                "title": "Заголовок новости",
                "summary": "Краткое описание",
                "source": "Источник",
                "impact": "positive/negative/neutral"
            }
        ],
        "price_analysis": {
            "current_trend": "up/down/sideways",
            "volume_change": "increased/decreased",
            "notable_movements": []
        },
        "partnerships": [],
        "technical_updates": [],
        "regulatory_news": [],
        "social_sentiment": "positive/negative/neutral"
    }
    
    Если информации мало, верни JSON с пустыми массивами. Не добавляй комментарии вне JSON.
    """
    
    try:
        # Запрос к OpenRouter API
        response = requests.post(
            url=f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://mex-trading-bot.com",
                "X-Title": "MEX Trading Bot"
            },
            json={
                "model": "perplexity/sonar-reasoning",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "max_tokens": 4000
            },
            timeout=60
        )
        
        print(f"📊 Статус ответа: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                
                print("\n✅ Успешный ответ от Perplexity:")
                print("=" * 50)
                print(content)
                print("=" * 50)
                
                # Попытка извлечь JSON из ответа
                try:
                    # Ищем JSON в ответе
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    
                    if json_start != -1 and json_end > json_start:
                        json_str = content[json_start:json_end]
                        parsed_data = json.loads(json_str)
                        
                        print("\n📋 Структурированные данные:")
                        print(f"Символ: {parsed_data.get('symbol', 'N/A')}")
                        print(f"Новостей найдено: {len(parsed_data.get('recent_news', []))}")
                        print(f"Настроения: {parsed_data.get('social_sentiment', 'N/A')}")
                        
                        # Показываем первые 3 новости
                        news = parsed_data.get('recent_news', [])
                        if news:
                            print("\n📰 Последние новости:")
                            for i, item in enumerate(news[:3], 1):
                                print(f"{i}. {item.get('title', 'N/A')}")
                                print(f"   Дата: {item.get('date', 'N/A')}")
                                print(f"   Влияние: {item.get('impact', 'N/A')}")
                                print()
                    else:
                        print("⚠️ JSON не найден в ответе")
                        
                except json.JSONDecodeError as e:
                    print(f"⚠️ Ошибка парсинга JSON: {e}")
                    print("Ответ получен, но не в JSON формате")
                
                # Информация о токенах
                if 'usage' in result:
                    usage = result['usage']
                    print(f"\n📊 Использование токенов:")
                    print(f"Входные: {usage.get('prompt_tokens', 0)}")
                    print(f"Выходные: {usage.get('completion_tokens', 0)}")
                    print(f"Всего: {usage.get('total_tokens', 0)}")
                
            else:
                print("❌ Неожиданный формат ответа")
                print(f"Ответ: {result}")
                
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут запроса (60 секунд)")
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")

def test_perplexity_simple_query():
    """Простой тест Perplexity для проверки подключения"""
    
    print("\n🔧 Простой тест подключения...")
    
    try:
        response = requests.post(
            url=f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "perplexity/sonar-reasoning",
                "messages": [
                    {
                        "role": "user",
                        "content": "Какая текущая цена Bitcoin?"
                    }
                ],
                "temperature": 0.1,
                "max_tokens": 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"✅ Простой тест успешен:")
            print(f"Ответ: {content[:200]}...")
        else:
            print(f"❌ Ошибка простого теста: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Ошибка простого теста: {e}")

if __name__ == "__main__":
    print("🚀 Запуск теста Perplexity модели")
    print("=" * 50)
    
    # Сначала простой тест
    test_perplexity_simple_query()
    
    # Затем полный тест с поиском новостей
    test_perplexity_news_search()
    
    print("\n🏁 Тест завершен") 