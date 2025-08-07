#!/usr/bin/env python3
"""
AI Trading Analyzer - Система принятия торговых решений
Архитектура: 3 эксперта (OpenAI, Anthropic, Google) + судья (Claude Opus)
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from openrouter_manager import OpenRouterManager
from perplexity_analyzer import PerplexityAnalyzer
from comprehensive_data_manager import ComprehensiveDataManager

class AITradingAnalyzer:
    """AI анализатор для принятия торговых решений"""
    
    def __init__(self):
        self.openrouter = OpenRouterManager()
        self.perplexity = PerplexityAnalyzer()
        self.data_manager = ComprehensiveDataManager()
        
        # Модели экспертов
        self.expert_models = {
            "openai": "openai/gpt-4o-mini",
            "anthropic": "anthropic/claude-3.5-haiku", 
            "google": "google/gemini-2.5-flash-lite"
        }
        
        # Модель судьи
        self.judge_model = "anthropic/claude-opus-4"
        
        # Параметры торговли
        self.min_confidence = 0.7
        self.max_risk_per_trade = 5.0  # $5
        self.stop_loss_percent = 2.0
        self.take_profit_percent = 4.0
    
    def prepare_data_for_analysis(self, market_data: Dict, perplexity_data: Dict) -> Dict:
        """Подготовить данные для анализа (без повторного запуска)"""
        try:
            # Получаем символ из market_data (может быть объектом или словарем)
            if hasattr(market_data, 'symbol'):
                symbol = market_data.symbol
            elif isinstance(market_data, dict):
                symbol = market_data.get("symbol", "UNKNOWN")
            else:
                symbol = "UNKNOWN"
                
            return {
                "symbol": symbol,
                "market_data": market_data,
                "perplexity_data": perplexity_data,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Ошибка подготовки данных: {e}")
            return None
    
    def _create_expert_prompt(self, data: Dict, expert_name: str) -> str:
        """Создать промпт для эксперта"""
        symbol = data["symbol"]
        market_data = data["market_data"]
        perplexity_data = data["perplexity_data"]
        
        prompt = f"""
        Ты эксперт по торговле криптовалютами. Проанализируй данные для {symbol} и прими торговое решение.
        
        РЫНОЧНЫЕ ДАННЫЕ:
        - Текущая цена: ${getattr(market_data, 'price', 'N/A')}
        - Изменение 24ч: {getattr(market_data, 'change_24h', 'N/A')}%
        - Объем 24ч: ${getattr(market_data, 'volume_24h', 'N/A'):,.0f}
        - RSI: {getattr(market_data, 'rsi', 'N/A')}
        - MACD: {getattr(market_data, 'macd', 'N/A')}
        - Тренд: {getattr(market_data, 'trend', 'N/A')}
        
        НОВОСТНОЙ АНАЛИЗ (Perplexity):
        - Общее настроение: {perplexity_data.get('overall_sentiment', 'N/A')}
        - Уверенность: {perplexity_data.get('overall_confidence', 'N/A')}
        - Impact Score: {perplexity_data.get('impact_score', 'N/A')}
        
        ДЕТАЛИ НОВОСТЕЙ:
        {json.dumps(perplexity_data.get('news_analysis', {}), indent=2, ensure_ascii=False)}
        
        НАСТРОЕНИЯ РЫНКА:
        {json.dumps(perplexity_data.get('sentiment_analysis', {}), indent=2, ensure_ascii=False)}
        
        ТЕХНИЧЕСКИЙ АНАЛИЗ:
        {json.dumps(perplexity_data.get('technical_analysis', {}), indent=2, ensure_ascii=False)}
        
        ПАРАМЕТРЫ ТОРГОВЛИ:
        - Максимальный риск за сделку: ${self.max_risk_per_trade}
        - Стоп-лосс: {self.stop_loss_percent}%
        - Тейк-профит: {self.take_profit_percent}%
        
        Верни торговое решение в формате JSON:
        {{
            "decision": "BUY/SELL/HOLD",
            "confidence": 0.0-1.0,
            "reason": "подробное обоснование решения",
            "risk_level": "LOW/MEDIUM/HIGH",
            "order": {{
                "type": "LIMIT",
                "side": "BUY/SELL",
                "quantity": 0.0,
                "price": 0.0,
                "stop_loss": 0.0,
                "take_profit": 0.0
            }},
            "expert": "{expert_name}"
        }}
        
        Учти все факторы: технические индикаторы, новости, настроения, риски.
        """
        
        return prompt
    
    async def _get_expert_decision(self, data: Dict, expert_name: str) -> Dict:
        """Получить решение от эксперта"""
        try:
            prompt = self._create_expert_prompt(data, expert_name)
            model = self.expert_models[expert_name]
            
            # Используем silver keys для экспертов
            result = self.openrouter.request_with_silver_keys(prompt, model)
            
            if result['success']:
                content = result['response']
                
                # Пытаемся извлечь JSON
                try:
                    if '{' in content and '}' in content:
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        json_str = content[json_start:json_end]
                        decision = json.loads(json_str)
                        decision['expert'] = expert_name
                        return decision
                    else:
                        return {
                            "decision": "HOLD",
                            "confidence": 0.0,
                            "reason": f"Ошибка парсинга ответа от {expert_name}",
                            "risk_level": "HIGH",
                            "order": None,
                            "expert": expert_name
                        }
                except json.JSONDecodeError:
                    return {
                        "decision": "HOLD",
                        "confidence": 0.0,
                        "reason": f"Ошибка JSON от {expert_name}: {content[:100]}",
                        "risk_level": "HIGH",
                        "order": None,
                        "expert": expert_name
                    }
            else:
                return {
                    "decision": "HOLD",
                    "confidence": 0.0,
                    "reason": f"Ошибка API от {expert_name}: {result['response']}",
                    "risk_level": "HIGH",
                    "order": None,
                    "expert": expert_name
                }
                
        except Exception as e:
            return {
                "decision": "HOLD",
                "confidence": 0.0,
                "reason": f"Ошибка эксперта {expert_name}: {str(e)}",
                "risk_level": "HIGH",
                "order": None,
                "expert": expert_name
            }
    
    def _create_judge_prompt(self, data: Dict, expert_decisions: List[Dict]) -> str:
        """Создать промпт для судьи"""
        symbol = data["symbol"]
        
        # Создаем безопасную версию данных для JSON
        safe_data = {
            "symbol": data["symbol"],
            "timestamp": data["timestamp"],
            "perplexity_data": data["perplexity_data"]
        }
        
        # Добавляем рыночные данные безопасно
        market_data = data["market_data"]
        if hasattr(market_data, '__dict__'):
            safe_data["market_data"] = {
                "symbol": market_data.symbol,
                "price": market_data.price,
                "change_24h": market_data.change_24h,
                "volume_24h": market_data.volume_24h,
                "high_24h": market_data.high_24h,
                "low_24h": market_data.low_24h,
                "timestamp": market_data.timestamp.isoformat(),
                "source": market_data.source.value
            }
        else:
            safe_data["market_data"] = market_data
        
        prompt = f"""
        Ты главный судья торговой системы. У тебя есть данные по {symbol} и решения от 3 экспертов.
        
        ИСХОДНЫЕ ДАННЫЕ:
        {json.dumps(safe_data, indent=2, ensure_ascii=False)}
        
        РЕШЕНИЯ ЭКСПЕРТОВ:
        {json.dumps(expert_decisions, indent=2, ensure_ascii=False)}
        
        Твоя задача - проанализировать все данные и решения экспертов, затем принять ФИНАЛЬНОЕ решение.
        
        КРИТЕРИИ ОЦЕНКИ:
        1. Качество обоснования каждого эксперта
        2. Соответствие решения рыночным данным
        3. Учет новостных факторов
        4. Управление рисками
        5. Консистентность между экспертами
        
        Верни ФИНАЛЬНОЕ решение в формате JSON:
        {{
            "final_decision": "BUY/SELL/HOLD",
            "confidence": 0.0-1.0,
            "reason": "подробное обоснование финального решения",
            "expert_analysis": {{
                "best_expert": "имя лучшего эксперта",
                "expert_agreement": "согласны ли эксперты",
                "risk_assessment": "оценка рисков"
            }},
            "order": {{
                "type": "LIMIT",
                "side": "BUY/SELL",
                "quantity": 0.0,
                "price": 0.0,
                "stop_loss": 0.0,
                "take_profit": 0.0
            }},
            "judge": "Claude Opus 4"
        }}
        
        Будь осторожен и принимай решение только при высокой уверенности.
        """
        
        return prompt
    
    async def _get_judge_decision(self, data: Dict, expert_decisions: List[Dict]) -> Dict:
        """Получить финальное решение от судьи"""
        try:
            prompt = self._create_judge_prompt(data, expert_decisions)
            
            # Используем golden key для судьи
            result = self.openrouter.request_with_golden_key(prompt, self.judge_model)
            
            if result['success']:
                content = result['response']
                
                try:
                    if '{' in content and '}' in content:
                        json_start = content.find('{')
                        json_end = content.rfind('}') + 1
                        json_str = content[json_start:json_end]
                        decision = json.loads(json_str)
                        decision['judge'] = "Claude Opus 4"
                        return decision
                    else:
                        return {
                            "final_decision": "HOLD",
                            "confidence": 0.0,
                            "reason": "Ошибка парсинга ответа судьи",
                            "expert_analysis": {},
                            "order": None,
                            "judge": "Claude Opus 4"
                        }
                except json.JSONDecodeError:
                    return {
                        "final_decision": "HOLD",
                        "confidence": 0.0,
                        "reason": f"Ошибка JSON судьи: {content[:100]}",
                        "expert_analysis": {},
                        "order": None,
                        "judge": "Claude Opus 4"
                    }
            else:
                return {
                    "final_decision": "HOLD",
                    "confidence": 0.0,
                    "reason": f"Ошибка API судьи: {result['response']}",
                    "expert_analysis": {},
                    "order": None,
                    "judge": "Claude Opus 4"
                }
                
        except Exception as e:
            return {
                "final_decision": "HOLD",
                "confidence": 0.0,
                "reason": f"Ошибка судьи: {str(e)}",
                "expert_analysis": {},
                "order": None,
                "judge": "Claude Opus 4"
            }
    
    async def analyze_and_decide(self, market_data: Dict, perplexity_data: Dict) -> Dict:
        """Основной метод анализа и принятия решения"""
        try:
            # Получаем символ из market_data (может быть объектом или словарем)
            if hasattr(market_data, 'symbol'):
                symbol = market_data.symbol
            elif isinstance(market_data, dict):
                symbol = market_data.get("symbol", "UNKNOWN")
            else:
                symbol = "UNKNOWN"
            print(f"🤖 Анализ {symbol} - подготовка данных...")
            
            # 1. Подготавливаем данные (без повторного запуска)
            data = self.prepare_data_for_analysis(market_data, perplexity_data)
            if not data:
                return {
                    "symbol": symbol,
                    "final_decision": "HOLD",
                    "confidence": 0.0,
                    "reason": "Не удалось подготовить данные",
                    "timestamp": datetime.now().isoformat()
                }
            
            print(f"📊 Данные получены, запрашиваем экспертов...")
            
            # 2. Получаем решения от 3 экспертов
            expert_tasks = [
                self._get_expert_decision(data, "openai"),
                self._get_expert_decision(data, "anthropic"),
                self._get_expert_decision(data, "google")
            ]
            
            expert_decisions = await asyncio.gather(*expert_tasks)
            
            print(f"👨‍💼 Решения экспертов получены:")
            for decision in expert_decisions:
                print(f"   {decision['expert']}: {decision['decision']} (уверенность: {decision['confidence']:.2f})")
            
            # 3. Получаем финальное решение от судьи
            print(f"⚖️ Запрашиваем финальное решение судьи...")
            final_decision = await self._get_judge_decision(data, expert_decisions)
            
            # 4. Формируем итоговый результат с полными данными
            # Конвертируем MarketData в словарь для JSON сериализации
            market_data_dict = {}
            if hasattr(data["market_data"], '__dict__'):
                market_data_dict = data["market_data"].__dict__.copy()
                # Убираем datetime объекты которые нельзя сериализовать
                if 'timestamp' in market_data_dict:
                    market_data_dict['timestamp'] = market_data_dict['timestamp'].isoformat()
                if 'source' in market_data_dict:
                    market_data_dict['source'] = market_data_dict['source'].value
            else:
                market_data_dict = data["market_data"]
                
            result = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "input_data": {
                    "market_data": market_data_dict,
                    "perplexity_data": data["perplexity_data"]
                },
                "expert_analysis": {
                    "prompts": {
                        "openai": self._create_expert_prompt(data, "openai"),
                        "anthropic": self._create_expert_prompt(data, "anthropic"),
                        "google": self._create_expert_prompt(data, "google")
                    },
                    "responses": expert_decisions
                },
                "judge_analysis": {
                    "prompt": self._create_judge_prompt(data, expert_decisions),
                    "response": final_decision
                },
                "final_result": {
                    "decision": final_decision.get("final_decision"),
                    "confidence": final_decision.get("confidence", 0),
                    "should_trade": final_decision.get("confidence", 0) >= self.min_confidence
                }
            }
            
            print(f"✅ Финальное решение: {final_decision.get('final_decision')} (уверенность: {final_decision.get('confidence', 0):.2f})")
            
            return result
            
        except Exception as e:
            # Получаем символ для ошибки
            error_symbol = "UNKNOWN"
            if hasattr(market_data, 'symbol'):
                error_symbol = market_data.symbol
            elif isinstance(market_data, dict):
                error_symbol = market_data.get("symbol", "UNKNOWN")
            
            print(f"❌ Ошибка анализа {error_symbol}: {e}")
            return {
                "symbol": error_symbol,
                "final_decision": "HOLD",
                "confidence": 0.0,
                "reason": f"Ошибка анализа: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

# Глобальный экземпляр для использования в других модулях
ai_trading_analyzer = AITradingAnalyzer()
