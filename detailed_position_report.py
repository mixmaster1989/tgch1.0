#!/usr/bin/env python3
"""
Детальный отчет по позициям с дополнительной информацией
"""

from mexc_advanced_api import MexAdvancedAPI
from mex_api import MexAPI
import time
from datetime import datetime
import json

def main():
    api = MexAPI()
    advanced_api = MexAdvancedAPI()
    
    print("📊 ДЕТАЛЬНЫЙ ОТЧЕТ ПО ПОЗИЦИЯМ")
    print("=" * 80)
    
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
            active_assets.append((balance['asset'], free, locked))
    
    print(f"💰 АКТИВЫ С БАЛАНСАМИ ({len(active_assets)} шт.):")
    print("-" * 50)
    for asset, free, locked in sorted(active_assets, key=lambda x: x[1] + x[2], reverse=True):
        total = free + locked
        print(f"{asset:8} | Свободно: {free:12.6f} | Заблокировано: {locked:12.6f} | Всего: {total:12.6f}")
    
    # Создаем пары для проверки
    pairs_to_check = []
    for asset, free, locked in active_assets:
        if asset != 'USDT' and (free > 0 or locked > 0):
            pairs_to_check.append(f"{asset}USDT")
    
    print(f"\n🔍 АНАЛИЗ ПОЗИЦИЙ ПО {len(pairs_to_check)} ПАРАМ:")
    print("=" * 80)
    
    all_positions = []
    current_positions = []
    
    for i, symbol in enumerate(pairs_to_check):
        print(f"\n[{i+1:2d}/{len(pairs_to_check)}] {symbol}")
        
        try:
            # Получаем сделки
            trades = advanced_api.get_my_trades(symbol, limit=1000)
            
            if not trades:
                print(f"    ❌ Сделок не найдено")
                continue
            
            print(f"    ✅ Сделок: {len(trades)}")
            
            # Анализируем позиции
            positions = analyze_positions_for_symbol(symbol, trades)
            
            if positions:
                closed_positions = [p for p in positions if p.get('end_price') is not None]
                open_positions = [p for p in positions if p.get('end_price') is None]
                
                print(f"    📈 Позиций: {len(positions)} (закрытых: {len(closed_positions)}, открытых: {len(open_positions)})")
                
                all_positions.extend(positions)
                current_positions.extend(open_positions)
                
                # Показываем самую долгую позицию для этой пары
                longest = max(positions, key=lambda x: x['duration_days'])
                print(f"    🏆 Самая долгая: {longest['duration_days']:.1f} дней ({longest['type']})")
                
            else:
                print(f"    ❌ Позиций не найдено")
                
        except Exception as e:
            print(f"    ❌ Ошибка: {e}")
            continue
        
        # Пауза между запросами
        time.sleep(0.1)
    
    # Сортируем по продолжительности
    all_positions.sort(key=lambda x: x['duration_days'], reverse=True)
    current_positions.sort(key=lambda x: x['duration_days'], reverse=True)
    
    print(f"\n📊 ИТОГОВАЯ СТАТИСТИКА:")
    print("=" * 80)
    print(f"Всего позиций: {len(all_positions)}")
    print(f"Открытых позиций: {len(current_positions)}")
    print(f"Закрытых позиций: {len(all_positions) - len(current_positions)}")
    
    if all_positions:
        avg_duration = sum(p['duration_days'] for p in all_positions) / len(all_positions)
        print(f"Средняя продолжительность: {avg_duration:.1f} дней")
        
        longest_overall = all_positions[0]
        print(f"Самая долгая позиция: {longest_overall['symbol']} - {longest_overall['duration_days']:.1f} дней")
    
    # ТОП-20 самых долгих позиций
    print(f"\n🏆 ТОП-20 САМЫХ ДОЛГИХ ПОЗИЦИЙ:")
    print("=" * 80)
    
    for i, position in enumerate(all_positions[:20], 1):
        status = "🟢 ОТКРЫТА" if position.get('end_price') is None else "🔴 ЗАКРЫТА"
        pnl_str = f"P&L: {position['pnl']:.2f} USDT" if position.get('pnl') is not None else "P&L: Не рассчитан"
        
        print(f"\n#{i:2d}. {position['symbol']} - {status}")
        print(f"    Тип: {position['type']}")
        print(f"    Продолжительность: {position['duration_days']:.2f} дней")
        print(f"    Начало: {datetime.fromtimestamp(position['start_time']/1000).strftime('%Y-%m-%d %H:%M:%S')}")
        if position.get('end_time'):
            print(f"    Конец: {datetime.fromtimestamp(position['end_time']/1000).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"    Количество: {position['quantity']:.6f}")
        print(f"    Цена входа: {position['start_price']:.6f}")
        if position.get('end_price'):
            print(f"    Цена выхода: {position['end_price']:.6f}")
        print(f"    {pnl_str}")
        print("-" * 60)
    
    # Текущие открытые позиции
    if current_positions:
        print(f"\n🟢 ТЕКУЩИЕ ОТКРЫТЫЕ ПОЗИЦИИ ({len(current_positions)} шт.):")
        print("=" * 80)
        
        for i, position in enumerate(current_positions, 1):
            print(f"\n#{i:2d}. {position['symbol']} - {position['type']}")
            print(f"    Продолжительность: {position['duration_days']:.2f} дней")
            print(f"    Начало: {datetime.fromtimestamp(position['start_time']/1000).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    Количество: {position['quantity']:.6f}")
            print(f"    Цена входа: {position['start_price']:.6f}")
            print(f"    Текущая цена: Не рассчитана")
            print("-" * 40)
    
    # Статистика по символам
    symbol_stats = {}
    for position in all_positions:
        symbol = position['symbol']
        if symbol not in symbol_stats:
            symbol_stats[symbol] = {
                'count': 0,
                'total_days': 0,
                'max_days': 0,
                'open_count': 0,
                'closed_count': 0
            }
        
        symbol_stats[symbol]['count'] += 1
        symbol_stats[symbol]['total_days'] += position['duration_days']
        symbol_stats[symbol]['max_days'] = max(symbol_stats[symbol]['max_days'], position['duration_days'])
        
        if position.get('end_price') is None:
            symbol_stats[symbol]['open_count'] += 1
        else:
            symbol_stats[symbol]['closed_count'] += 1
    
    print(f"\n📈 СТАТИСТИКА ПО СИМВОЛАМ:")
    print("=" * 80)
    print(f"{'Символ':<12} {'Всего':<6} {'Откр.':<6} {'Закр.':<6} {'Макс.дн.':<8} {'Ср.дн.':<8}")
    print("-" * 80)
    
    sorted_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]['max_days'], reverse=True)
    
    for symbol, stats in sorted_symbols:
        avg_days = stats['total_days'] / stats['count']
        print(f"{symbol:<12} {stats['count']:<6} {stats['open_count']:<6} {stats['closed_count']:<6} {stats['max_days']:<8.1f} {avg_days:<8.1f}")

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
