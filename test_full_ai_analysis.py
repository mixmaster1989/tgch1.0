#!/usr/bin/env python3
"""
Полный тест AI анализа - получение данных и принятие решений
"""

import asyncio
from datetime import datetime
from comprehensive_data_manager import comprehensive_data_manager, MarketData, DataSource
from perplexity_analyzer import PerplexityAnalyzer
from ai_trading_analyzer import AITradingAnalyzer
import json

def safe_json_dumps(obj, indent=3, ensure_ascii=False):
    """Безопасная сериализация в JSON с обработкой несериализуемых объектов"""
    try:
        return json.dumps(obj, indent=indent, ensure_ascii=ensure_ascii)
    except TypeError:
        # Если объект не сериализуется, конвертируем его в строку
        if hasattr(obj, '__dict__'):
            return json.dumps(obj.__dict__, indent=indent, ensure_ascii=ensure_ascii)
        else:
            return json.dumps(str(obj), indent=indent, ensure_ascii=ensure_ascii)

async def test_full_ai_analysis():
    """Полный тест AI анализа"""
    print("🚀 Запуск полного AI анализа (с реальными данными)...")
    
    try:
        # Запускаем менеджер данных
        print("📊 Получение данных для ETHUSDT...")
        await comprehensive_data_manager.start()
        await comprehensive_data_manager.subscribe_multiple_symbols(["ETHUSDT"])
        
        # Ждем загрузки данных
        await asyncio.sleep(3)
        
        # Получаем рыночные данные
        print("   🔄 Получение рыночных данных (один раз)...")
        market_data = comprehensive_data_manager.get_market_data("ETHUSDT")
        if market_data:
            print(f"   ✅ Рыночные данные получены: ${market_data.price}")
        
        # Получаем данные от Perplexity (реальные)
        print("🔍 Анализ ETHUSDT через Perplexity...")
        perplexity = PerplexityAnalyzer()
        perplexity_data = await perplexity.get_comprehensive_analysis("ETHUSDT")
        
        # Получаем технические индикаторы
        print("📈 Получение технических индикаторов...")
        indicators = comprehensive_data_manager.get_technical_indicators("ETHUSDT", "1m")
        if indicators:
            print(f"   ✅ Технические индикаторы получены:")
            print(f"      RSI: {indicators.rsi_14:.2f}")
            print(f"      SMA: {indicators.sma_20:.2f}")
            print(f"      MACD: {indicators.macd}")
        else:
            print("   ❌ Технические индикаторы не получены")
        
        # Получаем orderbook
        orderbook = await comprehensive_data_manager.get_orderbook_data("ETHUSDT")
        
        # Получаем корреляции
        correlations = comprehensive_data_manager.get_correlation_data("ETHUSDT")
        
        # ИСПОЛЬЗУЕМ РЕАЛЬНЫЙ AI АНАЛИЗАТОР
        print("🤖 Анализ ETHUSDT - подготовка данных...")
        ai_analyzer = AITradingAnalyzer()
        
        # Подготавливаем данные для анализа
        analysis_data = ai_analyzer.prepare_data_for_analysis(market_data, perplexity_data)
        
        print("📊 Данные получены, запрашиваем экспертов...")
        # Получаем реальное торговое решение
        trading_decision = await ai_analyzer.analyze_and_decide(market_data, perplexity_data)
        
        print("👨‍💼 Решения экспертов получены:")
        expert_responses = trading_decision.get('expert_analysis', {}).get('responses', [])
        for response in expert_responses:
            if isinstance(response, dict):
                expert_name = response.get('expert', 'UNKNOWN')
                decision = response.get('decision', 'UNKNOWN')
                confidence = response.get('confidence', 0.0)
                print(f"   {expert_name}: {decision} (уверенность: {confidence:.2f})")
            else:
                print(f"   Неизвестный формат ответа: {response}")
        
        print("⚖️ Запрашиваем финальное решение судьи...")
        final_decision = trading_decision.get('final_decision', {})
        
        print(f"✅ Финальное решение: {final_decision.get('final_decision', 'UNKNOWN')} (уверенность: {final_decision.get('confidence', 0.0):.2f})")
        
        # Записываем результаты в файл
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"full_ai_analysis_ETHUSDT_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=== ПОЛНЫЙ AI АНАЛИЗ ETHUSDT ===\n")
            f.write(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("Тип теста: full_ai_analysis_with_real_data\n\n")
            
            # Рыночные данные
            f.write("📊 РЫНОЧНЫЕ ДАННЫЕ:\n")
            f.write(f"   Символ: {market_data.symbol}\n")
            f.write(f"   Цена: ${market_data.price}\n")
            f.write(f"   Изменение 24ч: {market_data.change_24h}%\n")
            f.write(f"   Объем 24ч: ${market_data.volume_24h:,.0f}\n")
            f.write(f"   Максимум 24ч: ${market_data.high_24h}\n")
            f.write(f"   Минимум 24ч: ${market_data.low_24h}\n")
            f.write(f"   Время: {market_data.timestamp}\n\n")
            
            # Технические индикаторы
            f.write("📈 ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ:\n")
            if indicators:
                f.write(f"   ✅ RSI (14): {indicators.rsi_14:.2f}\n")
                f.write(f"   ✅ SMA (20): {indicators.sma_20:.2f}\n")
                f.write(f"   ✅ EMA (12): {indicators.ema_12:.2f}\n")
                f.write(f"   ✅ MACD: {indicators.macd}\n")
                f.write(f"   ✅ Bollinger: {indicators.bollinger}\n")
                f.write(f"   ✅ ATR (14): {indicators.atr_14:.2f}\n")
                f.write(f"   ✅ Volume SMA: {indicators.volume_sma:.2f}\n")
            else:
                f.write("   ❌ Индикаторы недоступны\n")
            f.write("\n")
            
            # Orderbook
            f.write("📚 ORDERBOOK ДАННЫЕ:\n")
            if orderbook:
                f.write(f"   Спред: ${orderbook.spread:.6f}\n")
                f.write(f"   Спред %: {orderbook.spread_percent:.4f}%\n")
                f.write(f"   Объем bids: ${orderbook.bid_volume:.2f}\n")
                f.write(f"   Объем asks: ${orderbook.ask_volume:.2f}\n")
                f.write(f"   Соотношение объемов: {orderbook.volume_ratio:.2f}\n")
                f.write(f"   Ликвидность: {orderbook.liquidity_score:.2f}\n")
            else:
                f.write("   ❌ Orderbook недоступен\n")
            f.write("\n")
            
            # Корреляции
            f.write("🔗 КОРРЕЛЯЦИИ:\n")
            f.write(f"   {safe_json_dumps(correlations)}\n\n")
            
            # Perplexity анализ
            f.write("🔍 АНАЛИЗ PERPLEXITY:\n")
            f.write(f"   Настроения: {perplexity_data.get('overall_sentiment', 'N/A')}\n")
            f.write(f"   Уверенность: {perplexity_data.get('overall_confidence', 'N/A')}\n")
            f.write(f"   Impact Score: {perplexity_data.get('impact_score', 'N/A')}\n\n")
            
            # ПОЛНЫЕ ДАННЫЕ PERPLEXITY (если есть)
            if perplexity_data:
                f.write("📄 ПОЛНЫЕ ДАННЫЕ PERPLEXITY:\n")
                f.write(f"   {safe_json_dumps(perplexity_data)}\n\n")
            
            # Торговое решение
            f.write("🤖 ТОРГОВОЕ РЕШЕНИЕ:\n")
            f.write(f"   Решение: {final_decision.get('final_decision', 'UNKNOWN')}\n")
            f.write(f"   Уверенность: {final_decision.get('confidence', 0.0):.2f}\n")
            f.write(f"   Торговать: {final_decision.get('confidence', 0.0) > 0.7}\n\n")
            
            # ПРОМПТЫ И ОТВЕТЫ AI ЭКСПЕРТОВ (если есть)
            expert_analysis = trading_decision.get('expert_analysis', {})
            if expert_analysis:
                f.write("🤖 ПРОМПТЫ И ОТВЕТЫ AI ЭКСПЕРТОВ:\n")
                
                # Промпты экспертов
                expert_prompts = expert_analysis.get('prompts', {})
                if expert_prompts:
                    f.write("📝 ПРОМПТЫ ЭКСПЕРТОВ:\n")
                    for expert_name, prompt in expert_prompts.items():
                        f.write(f"   🔍 {expert_name.upper()}:\n")
                        f.write(f"   {prompt}\n\n")
                
                # Ответы экспертов
                expert_responses = expert_analysis.get('responses', [])
                if expert_responses:
                    f.write("📥 ОТВЕТЫ ЭКСПЕРТОВ:\n")
                    for response in expert_responses:
                        if isinstance(response, dict):
                            expert_name = response.get('expert', 'UNKNOWN')
                            f.write(f"   🔍 {expert_name.upper()}:\n")
                            f.write(f"   {safe_json_dumps(response)}\n\n")
                        else:
                            f.write(f"   Неизвестный формат ответа: {response}\n\n")
                
                # Промпт и ответ судьи
                judge_analysis = trading_decision.get('judge_analysis', {})
                if judge_analysis:
                    f.write("⚖️ ПРОМПТ И ОТВЕТ СУДЬИ:\n")
                    
                    judge_prompt = judge_analysis.get('prompt', 'N/A')
                    f.write("📝 ПРОМПТ СУДЬИ:\n")
                    f.write(f"   {judge_prompt}\n\n")
                    
                    judge_response = judge_analysis.get('response', {})
                    f.write("📥 ОТВЕТ СУДЬИ:\n")
                    f.write(f"   {safe_json_dumps(judge_response)}\n\n")
            
            # Краткие решения экспертов
            f.write("👨‍💼 КРАТКИЕ РЕШЕНИЯ ЭКСПЕРТОВ:\n")
            expert_responses = trading_decision.get('expert_analysis', {}).get('responses', [])
            for response in expert_responses:
                if isinstance(response, dict):
                    expert_name = response.get('expert', 'UNKNOWN')
                    decision = response.get('decision', 'UNKNOWN')
                    confidence = response.get('confidence', 0.0)
                    f.write(f"   {expert_name}: {decision} (уверенность: {confidence:.2f})\n")
                else:
                    f.write(f"   Неизвестный формат ответа: {response}\n")
            
            f.write("\n✅ АНАЛИЗ ЗАВЕРШЕН\n")
        
        print(f"💾 Запись в файл: {filename}")
        
        # Останавливаем менеджер
        await comprehensive_data_manager.stop()
        
        print("\n✅ Анализ завершен!")
        print(f"   Файл: {filename}")
        print(f"   Финальное решение: {final_decision.get('final_decision', 'UNKNOWN')}")
        print(f"   Уверенность: {final_decision.get('confidence', 0.0):.2f}")
        print(f"   Торговать: {final_decision.get('confidence', 0.0) > 0.7}")
        
    except Exception as e:
        print(f"❌ Ошибка в полном AI анализе: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_ai_analysis())
