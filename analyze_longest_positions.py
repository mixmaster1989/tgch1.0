#!/usr/bin/env python3
"""
Анализ позиций, которые дольше всего держатся
Получает данные через MEX API и анализирует время удержания спот позиций
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from mexc_advanced_api import MexAdvancedAPI
from mex_api import MexAPI

class PositionAnalyzer:
    def __init__(self):
        self.api = MexAPI()
        self.advanced_api = MexAdvancedAPI()
        
    def get_all_trading_pairs(self) -> List[str]:
        """Получить все доступные торговые пары"""
        try:
            exchange_info = self.api.get_exchange_info()
            if isinstance(exchange_info, dict) and 'symbols' in exchange_info:
                symbols = []
                for symbol_info in exchange_info['symbols']:
                    symbol = symbol_info.get('symbol', '')
                    # Фильтруем только спот пары с USDT
                    if symbol.endswith('USDT') and symbol_info.get('status') == 'TRADING':
                        symbols.append(symbol)
                return symbols
            return []
        except Exception as e:
            print(f"Ошибка получения списка пар: {e}")
            return []
    
    def analyze_position_duration(self, symbol: str, limit: int = 1000) -> Dict:
        """Анализировать продолжительность позиций для конкретной пары"""
        try:
            print(f"Анализирую позиции для {symbol}...")
            
            # Получаем историю сделок
            trades = self.advanced_api.get_my_trades(symbol, limit=limit)
            
            if not trades:
                return {
                    'symbol': symbol,
                    'total_trades': 0,
                    'positions': [],
                    'longest_position_days': 0,
                    'avg_position_days': 0
                }
            
            # Сортируем сделки по времени
            trades.sort(key=lambda x: x['time'])
            
            # Анализируем позиции
            positions = []
            current_position = 0  # Текущая позиция (положительная = лонг, отрицательная = шорт)
            position_start_time = None
            position_start_price = 0
            position_quantity = 0
            
            for trade in trades:
                trade_time = trade['time']
                trade_price = trade['price']
                trade_qty = trade['qty']
                is_buy = trade['isBuyer']
                
                if is_buy:
                    # Покупка
                    if current_position <= 0:  # Начинаем новую лонг позицию
                        if current_position < 0:  # Закрываем шорт позицию
                            if position_start_time:
                                duration_days = (trade_time - position_start_time) / (1000 * 60 * 60 * 24)
                                positions.append({
                                    'type': 'SHORT',
                                    'start_time': position_start_time,
                                    'end_time': trade_time,
                                    'duration_days': duration_days,
                                    'start_price': position_start_price,
                                    'end_price': trade_price,
                                    'quantity': abs(position_quantity),
                                    'pnl': (position_start_price - trade_price) * abs(position_quantity)
                                })
                        
                        # Начинаем лонг позицию
                        current_position = trade_qty
                        position_start_time = trade_time
                        position_start_price = trade_price
                        position_quantity = trade_qty
                    else:
                        # Увеличиваем лонг позицию
                        current_position += trade_qty
                        position_quantity += trade_qty
                else:
                    # Продажа
                    if current_position >= 0:  # Закрываем лонг позицию
                        if current_position > 0:  # Закрываем лонг позицию
                            if position_start_time:
                                duration_days = (trade_time - position_start_time) / (1000 * 60 * 60 * 24)
                                positions.append({
                                    'type': 'LONG',
                                    'start_time': position_start_time,
                                    'end_time': trade_time,
                                    'duration_days': duration_days,
                                    'start_price': position_start_price,
                                    'end_price': trade_price,
                                    'quantity': position_quantity,
                                    'pnl': (trade_price - position_start_price) * position_quantity
                                })
                        
                        # Начинаем шорт позицию
                        current_position = -trade_qty
                        position_start_time = trade_time
                        position_start_price = trade_price
                        position_quantity = -trade_qty
                    else:
                        # Увеличиваем шорт позицию
                        current_position -= trade_qty
                        position_quantity -= trade_qty
            
            # Если есть открытая позиция, считаем её как текущую
            current_position_info = None
            if current_position != 0 and position_start_time:
                current_time = int(time.time() * 1000)
                duration_days = (current_time - position_start_time) / (1000 * 60 * 60 * 24)
                current_position_info = {
                    'type': 'LONG' if current_position > 0 else 'SHORT',
                    'start_time': position_start_time,
                    'end_time': current_time,
                    'duration_days': duration_days,
                    'start_price': position_start_price,
                    'end_price': None,  # Текущая цена
                    'quantity': abs(current_position),
                    'pnl': None  # Не можем рассчитать без текущей цены
                }
            
            # Статистика
            if positions:
                longest_position = max(positions, key=lambda x: x['duration_days'])
                avg_duration = sum(p['duration_days'] for p in positions) / len(positions)
            else:
                longest_position = None
                avg_duration = 0
            
            return {
                'symbol': symbol,
                'total_trades': len(trades),
                'closed_positions': len(positions),
                'current_position': current_position_info,
                'positions': positions,
                'longest_position_days': longest_position['duration_days'] if longest_position else 0,
                'avg_position_days': avg_duration,
                'longest_position': longest_position
            }
            
        except Exception as e:
            print(f"Ошибка анализа позиций для {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'total_trades': 0,
                'positions': []
            }
    
    def get_longest_positions(self, symbols: List[str] = None, min_duration_days: float = 1.0) -> List[Dict]:
        """Получить позиции, которые держались дольше всего"""
        if symbols is None:
            symbols = self.get_all_trading_pairs()
        
        all_positions = []
        
        for symbol in symbols:
            try:
                analysis = self.analyze_position_duration(symbol)
                
                if 'error' not in analysis and analysis['positions']:
                    for position in analysis['positions']:
                        if position['duration_days'] >= min_duration_days:
                            position['symbol'] = symbol
                            all_positions.append(position)
                
                # Добавляем текущую позицию если она долгая
                if analysis.get('current_position') and analysis['current_position']['duration_days'] >= min_duration_days:
                    current_pos = analysis['current_position'].copy()
                    current_pos['symbol'] = symbol
                    all_positions.append(current_pos)
                    
            except Exception as e:
                print(f"Ошибка обработки {symbol}: {e}")
                continue
        
        # Сортируем по продолжительности
        all_positions.sort(key=lambda x: x['duration_days'], reverse=True)
        
        return all_positions
    
    def format_position_info(self, position: Dict) -> str:
        """Форматировать информацию о позиции"""
        start_time = datetime.fromtimestamp(position['start_time'] / 1000)
        end_time = datetime.fromtimestamp(position['end_time'] / 1000) if position['end_time'] else "Текущая"
        
        pnl_str = ""
        if position.get('pnl') is not None:
            pnl_str = f"P&L: {position['pnl']:.2f} USDT"
        else:
            pnl_str = "P&L: Не рассчитан (текущая позиция)"
        
        return f"""
