#!/usr/bin/env python3
"""
Анализ позиций старше 10 дней с текущими ценами и P&L
"""

from mexc_advanced_api import MexAdvancedAPI
from mex_api import MexAPI
import time
from datetime import datetime
import json

def main():
    api = MexAPI()
    advanced_api = MexAdvancedAPI()
    
    print("🔍 АНАЛИЗ ПОЗИЦИЙ СТАРШЕ 10 ДНЕЙ")
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
    
    # Создаем пары для проверки
    pairs_to_check = []
    for asset, free, locked in active_assets:
        if asset != 'USDT' and (free > 0 or locked > 0):
            pairs_to_check.append(f"{asset}USDT")
    
    print(f"🔍 Анализирую {len(pairs_to_check)} пар...")
    
    old_positions = []
    
    for i, symbol in enumerate(pairs_to_check):
        print(f"[{i+1:2d}/{len(pairs_to_check)}] {symbol}...", end=" ")
        
        try:
            # Получаем сделки
            trades = advanced_api.get_my_trades(symbol, limit=1000)
            
            if not trades:
                print("❌")
                continue
            
            # Анализируем позиции
            positions = analyze_positions_for_symbol(symbol, trades)
            
            # Фильтруем позиции старше 10 дней
            old_pos = [p for p in positions if p['duration_days'] >= 10.0]
            
            if old_pos:
                print(f"✅ {len(old_pos)} позиций старше 10 дней")
                old_positions.extend(old_pos)
            else:
                print("❌")
                
        except Exception as e:
            print(f"❌ {e}")
            continue
        
        # Пауза между запросами
        time.sleep(0.1)
    
    if not old_positions:
        print("\n❌ Не найдено позиций старше 10 дней")
        return
    
    # Сортируем по продолжительности
    old_positions.sort(key=lambda x: x['duration_days'], reverse=True)
    
    print(f"\n📊 НАЙДЕНО {len(old_positions)} ПОЗИЦИЙ СТАРШЕ 10 ДНЕЙ")
    print("=" * 80)
    
    # Получаем текущие цены и рассчитываем P&L
    print("\n🔍 Получаю текущие цены...")
    
    for i, position in enumerate(old_positions, 1):
        symbol = position['symbol']
        
        try:
            # Получаем текущую цену
            price_data = api.get_ticker_price(symbol)
            current_price = None
            
            if isinstance(price_data, dict) and 'price' in price_data:
                current_price = float(price_data['price'])
            
            if current_price is None:
                print(f"❌ Не удалось получить цену для {symbol}")
                current_price = 0
                pnl = 0
                pnl_percent = 0
            else:
                # Рассчитываем P&L
                if position['type'] == 'LONG':
                    pnl = (current_price - position['start_price']) * position['quantity']
                    pnl_percent = ((current_price - position['start_price']) / position['start_price']) * 100 if position['start_price'] > 0 else 0
                else:  # SHORT
                    pnl = (position['start_price'] - current_price) * position['quantity']
                    pnl_percent = ((position['start_price'] - current_price) / position['start_price']) * 100 if position['start_price'] > 0 else 0
            
            # Форматируем вывод
            status = "🟢 ОТКРЫТА" if position.get('end_price') is None else "🔴 ЗАКРЫТА"
            pnl_color = "🟢" if pnl >= 0 else "🔴"
            
            print(f"\n#{i:2d}. {symbol} - {status}")
            print(f"    Тип: {position['type']}")
            print(f"    Продолжительность: {position['duration_days']:.1f} дней")
            print(f"    Начало: {datetime.fromtimestamp(position['start_time']/1000).strftime('%Y-%m-%d %H:%M:%S')}")
            if position.get('end_time'):
                print(f"    Конец: {datetime.fromtimestamp(position['end_time']/1000).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    Количество: {position['quantity']:.6f}")
            print(f"    Цена входа: {position['start_price']:.6f}")
            if position.get('end_price'):
                print(f"    Цена выхода: {position['end_price']:.6f}")
            else:
                print(f"    Текущая цена: {current_price:.6f}")
            
            if position.get('end_price'):
                # Для закрытых позиций показываем расчетный P&L
                if position.get('pnl') is not None:
                    print(f"    P&L: {position['pnl']:.2f} USDT")
                else:
                    print(f"    P&L: Не рассчитан")
            else:
                # Для открытых позиций показываем текущий P&L
                print(f"    {pnl_color} P&L: {pnl:.2f} USDT ({pnl_percent:+.2f}%)")
            
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ Ошибка получения цены для {symbol}: {e}")
            continue
        
        # Пауза между запросами цен
        time.sleep(0.2)
    
    # Итоговая статистика
    print(f"\n📈 ИТОГОВАЯ СТАТИСТИКА:")
    print("=" * 80)
    
    open_positions = [p for p in old_positions if p.get('end_price') is None]
    closed_positions = [p for p in old_positions if p.get('end_price') is not None]
    
    print(f"Всего позиций старше 10 дней: {len(old_positions)}")
    print(f"Открытых: {len(open_positions)}")
    print(f"Закрытых: {len(closed_positions)}")
    
    if old_positions:
        avg_duration = sum(p['duration_days'] for p in old_positions) / len(old_positions)
        print(f"Средняя продолжительность: {avg_duration:.1f} дней")
        
        longest = old_positions[0]
        print(f"Самая долгая: {longest['symbol']} - {longest['duration_days']:.1f} дней")

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
