#!/usr/bin/env python3
"""
Анализ позиций на основе балансов аккаунта
Проверяем только те пары, по которым есть ненулевые балансы
"""

from mexc_advanced_api import MexAdvancedAPI
from mex_api import MexAPI
import time
from datetime import datetime
import json

def main():
    api = MexAPI()
    advanced_api = MexAdvancedAPI()
    
    print("🔍 Анализ позиций на основе балансов...")
    
    # Получаем информацию об аккаунте
    account_info = api.get_account_info()
    
    if not isinstance(account_info, dict) or 'balances' not in account_info:
        print("❌ Не удалось получить информацию об аккаунте")
        return
    
    # Находим активы с ненулевыми балансами
    active_assets = []
    for balance in account_info['balances']:
        free = float(balance.get('free', 0))
        locked = float(balance.get('locked', 0))
        if free > 0 or locked > 0:
            active_assets.append(balance['asset'])
    
    print(f"📊 Найдено {len(active_assets)} активов с балансами:")
    for asset in active_assets:
        print(f"  - {asset}")
    
    # Создаем пары для проверки
    pairs_to_check = []
    for asset in active_assets:
        if asset != 'USDT':  # USDT - это базовая валюта
            pairs_to_check.append(f"{asset}USDT")
    
    print(f"\n🔍 Проверяем {len(pairs_to_check)} пар на наличие сделок...")
    
    all_positions = []
    
    for i, symbol in enumerate(pairs_to_check):
        print(f"\n[{i+1}/{len(pairs_to_check)}] Анализирую {symbol}...")
        
        try:
            # Получаем сделки
            trades = advanced_api.get_my_trades(symbol, limit=1000)
            
            if not trades:
                print(f"  ❌ Сделок не найдено")
                continue
            
            print(f"  ✅ Найдено {len(trades)} сделок")
            
            # Анализируем позиции
            positions = analyze_positions_for_symbol(symbol, trades)
            
            if positions:
                print(f"  📈 Найдено {len(positions)} позиций")
                all_positions.extend(positions)
            else:
                print(f"  ❌ Позиций не найдено")
                
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            continue
        
        # Пауза между запросами
        time.sleep(0.2)
    
    # Сортируем по продолжительности
    all_positions.sort(key=lambda x: x['duration_days'], reverse=True)
    
    print(f"\n📊 ИТОГОВЫЙ АНАЛИЗ:")
    print(f"Всего найдено {len(all_positions)} позиций")
    
    if all_positions:
        print(f"\n🏆 ТОП-10 САМЫХ ДОЛГИХ ПОЗИЦИЙ:")
        print("=" * 80)
        
        for i, position in enumerate(all_positions[:10], 1):
            print(f"\n#{i}. {position['symbol']}")
            print(f"   Тип: {position['type']}")
            print(f"   Продолжительность: {position['duration_days']:.2f} дней")
            print(f"   Начало: {datetime.fromtimestamp(position['start_time']/1000).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   Конец: {datetime.fromtimestamp(position['end_time']/1000).strftime('%Y-%m-%d %H:%M:%S') if position['end_time'] else 'Текущая'}")
            print(f"   Количество: {position['quantity']:.6f}")
            print(f"   Цена входа: {position['start_price']:.6f}")
            print(f"   Цена выхода: {position.get('end_price', 'N/A')}")
            if position.get('pnl') is not None:
                print(f"   P&L: {position['pnl']:.2f} USDT")
            print("-" * 40)
        
        # Статистика по символам
        symbol_stats = {}
        for position in all_positions:
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
        
        print(f"\n📈 СТАТИСТИКА ПО СИМВОЛАМ:")
        print("=" * 60)
        
        sorted_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]['max_days'], reverse=True)
        
        for symbol, stats in sorted_symbols:
            avg_days = stats['total_days'] / stats['count']
            print(f"{symbol}: {stats['count']} позиций, макс. {stats['max_days']:.1f} дней, ср. {avg_days:.1f} дней")

def analyze_positions_for_symbol(symbol: str, trades: list) -> list:
    """Анализировать позиции для конкретного символа"""
    
    # Сортируем сделки по времени
    trades.sort(key=lambda x: x['time'])
    
    positions = []
    current_position = 0  # Текущая позиция
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
                            'symbol': symbol,
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
                            'symbol': symbol,
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
    if current_position != 0 and position_start_time:
        current_time = int(time.time() * 1000)
        duration_days = (current_time - position_start_time) / (1000 * 60 * 60 * 24)
        positions.append({
            'symbol': symbol,
            'type': 'LONG' if current_position > 0 else 'SHORT',
            'start_time': position_start_time,
            'end_time': current_time,
            'duration_days': duration_days,
            'start_price': position_start_price,
            'end_price': None,  # Текущая цена
            'quantity': abs(current_position),
            'pnl': None  # Не можем рассчитать без текущей цены
        })
    
    return positions

if __name__ == "__main__":
    main()

