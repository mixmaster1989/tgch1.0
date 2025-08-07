#!/usr/bin/env python3
"""
Полный тест AI анализа - получение данных и принятие решений
"""

import asyncio
from datetime import datetime
from comprehensive_data_manager import comprehensive_data_manager, MarketData, DataSource
from perplexity_analyzer import PerplexityAnalyzer
from ai_trading_analyzer import AITradingAnalyzer

# ЗАГЛУШКИ ДЛЯ ТЕСТИРОВАНИЯ (без обращения к нейросетям)
class MockPerplexityAnalyzer:
    """Заглушка для Perplexity анализатора"""
    async def get_comprehensive_analysis(self, symbol: str) -> dict:
        print(f"   🔄 [ЗАГЛУШКА] Данные от Perplexity для {symbol}...")
        await asyncio.sleep(0.1)  # Имитируем задержку
        return {
            "symbol": symbol,
            "overall_sentiment": "positive",
            "overall_confidence": 0.8,
            "impact_score": 0.7,
            "news_analysis": {
                "sentiment": "positive",
                "impact_score": 0.7,
                "key_events": [
                    {
                        "title": "Тестовая новость",
                        "impact": "medium",
                        "sentiment": "positive",
                        "summary": "Тестовое событие для проверки"
                    }
                ],
                "market_outlook": "Тестовый прогноз",
                "confidence": 0.8
            },
            "sentiment_analysis": {
                "social_sentiment": "positive",
                "analyst_sentiment": "positive",
                "correlation_analysis": "Тестовая корреляция",
                "confidence": 0.8,
                "summary": "Тестовый анализ настроений"
            },
            "technical_analysis": {
                "technical_score": 0.75,
                "on_chain_metrics": {
                    "active_addresses": "up",
                    "large_transactions": "10",
                    "network_health": "good"
                },
                "defi_metrics": {
                    "tvl_trend": "up",
                    "volume_trend": "up"
                },
                "analysis": "Тестовый технический анализ"
            },
            "timestamp": datetime.now().isoformat(),
            "source": "mock_perplexity"
        }

class MockAITradingAnalyzer:
    """Заглушка для AI торгового анализатора"""
    async def analyze_and_decide(self, market_data, perplexity_data: dict) -> dict:
        # Получаем символ из market_data (может быть объектом или словарем)
        symbol = "UNKNOWN"
        if hasattr(market_data, 'symbol'):
            symbol = market_data.symbol
        elif isinstance(market_data, dict):
            symbol = market_data.get('symbol', 'UNKNOWN')
        
        print(f"   🔄 [ЗАГЛУШКА] Торговое решение для {symbol}...")
        await asyncio.sleep(0.1)  # Имитируем задержку
        
        return {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "input_data": {
                "market_data": market_data,
                "perplexity_data": perplexity_data
            },
            "expert_analysis": {
                "prompts": {
                    "openai": "[ЗАГЛУШКА] Промпт OpenAI",
                    "anthropic": "[ЗАГЛУШКА] Промпт Anthropic", 
                    "google": "[ЗАГЛУШКА] Промпт Google"
                },
                "responses": [
                    {
                        "expert": "OpenAI GPT-4o-mini",
                        "decision": "BUY",
                        "confidence": 0.85,
                        "reason": "Тестовое решение OpenAI"
                    },
                    {
                        "expert": "Anthropic Claude 3.5 Haiku",
                        "decision": "BUY", 
                        "confidence": 0.82,
                        "reason": "Тестовое решение Anthropic"
                    },
                    {
                        "expert": "Google Gemini 2.5 Flash Lite",
                        "decision": "HOLD",
                        "confidence": 0.78,
                        "reason": "Тестовое решение Google"
                    }
                ]
            },
            "judge_analysis": {
                "prompt": "[ЗАГЛУШКА] Промпт судьи",
                "response": {
                    "final_decision": "BUY",
                    "confidence": 0.83,
                    "reason": "Тестовое финальное решение судьи"
                }
            },
            "final_result": {
                "decision": "BUY",
                "confidence": 0.83,
                "should_trade": True
            }
        }

