import time
from datetime import datetime
from typing import Dict, List, Optional
from market_analyzer import MarketAnalyzer
from mex_api import MexAPI

class TradingEngine:
    def __init__(self, simulation_mode=True):
        self.market_analyzer = MarketAnalyzer()
        self.mex_api = MexAPI()
        self.max_positions = 3  # Максимум открытых позиций
        self.min_confidence = 0.7  # Минимальная уверенность ИИ
        self.simulation_mode = simulation_mode  # РЕЖИМ СИМУЛЯЦИИ - НЕ ТРАТИТ ДЕНЬГИ!
        
    def get_current_positions(self) -> List[Dict]:
        """Получить текущие открытые позиции"""
        try:
            account_info = self.mex_api.get_account_info()
            if 'balances' not in account_info:
                return []
            
            positions = []
            for balance in account_info['balances']:
                if (balance['asset'] != 'USDT' and 
                    float(balance['free']) > 0):
                    positions.append({
                        'symbol': balance['asset'] + 'USDT',
                        'asset': balance['asset'],
                        'quantity': float(balance['free']),
                        'locked': float(balance['locked'])
                    })
            
            return positions
            
        except Exception as e:
            print(f"Ошибка получения позиций: {e}")
            return []
    
    def get_usdt_balance(self) -> float:
        """Получить баланс USDT"""
        try:
            account_info = self.mex_api.get_account_info()
            if 'balances' not in account_info:
                return 0.0
            
            for balance in account_info['balances']:
                if balance['asset'] == 'USDT':
                    return float(balance['free'])
            
            return 0.0
            
        except Exception as e:
            print(f"Ошибка получения баланса USDT: {e}")
            return 0.0
    
    def place_buy_order(self, symbol: str, quantity: float) -> Dict:
        """Разместить ордер на покупку"""
        try:
            # Получаем текущую цену
            ticker = self.mex_api.get_symbol_ticker(symbol)
            if not ticker:
                return {'success': False, 'error': 'Не удалось получить цену'}
            
            price = float(ticker['price'])
            
            # РЕЖИМ СИМУЛЯЦИИ - НЕ ТРАТИМ ДЕНЬГИ!
            if self.simulation_mode:
                return {
                    'success': True,
                    'order_id': f'SIM_{int(time.time())}',
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': price,
                    'total': quantity * price,
                    'simulation': True
                }
            
            # Реальный ордер (ОТКЛЮЧЕН!)
            order = self.mex_api.create_order(
                symbol=symbol,
                side='BUY',
                type='MARKET',
                quantity=quantity
            )
            
            if order:
                return {
                    'success': True,
                    'order_id': order.get('orderId'),
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': price,
                    'total': quantity * price
                }
            else:
                return {'success': False, 'error': 'Ошибка создания ордера'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def place_sell_order(self, symbol: str, quantity: float) -> Dict:
        """Разместить ордер на продажу"""
        try:
            ticker = self.mex_api.get_symbol_ticker(symbol)
            price = float(ticker['price']) if ticker else 0
            
            # РЕЖИМ СИМУЛЯЦИИ - НЕ ТРАТИМ ДЕНЬГИ!
            if self.simulation_mode:
                return {
                    'success': True,
                    'order_id': f'SIM_{int(time.time())}',
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': price,
                    'total': quantity * price,
                    'simulation': True
                }
            
            # Реальный ордер (ОТКЛЮЧЕН!)
            order = self.mex_api.create_order(
                symbol=symbol,
                side='SELL',
                type='MARKET',
                quantity=quantity
            )
            
            if order:
                return {
                    'success': True,
                    'order_id': order.get('orderId'),
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': price,
                    'total': quantity * price
                }
            else:
                return {'success': False, 'error': 'Ошибка создания ордера'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def execute_buy_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """Выполнить рекомендации на покупку"""
        results = []
        current_positions = self.get_current_positions()
        usdt_balance = self.get_usdt_balance()
        
        print(f"Баланс USDT: ${usdt_balance:.2f}")
        print(f"Текущих позиций: {len(current_positions)}")
        
        # Проверяем лимиты
        if len(current_positions) >= self.max_positions:
            print(f"Достигнут лимит позиций ({self.max_positions})")
            return results
        
        if usdt_balance < 10:  # Минимум $10 для торговли
            print("Недостаточно USDT для торговли")
            return results
        
        # Фильтруем рекомендации
        buy_candidates = [
            rec for rec in recommendations 
            if (rec['action'] == 'BUY' and 
                rec['confidence'] >= self.min_confidence and
                rec['position_size_usdt'] <= usdt_balance)
        ]
        
        print(f"Кандидатов на покупку: {len(buy_candidates)}")
        
        for candidate in buy_candidates:
            if len(current_positions) + len(results) >= self.max_positions:
                break
                
            if usdt_balance < candidate['position_size_usdt']:
                continue
            
            print(f"Покупка {candidate['symbol']}...")
            
            # Размещаем ордер
            order_result = self.place_buy_order(
                candidate['symbol'], 
                candidate['quantity']
            )
            
            if order_result['success']:
                sim_text = " [SIMULATION]" if order_result.get('simulation') else ""
                print(f"Ордер размещен: {candidate['symbol']}{sim_text}")
                usdt_balance -= order_result['total']
                results.append({
                    'action': 'BUY',
                    'symbol': candidate['symbol'],
                    'result': order_result,
                    'recommendation': candidate
                })
            else:
                print(f"Ошибка ордера {candidate['symbol']}: {order_result['error']}")
                results.append({
                    'action': 'BUY',
                    'symbol': candidate['symbol'],
                    'result': order_result,
                    'recommendation': candidate
                })
            
            time.sleep(1)  # Пауза между ордерами
        
        return results
    
    def check_sell_conditions(self) -> List[Dict]:
        """Проверить условия для продажи"""
        positions = self.get_current_positions()
        sell_recommendations = []
        
        for position in positions:
            try:
                # Получаем текущую цену
                ticker = self.mex_api.get_symbol_ticker(position['symbol'])
                if not ticker:
                    continue
                
                current_price = float(ticker['price'])
                
                # Простая логика: продаем если прибыль > 5% или убыток > 3%
                # (В реальности нужно хранить цену покупки)
                
                # Получаем данные для анализа
                klines = self.market_analyzer.get_klines(position['symbol'])
                if not klines:
                    continue
                
                tech_data = self.market_analyzer.calculate_technical_indicators(klines)
                if not tech_data:
                    continue
                
                # Условия продажи
                should_sell = False
                reason = ""
                
                # RSI перекуплен
                if tech_data['rsi'] > 75:
                    should_sell = True
                    reason = "RSI_перекуплен"
                
                # Нисходящий тренд
                elif (tech_data['trend'] == 'DOWN' and 
                      tech_data['price_change_1h'] < -2):
                    should_sell = True
                    reason = "нисходящий_тренд"
                
                # Низкий объем
                elif tech_data['volume_ratio'] < 0.5:
                    should_sell = True
                    reason = "низкий_объем"
                
                if should_sell:
                    sell_recommendations.append({
                        'symbol': position['symbol'],
                        'asset': position['asset'],
                        'quantity': position['quantity'],
                        'current_price': current_price,
                        'reason': reason,
                        'tech_data': tech_data
                    })
            
            except Exception as e:
                print(f"Ошибка анализа позиции {position['symbol']}: {e}")
        
        return sell_recommendations
    
    def execute_sell_recommendations(self, sell_recommendations: List[Dict]) -> List[Dict]:
        """Выполнить рекомендации на продажу"""
        results = []
        
        for rec in sell_recommendations:
            print(f"Продажа {rec['symbol']} (причина: {rec['reason']})...")
            
            order_result = self.place_sell_order(rec['symbol'], rec['quantity'])
            
            if order_result['success']:
                sim_text = " [SIMULATION]" if order_result.get('simulation') else ""
                print(f"Продажа выполнена: {rec['symbol']}{sim_text}")
            else:
                print(f"Ошибка продажи {rec['symbol']}: {order_result['error']}")
            
            results.append({
                'action': 'SELL',
                'symbol': rec['symbol'],
                'result': order_result,
                'recommendation': rec
            })
            
            time.sleep(1)
        
        return results
    
    def run_trading_cycle(self) -> Dict:
        """Запустить торговый цикл"""
        print(f"[TRADING DEBUG] Запуск торгового цикла - {datetime.now().strftime('%H:%M:%S')}")
        
        results = {
            'timestamp': datetime.now(),
            'buy_orders': [],
            'sell_orders': [],
            'errors': []
        }
        
        try:
            print("[TRADING DEBUG] Проверка условий продажи...")
            # 1. Проверяем условия продажи
            sell_recommendations = self.check_sell_conditions()
            print(f"[TRADING DEBUG] Найдено {len(sell_recommendations)} позиций для продажи")
            
            if sell_recommendations:
                sell_results = self.execute_sell_recommendations(sell_recommendations)
                results['sell_orders'] = sell_results
            
            print("[TRADING DEBUG] Поиск возможностей покупки...")
            # 2. Ищем возможности покупки
            buy_recommendations = self.market_analyzer.get_trading_recommendations()
            print(f"[TRADING DEBUG] Найдено {len(buy_recommendations)} возможностей покупки")
            
            if buy_recommendations:
                buy_results = self.execute_buy_recommendations(buy_recommendations)
                results['buy_orders'] = buy_results
            
            print("[TRADING DEBUG] Торговый цикл завершен")
            
        except Exception as e:
            error_msg = f"Ошибка торгового цикла: {str(e)}"
            print(f"[TRADING ERROR] {error_msg}")
            results['errors'].append(error_msg)
            import traceback
            traceback.print_exc()
        
        return results

def test_trading_engine():
    """Тест торгового движка"""
    engine = TradingEngine(simulation_mode=True)  # РЕЖИМ СИМУЛЯЦИИ
    
    print("=== ТЕСТ ТОРГОВОГО ДВИЖКА ===")
    
    # Тест анализа рынка
    print("\n1. Тест анализа рынка...")
    recommendations = engine.market_analyzer.get_trading_recommendations()
    print(f"Получено {len(recommendations)} рекомендаций")
    
    # Тест проверки позиций
    print("\n2. Тест текущих позиций...")
    positions = engine.get_current_positions()
    print(f"Текущих позиций: {len(positions)}")
    
    # Тест баланса
    print("\n3. Тест баланса...")
    balance = engine.get_usdt_balance()
    print(f"Баланс USDT: ${balance:.2f}")
    
    # Тест условий продажи
    print("\n4. Тест условий продажи...")
    sell_recs = engine.check_sell_conditions()
    print(f"Позиций для продажи: {len(sell_recs)}")

if __name__ == "__main__":
    test_trading_engine()