Символ: {position['symbol']}
Тип: {position['type']}
Продолжительность: {position['duration_days']:.2f} дней
Начало: {start_time.strftime('%Y-%m-%d %H:%M:%S')}
Конец: {end_time}
Количество: {position['quantity']:.6f}
Цена входа: {position['start_price']:.6f}
Цена выхода: {position.get('end_price', 'N/A')}
{pnl_str}
"""

def main():
    analyzer = PositionAnalyzer()
    
    print("🔍 Анализ позиций, которые дольше всего держатся...")
    print("=" * 60)
    
    # Получаем топ-20 самых долгих позиций
    longest_positions = analyzer.get_longest_positions(min_duration_days=0.1)  # Минимум 2.4 часа
    
    if not longest_positions:
        print("❌ Не найдено позиций с достаточной продолжительностью")
        return
    
    print(f"📊 Найдено {len(longest_positions)} позиций")
    print("=" * 60)
    
    # Показываем топ-20
    for i, position in enumerate(longest_positions[:20], 1):
        print(f"\n🏆 Позиция #{i}")
        print(analyzer.format_position_info(position))
        print("-" * 40)
    
    # Статистика по символам
    symbol_stats = {}
    for position in longest_positions:
        symbol = position['symbol']
        if symbol not in symbol_stats:
            symbol_stats[symbol] = {
                'count': 0,
                'total_days': 0,
                'max_days': 0
            }
        
        symbol_stats[symbol]['count'] += 1
        symbol_stats[symbol]['total_days'] += position['duration_days']
        symbol_stats[symbol]['max_days'] = max(symbol_stats[symbol]['max_days'], position['duration_days'])
    
    print("\n📈 Статистика по символам:")
    print("=" * 60)
    
    # Сортируем по количеству долгих позиций
    sorted_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]['count'], reverse=True)
    
    for symbol, stats in sorted_symbols[:10]:
        avg_days = stats['total_days'] / stats['count']
        print(f"{symbol}: {stats['count']} позиций, макс. {stats['max_days']:.1f} дней, ср. {avg_days:.1f} дней")

if __name__ == "__main__":
    main()
