import json
import pandas as pd
from typing import Dict, List
from openrouter_manager import OpenRouterManager

class NeuralAnalyzer:
    def __init__(self):
        self.openrouter = OpenRouterManager()
    
    def analyze_market_data(self, klines_data: List, symbol: str) -> Dict:
        """Анализ рыночных данных с помощью ИИ"""
        # Преобразуем данные свечей в удобный формат
        df = pd.DataFrame(klines_data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'count', 'taker_buy_volume',
            'taker_buy_quote_volume', 'ignore'
        ])
        
        # Конвертируем в числовые значения
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
        
        # Создаем промпт для анализа
        recent_data = df.tail(20)
        current_price = float(recent_data['close'].iloc[-1])
        price_change = ((current_price - float(recent_data['close'].iloc[0])) / float(recent_data['close'].iloc[0])) * 100
        
        prompt = f"""
        Проанализируй данные торговой пары {symbol}:
        
        Текущая цена: {current_price}
        Изменение за период: {price_change:.2f}%
        Максимум за период: {recent_data['high'].max()}
        Минимум за период: {recent_data['low'].min()}
        Средний объем: {recent_data['volume'].mean():.2f}
        
        Последние 5 свечей (OHLC):
        {recent_data[['open', 'high', 'low', 'close']].tail().to_string()}
        
        Дай краткий анализ и рекомендацию: BUY, SELL или HOLD.
        Укажи уровни поддержки и сопротивления.
        Ответ должен быть в формате JSON:
        {{
            "recommendation": "BUY/SELL/HOLD",
            "confidence": 0.8,
            "support_level": 0.0,
            "resistance_level": 0.0,
            "analysis": "краткий анализ"
        }}
        """
        
        try:
            # Используем golden key для торговых решений
            result = self.openrouter.request_with_golden_key(prompt)
            
            if not result['success']:
                return {
                    "recommendation": "HOLD",
                    "confidence": 0.0,
                    "support_level": current_price * 0.98,
                    "resistance_level": current_price * 1.02,
                    "analysis": f"Ошибка API: {result['response']}"
                }
            
            response = result['response']
            # Попытка извлечь JSON из ответа
            if '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                return {
                    "recommendation": "HOLD",
                    "confidence": 0.5,
                    "support_level": current_price * 0.98,
                    "resistance_level": current_price * 1.02,
                    "analysis": response
                }
        except Exception as e:
            return {
                "recommendation": "HOLD",
                "confidence": 0.0,
                "support_level": current_price * 0.98,
                "resistance_level": current_price * 1.02,
                "analysis": f"Ошибка анализа: {str(e)}"
            }
    
    def analyze_portfolio(self, balances: List[Dict]) -> str:
        """Анализ портфеля (используем silver key)"""
        prompt = f"""
        Проанализируй текущий портфель:
        {json.dumps(balances, indent=2)}
        
        Дай рекомендации по диверсификации и управлению рисками.
        """
        
        result = self.openrouter.request_with_silver_keys(prompt)
        return result['response'] if result['success'] else f"Ошибка: {result['response']}"