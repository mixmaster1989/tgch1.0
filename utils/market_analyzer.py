import requests
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from mex_api import MexAPI
from neural_analyzer import NeuralAnalyzer

class MarketAnalyzer:
    def __init__(self):
        self.mex_api = MexAPI()
        self.neural_analyzer = NeuralAnalyzer()
        self.trading_balance = 50.0  # $50 для торговли
        self.reserve_balance = 50.0  # $50 резерв
        self.min_volume_24h = 10000  # Минимальный объем за 24ч (снижено)
        self.max_price_change = 25.0  # Максимальное изменение цены % (увеличено)
        
    def get_market_data(self) -> List[Dict]:
        """Получить данные по всем торговым парам"""
        try:
            # Получаем 24h статистику по всем парам
            tickers = self.mex_api.get_24hr_ticker()
            if not isinstance(tickers, list):
                return []
            
            # Фильтруем только USDT пары
            usdt_pairs = [
                ticker for ticker in tickers 
                if ticker['symbol'].endswith('USDT') and 
                float(ticker['quoteVolume']) > self.min_volume_24h
            ]
            
            return usdt_pairs
            
        except Exception as e:
            print(f"Ошибка получения рыночных данных: {e}")
            return []
    
    def get_klines(self, symbol: str, interval: str = '1h', limit: int = 100) -> List[List]:
        """Получить свечи для символа"""
        try:
            # Пробуем рабочие интервалы MEX
            intervals = ['60m', '4h', '1d', '30m', '15m']  # Используем 4h
            for intv in intervals:
                try:
                    result = self.mex_api.get_klines(symbol, intv, limit)
                    if isinstance(result, list) and len(result) > 0:
                        return result
                except:
                    continue
            return []
        except Exception as e:
            print(f"Ошибка получения свечей для {symbol}: {e}")
            return []
    
    def calculate_technical_indicators(self, klines: List[List]) -> Dict:
        """Рассчитать технические индикаторы"""
        if len(klines) < 3:  # Снижаем требование
            return {}
        
        closes = [float(k[4]) for k in klines]  # Цены закрытия
        volumes = [float(k[5]) for k in klines]  # Объемы
        
        # Простая скользящая средняя (SMA)
        sma_period = min(len(closes), 20)
        sma_20 = sum(closes[-sma_period:]) / sma_period
        sma_50 = sum(closes[-min(len(closes), 50):]) / min(len(closes), 50)
        
        # Текущая цена
        current_price = closes[-1]
        
        # Изменение цены за последние периоды
        price_change_1h = 0
        if len(closes) > 1 and closes[-2] > 0:
            price_change_1h = ((current_price - closes[-2]) / closes[-2]) * 100
            
        price_change_24h = 0
        if len(closes) > 1:
            prev_price_24h = closes[-min(len(closes), 24)]
            if prev_price_24h > 0:
                price_change_24h = ((current_price - prev_price_24h) / prev_price_24h) * 100
        
        # Средний объем
        vol_period = min(len(volumes), 20)
        avg_volume = sum(volumes[-vol_period:]) / vol_period
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # RSI упрощенный
        gains = []
        losses = []
        rsi_period = min(len(closes) - 1, 14)
        for i in range(1, rsi_period + 1):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))
        
        avg_gain = sum(gains) / len(gains) if gains else 0
        avg_loss = sum(losses) / len(losses) if losses else 0.001
        
        # Защита от деления на ноль
        if avg_loss == 0:
            rsi = 50  # Нейтральное значение
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        return {
            'current_price': current_price,
            'sma_20': sma_20,
            'sma_50': sma_50,
            'price_change_1h': price_change_1h,
            'price_change_24h': price_change_24h,
            'volume_ratio': volume_ratio,
            'rsi': rsi,
            'trend': 'UP' if current_price > sma_20 > sma_50 else 'DOWN'
        }
    
    def filter_trading_candidates(self, market_data: List[Dict]) -> List[Dict]:
        """Фильтровать кандидатов для торговли"""
        candidates = []
        
        for ticker in market_data:
            try:
                symbol = ticker['symbol']
                price_change = float(ticker['priceChangePercent'])
                volume = float(ticker['quoteVolume'])
                
                # Проверка на валидность данных
                if volume <= 0 or price_change is None:
                    continue
                
                # Базовые фильтры (смягченные)
                if (abs(price_change) > self.max_price_change or  # Слишком большое изменение
                    volume < self.min_volume_24h):  # Малый объем
                    continue
                
                # Получаем технические данные
                klines = self.get_klines(symbol)
                if not klines:
                    continue
                    
                tech_data = self.calculate_technical_indicators(klines)
                if not tech_data:
                    continue
                
                # Критерии отбора
                score = 0
                reasons = []
                
                # Объем выше среднего
                if tech_data['volume_ratio'] > 1.5:
                    score += 2
                    reasons.append("высокий_объем")
                
                # RSI в зоне перепроданности/перекупленности
                if 30 < tech_data['rsi'] < 70:
                    score += 1
                    reasons.append("нормальный_rsi")
                elif tech_data['rsi'] < 35:
                    score += 2
                    reasons.append("перепродано")
                
                # Тренд
                if tech_data['trend'] == 'UP' and tech_data['price_change_1h'] > 0:
                    score += 2
                    reasons.append("восходящий_тренд")
                
                # Цена выше SMA20
                if tech_data['current_price'] > tech_data['sma_20']:
                    score += 1
                    reasons.append("выше_sma20")
                
                if score >= 1:  # Минимальный порог (снижен)
                    candidates.append({
                        'symbol': symbol,
                        'score': score,
                        'reasons': reasons,
                        'current_price': tech_data['current_price'],
                        'price_change_24h': price_change,
                        'volume_24h': volume,
                        'tech_data': tech_data
                    })
            except Exception as e:
                print(f"Ошибка обработки {ticker.get('symbol', 'UNKNOWN')}: {e}")
                continue
        
        # Сортируем по скору
        return sorted(candidates, key=lambda x: x['score'], reverse=True)[:10]
    
    def calculate_position_size(self, symbol: str, price: float, score: int) -> float:
        """Рассчитать размер позиции"""
        # Проверка на валидность цены
        if price <= 0:
            print(f"Предупреждение: нулевая или отрицательная цена для {symbol}: {price}")
            return 0.0
            
        # Адаптивная логика: при малом торговом балансе используем больше средств
        if self.trading_balance < 20.0:
            # При балансе меньше $20 используем 20% от баланса
            base_allocation = self.trading_balance * 0.2
        else:
            # При большем балансе используем 10% от торгового баланса
            base_allocation = self.trading_balance * 0.1
        
        # Корректировка по скору
        score_multiplier = min(score / 5.0, 2.0)  # Максимум 2x
        
        # Итоговый размер в USDT
        position_size_usdt = base_allocation * score_multiplier
        
        # Обеспечиваем минимальную сумму $5
        if position_size_usdt < 5.0 and self.trading_balance >= 5.0:
            position_size_usdt = 5.0
        
        # Максимум $20
        position_size_usdt = min(position_size_usdt, 20.0)
        
        # Количество монет
        quantity = position_size_usdt / price
        
        return round(quantity, 6)
    
    def analyze_with_ai(self, candidate: Dict) -> Dict:
        """Анализ кандидата с помощью ИИ"""
        try:
            symbol = candidate['symbol']
            tech_data = candidate['tech_data']
            
            # Формируем данные для ИИ анализа
            market_data = {
                'symbol': symbol,
                'current_price': tech_data['current_price'],
                'price_change_24h': candidate['price_change_24h'],
                'volume_24h': candidate['volume_24h'],
                'rsi': tech_data['rsi'],
                'trend': tech_data['trend'],
                'volume_ratio': tech_data['volume_ratio']
            }
            
            # Получаем свечи для более точного анализа
            klines = self.get_klines(symbol, '60m', 50)
            
            # Получаем рекомендацию от ИИ
            ai_analysis = self.neural_analyzer.analyze_market_data(
                symbol, tech_data['current_price'], market_data, klines
            )
            
            return ai_analysis
            
        except Exception as e:
            print(f"Ошибка ИИ анализа для {candidate['symbol']}: {e}")
            return {
                'recommendation': 'HOLD',
                'confidence': 0.0,
                'analysis': f"Ошибка анализа: {str(e)}"
            }
    
    def get_trading_recommendations(self) -> List[Dict]:
        """Получить рекомендации для торговли"""
        print("Анализ рынка...")
        
        # Получаем рыночные данные
        market_data = self.get_market_data()
        if not market_data:
            return []
        
        print(f"Найдено {len(market_data)} торговых пар")
        
        # Фильтруем кандидатов
        candidates = self.filter_trading_candidates(market_data)
        print(f"Отобрано {len(candidates)} кандидатов")
        
        recommendations = []
        
        for candidate in candidates[:5]:  # Анализируем топ-5
            print(f"Анализ {candidate['symbol']}...")
            
            # ИИ анализ
            ai_analysis = self.analyze_with_ai(candidate)
            
            # Размер позиции
            quantity = self.calculate_position_size(
                candidate['symbol'], 
                candidate['current_price'], 
                candidate['score']
            )
            
            recommendation = {
                'symbol': candidate['symbol'],
                'action': ai_analysis['recommendation'],
                'confidence': ai_analysis['confidence'],
                'quantity': quantity,
                'price': candidate['current_price'],
                'score': candidate['score'],
                'reasons': candidate['reasons'],
                'ai_analysis': ai_analysis['analysis'],
                'position_size_usdt': quantity * candidate['current_price']
            }
            
            recommendations.append(recommendation)
        
        return recommendations

def test_market_analyzer():
    """Тест анализатора рынка"""
    analyzer = MarketAnalyzer()
    
    print("=== ТЕСТ АНАЛИЗАТОРА РЫНКА ===")
    recommendations = analyzer.get_trading_recommendations()
    
    print(f"\nПолучено {len(recommendations)} рекомендаций:")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['symbol']}")
        print(f"   Действие: {rec['action']}")
        print(f"   Уверенность: {rec['confidence']:.2f}")
        print(f"   Количество: {rec['quantity']}")
        print(f"   Цена: ${rec['price']:.6f}")
        print(f"   Размер позиции: ${rec['position_size_usdt']:.2f}")
        print(f"   Скор: {rec['score']}")
        print(f"   Причины: {', '.join(rec['reasons'])}")
        print(f"   ИИ анализ: {rec['ai_analysis'][:100]}...")

if __name__ == "__main__":
    test_market_analyzer()