# Создаем экземпляры заглушек
perplexity_analyzer = MockPerplexityAnalyzer()
ai_trading_analyzer = MockAITradingAnalyzer()

async def test_full_ai_analysis():
    """Полный тест AI анализа"""
    print("🚀 Запуск полного AI анализа (с заглушками)...")
    
    try:
        symbol = "ETHUSDT"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"full_ai_analysis_{symbol}_{timestamp}.txt"
        
        print(f"📊 Получение данных для {symbol}...")
        
        # 1. ОДИН запрос данных через comprehensive_data_manager
        print("   🔄 Получение рыночных данных (один раз)...")
        
        # Получаем рыночные данные ОДИН РАЗ через исправленный метод
        market_data = comprehensive_data_manager.get_market_data(symbol)
        if market_data:
            print(f"   ✅ Рыночные данные получены: ${market_data.price}")
        else:
            print(f"   ❌ Не удалось получить рыночные данные для {symbol}")
            market_data = None
        
        # 2. Инициализируем анализаторы
        perplexity_analyzer = PerplexityAnalyzer()
        ai_trading_analyzer = AITradingAnalyzer()
        
        # 3. Запускаем perplexity_analyzer и получаем новостные данные
        print("   🔄 Данные от Perplexity...")
        perplexity_data = await perplexity_analyzer.get_comprehensive_analysis(symbol)
        
        # 4. Получаем торговое решение через ai_trading_analyzer
        print("   🔄 Торговое решение...")
        trading_result = await ai_trading_analyzer.analyze_and_decide(market_data, perplexity_data)
        
        # 5. Записываем результат в текстовый файл
        print(f"💾 Запись в файл: {filename}")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"=== ПОЛНЫЙ AI АНАЛИЗ {symbol} ===\n")
            f.write(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Тип теста: full_ai_analysis_with_mocks\n\n")
            
            # Рыночные данные
            f.write("📊 РЫНОЧНЫЕ ДАННЫЕ:\n")
            if market_data:
                f.write(f"   Символ: {getattr(market_data, 'symbol', 'N/A')}\n")
                f.write(f"   Цена: ${getattr(market_data, 'price', 0):.2f}\n")
                f.write(f"   Изменение 24ч: {getattr(market_data, 'change_24h', 0):.2f}%\n")
                f.write(f"   Объем 24ч: ${getattr(market_data, 'volume_24h', 0):,.0f}\n")
                f.write(f"   Максимум 24ч: ${getattr(market_data, 'high_24h', 0):.2f}\n")
                f.write(f"   Минимум 24ч: ${getattr(market_data, 'low_24h', 0):.2f}\n")
                f.write(f"   Время: {getattr(market_data, 'timestamp', 'N/A')}\n")
            else:
                f.write("   ❌ Данные недоступны\n")
            f.write("\n")
            
            # Технические индикаторы
            f.write("📈 ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ:\n")
            indicators = comprehensive_data_manager.get_technical_indicators(symbol, '1m')
            if indicators:
                f.write(f"   RSI (14): {indicators.rsi_14:.2f}\n")
                f.write(f"   SMA (20): ${indicators.sma_20:.2f}\n")
                f.write(f"   EMA (12): ${indicators.ema_12:.2f}\n")
                f.write(f"   MACD: {indicators.macd}\n")
                f.write(f"   Bollinger: {indicators.bollinger}\n")
                f.write(f"   ATR (14): {indicators.atr_14:.6f}\n")
                f.write(f"   Volume SMA: {indicators.volume_sma:.2f}\n")
            else:
                f.write("   ❌ Индикаторы недоступны\n")
            f.write("\n")
            
            # Orderbook данные
            f.write("📚 ORDERBOOK ДАННЫЕ:\n")
            try:
                orderbook = await comprehensive_data_manager.get_orderbook_data(symbol)
                if orderbook:
                    f.write(f"   Объект orderbook: {type(orderbook)}\n")
                    f.write(f"   Атрибуты: {dir(orderbook)}\n")
                    if hasattr(orderbook, '__dict__'):
                        f.write(f"   Содержимое: {orderbook.__dict__}\n")
                    
                    if hasattr(orderbook, 'spread'):
                        f.write(f"   Спред: ${orderbook.spread:.6f}\n")
                        f.write(f"   Спред %: {orderbook.spread_percent:.4f}%\n")
                        f.write(f"   Объем bids: ${orderbook.bid_volume:.2f}\n")
                        f.write(f"   Объем asks: ${orderbook.ask_volume:.2f}\n")
                        f.write(f"   Соотношение объемов: {orderbook.volume_ratio:.2f}\n")
                        f.write(f"   Ликвидность: {orderbook.liquidity_score:.2f}\n")
                    else:
                        f.write("   ❌ Атрибут 'spread' отсутствует\n")
                        print(f"⚠️ Orderbook для {symbol}: объект не содержит атрибут 'spread'")
                        print(f"   Доступные атрибуты: {[attr for attr in dir(orderbook) if not attr.startswith('_')]}")
                else:
                    f.write("   ❌ Orderbook объект None\n")
                    print(f"⚠️ Orderbook для {symbol}: объект None")
            except Exception as e:
                f.write(f"   ❌ Ошибка получения orderbook: {e}\n")
                print(f"❌ Ошибка получения orderbook для {symbol}: {e}")
            f.write("\n")
            
            # Корреляции
            f.write("🔗 КОРРЕЛЯЦИИ:\n")
            try:
                correlations = comprehensive_data_manager.get_correlation_data(symbol)
                if correlations:
                    for asset, corr in correlations.items():
                        # Проверяем тип корреляции
                        if isinstance(corr, (int, float)):
                            f.write(f"   {asset}: {corr:.4f}\n")
                        else:
                            f.write(f"   {asset}: {corr}\n")
                else:
                    f.write("   ❌ Корреляции недоступны\n")
                    print(f"⚠️ Корреляции для {symbol}: данные недоступны")
            except Exception as e:
                f.write(f"   ❌ Ошибка получения корреляций: {e}\n")
                print(f"❌ Ошибка получения корреляций для {symbol}: {e}")
            f.write("\n")
            
            # Perplexity данные
            f.write("🔍 АНАЛИЗ PERPLEXITY:\n")
            f.write(f"   Настроения: {perplexity_data.get('overall_sentiment', 'N/A')}\n")
            f.write(f"   Уверенность: {perplexity_data.get('overall_confidence', 0):.2f}\n")
            f.write(f"   Impact Score: {perplexity_data.get('impact_score', 0):.2f}\n")
            f.write("\n")
            
            # ПРОМПТЫ К НЕЙРОСЕТЯМ
            f.write("🤖 ПРОМПТЫ К НЕЙРОСЕТЯМ:\n\n")
            
            # Промпт для Perplexity
            f.write("📰 ПРОМПТ ДЛЯ PERPLEXITY:\n")
            perplexity_prompt = f"""
Проанализируй последние новости и события для {symbol} за последние 24 часа.
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
            f.write(perplexity_prompt)
            f.write("\n\n")
            
            # Промпты для торговых экспертов
            f.write("👨‍💼 ПРОМПТЫ ДЛЯ ТОРГОВЫХ ЭКСПЕРТОВ:\n")
            expert_prompt = f"""
Ты эксперт по торговле криптовалютами. Проанализируй данные для {symbol} и прими торговое решение.

РЫНОЧНЫЕ ДАННЫЕ:
- Текущая цена: ${getattr(market_data, 'price', 0):.2f}
- Изменение 24ч: {getattr(market_data, 'change_24h', 0):.2f}%
- Объем 24ч: ${getattr(market_data, 'volume_24h', 0):,.0f}
- RSI: {indicators.rsi_14 if indicators else 'N/A'}
- MACD: {indicators.macd if indicators else 'N/A'}
- Спред: ${orderbook.spread if orderbook and hasattr(orderbook, 'spread') else 0:.6f}

НОВОСТНОЙ АНАЛИЗ (Perplexity):
- Общее настроение: {perplexity_data.get('overall_sentiment', 'N/A')}
- Уверенность: {perplexity_data.get('overall_confidence', 0):.2f}
- Impact Score: {perplexity_data.get('impact_score', 0):.2f}

Верни торговое решение в формате JSON:
{{
    "decision": "BUY/SELL/HOLD",
    "confidence": 0.0-1.0,
    "reason": "подробное обоснование решения",
    "risk_level": "LOW/MEDIUM/HIGH"
}}
"""
            f.write(expert_prompt)
            f.write("\n\n")
            
            # Промпт для судьи
            f.write("⚖️ ПРОМПТ ДЛЯ СУДЬИ (Claude Opus):\n")
            judge_prompt = f"""
Ты судья в системе принятия торговых решений. Проанализируй решения 3 экспертов для {symbol} и прими финальное решение.

РЕШЕНИЯ ЭКСПЕРТОВ:
1. OpenAI GPT-4o-mini: BUY (уверенность: 0.85)
2. Anthropic Claude 3.5 Haiku: BUY (уверенность: 0.82)  
3. Google Gemini 2.5 Flash Lite: HOLD (уверенность: 0.78)

РЫНОЧНЫЕ ДАННЫЕ:
- Цена: ${getattr(market_data, 'price', 0):.2f}
- RSI: {indicators.rsi_14 if indicators else 'N/A'}
- Настроения: {perplexity_data.get('overall_sentiment', 'N/A')}

Прими финальное решение в формате JSON:
{{
    "final_decision": "BUY/SELL/HOLD",
    "confidence": 0.0-1.0,
    "reason": "обоснование финального решения"
}}
"""
            f.write(judge_prompt)
            f.write("\n\n")
            
            # Торговое решение
            f.write("🤖 ТОРГОВОЕ РЕШЕНИЕ:\n")
            if trading_result and isinstance(trading_result, dict):
                final_result = trading_result.get('final_result', {})
                if isinstance(final_result, dict):
                    f.write(f"   Решение: {final_result.get('decision', 'N/A')}\n")
                    f.write(f"   Уверенность: {final_result.get('confidence', 0):.2f}\n")
                    f.write(f"   Торговать: {final_result.get('should_trade', False)}\n")
                else:
                    f.write(f"   Решение: {final_result}\n")
            else:
                f.write("   ❌ Ошибка в торговом результате\n")
            f.write("\n")
            
            # Эксперты
            f.write("👨‍💼 РЕШЕНИЯ ЭКСПЕРТОВ:\n")
            if trading_result and isinstance(trading_result, dict):
                expert_responses = trading_result.get('expert_analysis', {}).get('responses', [])
                for expert in expert_responses:
                    f.write(f"   {expert.get('expert', 'N/A')}: {expert.get('decision', 'N/A')} (уверенность: {expert.get('confidence', 0):.2f})\n")
            f.write("\n")
            
            f.write("✅ АНАЛИЗ ЗАВЕРШЕН\n")
        
        # 6. Краткий вывод результата
        print(f"\n✅ Анализ завершен!")
        print(f"   Файл: {filename}")
        
        # Проверяем результат
        if trading_result and isinstance(trading_result, dict):
            final_result = trading_result.get('final_result', {})
            if isinstance(final_result, dict):
                print(f"   Финальное решение: {final_result.get('decision', 'N/A')}")
                print(f"   Уверенность: {final_result.get('confidence', 0):.2f}")
                print(f"   Торговать: {final_result.get('should_trade', False)}")
            else:
                print(f"   Финальное решение: {final_result}")
        else:
            print(f"   Ошибка в торговом результате")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_full_ai_analysis())
