import json
import pandas as pd
from typing import Dict, List
from openrouter_manager import OpenRouterManager

class NeuralAnalyzer:
    def __init__(self):
        self.openrouter = OpenRouterManager()
    
    def analyze_market_data(self, symbol: str, current_price: float, market_data: Dict, klines_data: List = None) -> Dict:
        """Анализ рыночных данных с помощью ИИ"""
        try:
            # Если есть данные свечей, используем их
            if klines_data and len(klines_data) > 0:
                # Проверяем количество колонок
                if len(klines_data[0]) >= 6:
                    # Стандартный формат Binance
                    columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
                    if len(klines_data[0]) > 6:
                        columns.extend(['close_time', 'quote_volume', 'count', 'taker_buy_volume', 'taker_buy_quote_volume', 'ignore'][:len(klines_data[0])-6])
                    df = pd.DataFrame(klines_data, columns=columns[:len(klines_data[0])])
                else:
                    # Минимальный формат
                    df = pd.DataFrame(klines_data, columns=['timestamp', 'open', 'high', 'low', 'close'][:len(klines_data[0])])
                
                # Конвертируем в числовые значения
                for col in ['open', 'high', 'low', 'close']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col])
                if 'volume' in df.columns:
                    df['volume'] = pd.to_numeric(df['volume'])
                
                recent_data = df.tail(min(20, len(df)))
                if len(recent_data) > 1:
                    price_change = ((current_price - float(recent_data['close'].iloc[0])) / float(recent_data['close'].iloc[0])) * 100
                else:
                    price_change = 0
                max_price = recent_data['high'].max()
                min_price = recent_data['low'].min()
                avg_volume = recent_data['volume'].mean() if 'volume' in recent_data.columns else market_data.get('volume_24h', 0)
            else:
                # Используем данные из market_data
                price_change = market_data.get('price_change_24h', 0)
                max_price = current_price * 1.05
                min_price = current_price * 0.95
                avg_volume = market_data.get('volume_24h', 0)
            
            prompt = f"""
            Проанализируй данные торговой пары {symbol}:
            
            Текущая цена: {current_price}
            Изменение за период: {price_change:.2f}%
            Максимум за период: {max_price}
            Минимум за период: {min_price}
            Средний объем: {avg_volume:.2f}
            RSI: {market_data.get('rsi', 50)}
            Тренд: {market_data.get('trend', 'UNKNOWN')}
            Объем выше среднего: {market_data.get('volume_ratio', 1):.2f}x
            
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