#!/usr/bin/env python3
"""
Perplexity Analyzer для анализа новостей и рыночных данных
Получает данные через OpenRouter с Perplexity моделью для принятия торговых решений
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from openrouter_manager import OpenRouterManager

class PerplexityAnalyzer:
    """Анализатор новостей и рыночных данных через Perplexity модель в OpenRouter"""
    
    def __init__(self):
        self.openrouter = OpenRouterManager()
        self.perplexity_model = "perplexity/sonar-reasoning"  # Perplexity модель в OpenRouter
        
    async def _make_request(self, query: str, focus: str = "news") -> Optional[Dict]:
        """Выполнить запрос через OpenRouter с Perplexity моделью"""
        try:
            # Формируем промпт в зависимости от типа запроса
            if focus == "news":
                prompt = f"""
                Проанализируй последние новости и события для {query} за последние 24 часа.
                Сфокусируйся на:
                1. Критических новостях (обновления, взломы, регулятивные решения)
                2. Институциональных событиях (ETF, крупные инвестиции)
                3. Технических событиях (проблемы сети, обновления)
                4. Рыночных настроениях
                
                Верни ответ в формате JSON:
                {{
                    "sentiment": "positive/negative/neutral",
                    "impact_score": 0.0-1.0,
                    "key_events": [
                        {{
                            "title": "заголовок события",
                            "impact": "high/medium/low",
                            "sentiment": "positive/negative/neutral",
                            "summary": "краткое описание"
                        }}
                    ],
                    "market_outlook": "краткий прогноз",
                    "confidence": 0.0-1.0
                }}
                """
            elif focus == "technical":
                prompt = f"""
                Проанализируй технические аспекты {query}:
                1. On-chain метрики (активность адресов, крупные транзакции)
                2. DeFi метрики (TVL, объемы торгов)
                3. Майнинг данные (хешрейт, сложность)
                4. Технические индикаторы рынка
                
                Верни ответ в формате JSON:
                {{
                    "technical_score": 0.0-1.0,
                    "on_chain_metrics": {{
                        "active_addresses": "trend",
                        "large_transactions": "count",
                        "network_health": "status"
                    }},
                    "defi_metrics": {{
                        "tvl_trend": "up/down/stable",
                        "volume_trend": "up/down/stable"
                    }},
                    "analysis": "технический анализ"
                }}
                """
            else:  # market sentiment
                prompt = f"""
                Проанализируй рыночные настроения для {query}:
                1. Социальные настроения (Twitter, Reddit, Telegram)
                2. Мнения аналитиков и трейдеров
                3. Корреляции с традиционными рынками
                4. Институциональные отчеты
                
                Верни ответ в формате JSON:
                {{
                    "social_sentiment": "positive/negative/neutral",
                    "analyst_sentiment": "positive/negative/neutral",
                    "correlation_analysis": "корреляция с традиционными рынками",
                    "confidence": 0.0-1.0,
                    "summary": "общий анализ настроений"
                }}
                """
            
            # Используем golden key для важных торговых решений
            result = self.openrouter.request_with_golden_key(prompt, self.perplexity_model)
            
            if result['success']:
                content = result['response']
                
                # Пытаемся извлечь JSON из ответа
                try:
                    if '{' in content and '}' in content:
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        json_str = content[json_start:json_end]
                        return json.loads(json_str)
                    else:
                        return {"error": "Не удалось извлечь JSON", "raw_response": content}
                except json.JSONDecodeError:
                    return {"error": "Ошибка парсинга JSON", "raw_response": content}
            else:
                return {"error": f"API ошибка: {result['response']}"}
                    
        except Exception as e:
            print(f"❌ Ошибка запроса к Perplexity через OpenRouter: {e}")
            return {"error": str(e)}
    
    async def analyze_coin_news(self, symbol: str) -> Optional[Dict]:
        """Анализ новостей по конкретной монете"""
        try:
            # Получаем базовое название монеты
            base_symbol = symbol.replace('USDT', '').replace('BTC', '').replace('ETH', '')
            
            # Формируем запрос
            query = f"{base_symbol} cryptocurrency"
            
            result = await self._make_request(query, "news")
            
            if result and "error" not in result:
                return {
                    "symbol": symbol,
                    "news_analysis": result,
                    "timestamp": datetime.now().isoformat(),
                    "source": "perplexity_news"
                }
            else:
                print(f"❌ Ошибка анализа новостей для {symbol}: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка анализа новостей для {symbol}: {e}")
            return None
    
    async def analyze_market_sentiment(self, symbol: str) -> Optional[Dict]:
        """Анализ рыночных настроений"""
        try:
            base_symbol = symbol.replace('USDT', '').replace('BTC', '').replace('ETH', '')
            query = f"{base_symbol} market sentiment social media"
            
            result = await self._make_request(query, "sentiment")
            
            if result and "error" not in result:
                return {
                    "symbol": symbol,
                    "sentiment_analysis": result,
                    "timestamp": datetime.now().isoformat(),
                    "source": "perplexity_sentiment"
                }
            else:
                print(f"❌ Ошибка анализа настроений для {symbol}: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка анализа настроений для {symbol}: {e}")
            return None
    
    async def analyze_technical_factors(self, symbol: str) -> Optional[Dict]:
        """Анализ технических факторов"""
        try:
            base_symbol = symbol.replace('USDT', '').replace('BTC', '').replace('ETH', '')
            query = f"{base_symbol} on-chain metrics DeFi TVL technical analysis"
            
            result = await self._make_request(query, "technical")
            
            if result and "error" not in result:
                return {
                    "symbol": symbol,
                    "technical_analysis": result,
                    "timestamp": datetime.now().isoformat(),
                    "source": "perplexity_technical"
                }
            else:
                print(f"❌ Ошибка технического анализа для {symbol}: {result}")
                return None
                
        except Exception as e:
            print(f"❌ Ошибка технического анализа для {symbol}: {e}")
            return None
    
    async def get_comprehensive_analysis(self, symbol: str) -> Dict:
        """Получить комплексный анализ для торгового решения"""
        try:
            print(f"🔍 Анализ {symbol} через Perplexity...")
            
            # Параллельно получаем все типы анализа
            tasks = [
                self.analyze_coin_news(symbol),
                self.analyze_market_sentiment(symbol),
                self.analyze_technical_factors(symbol)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Обрабатываем результаты
            news_analysis = results[0] if not isinstance(results[0], Exception) else None
            sentiment_analysis = results[1] if not isinstance(results[1], Exception) else None
            technical_analysis = results[2] if not isinstance(results[2], Exception) else None
            
            # Формируем общий анализ
            overall_sentiment = "neutral"
            overall_confidence = 0.5
            impact_score = 0.5
            
            if news_analysis and "news_analysis" in news_analysis:
                news_data = news_analysis["news_analysis"]
                if "sentiment" in news_data:
                    overall_sentiment = news_data["sentiment"]
                if "confidence" in news_data:
                    overall_confidence = news_data["confidence"]
                if "impact_score" in news_data:
                    impact_score = news_data["impact_score"]
            
            return {
                "symbol": symbol,
                "overall_sentiment": overall_sentiment,
                "overall_confidence": overall_confidence,
                "impact_score": impact_score,
                "news_analysis": news_analysis,
                "sentiment_analysis": sentiment_analysis,
                "technical_analysis": technical_analysis,
                "timestamp": datetime.now().isoformat(),
                "source": "perplexity_comprehensive"
            }
            
        except Exception as e:
            print(f"❌ Ошибка комплексного анализа для {symbol}: {e}")
            return {
                "symbol": symbol,
                "overall_sentiment": "neutral",
                "overall_confidence": 0.0,
                "impact_score": 0.5,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def close(self):
        """Закрыть анализатор (не нужно для OpenRouter)"""
        pass

# Глобальный экземпляр для использования в других модулях
perplexity_analyzer = PerplexityAnalyzer() 