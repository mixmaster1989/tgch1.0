#!/usr/bin/env python3
"""
Скрипт для проверки поддерживаемых символов на бирже MEX
"""

from mex_api import MexAPI
import json

def main():
    api = MexAPI()
    
    print("🔍 Проверка поддерживаемых символов на MEX...")
    
    try:
        # Получаем информацию о бирже
        exchange_info = api.get_exchange_info()
        
        if 'symbols' in exchange_info:
            symbols = exchange_info['symbols']
            print(f"📊 Всего символов: {len(symbols)}")
            
            # Показываем первые 5 символов для понимания структуры
            print(f"\n📋 Примеры символов:")
            for i, symbol in enumerate(symbols[:5]):
                status = symbol.get('status', 'N/A')
                print(f"   {i+1}. {symbol['symbol']} - Статус: {status} (тип: {type(status)})")
                print(f"      Базовый актив: {symbol.get('baseAsset', 'N/A')}")
                print(f"      Котируемый актив: {symbol.get('quoteAsset', 'N/A')}")
                print(f"      Разрешенные ордера: {symbol.get('orderTypes', [])}")
                print()
            
            # Проверяем статусы
            statuses = {}
            for symbol in symbols:
                status = symbol.get('status', 'UNKNOWN')
                statuses[status] = statuses.get(status, 0) + 1
            
            print(f"\n📊 Статусы символов:")
            for status, count in statuses.items():
                print(f"   {status} (тип: {type(status)}): {count}")
            
            # Ищем торговые символы (статус '1' = активная торговля)
            trading_symbols = [s for s in symbols if s.get('status') == '1']
            print(f"\n✅ Торговых символов: {len(trading_symbols)}")
            
            # Фильтруем USDT пары
            usdt_trading_pairs = [s for s in trading_symbols if s['symbol'].endswith('USDT')]
            print(f"💱 USDT торговых пар: {len(usdt_trading_pairs)}")
            
            # Показываем первые 10 USDT торговых символов
            print(f"\n📋 Первые 10 USDT торговых символов:")
            for i, symbol in enumerate(usdt_trading_pairs[:10]):
                print(f"   {i+1}. {symbol['symbol']} ({symbol.get('baseAsset', 'N/A')}/{symbol.get('quoteAsset', 'N/A')})")
            
            # Проверяем конкретные символы
            test_symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT']
            print(f"\n🔍 Проверка конкретных символов:")
            for symbol_name in test_symbols:
                found = False
                for symbol_info in usdt_trading_pairs:
                    if symbol_info['symbol'] == symbol_name:
                        found = True
                        print(f"✅ {symbol_name}: Статус {symbol_info['status']}")
                        print(f"   Разрешенные ордера: {symbol_info.get('orderTypes', [])}")
                        break
                
                if not found:
                    print(f"❌ {symbol_name}: НЕ НАЙДЕН")
                
        else:
            print(f"❌ Ошибка получения информации: {exchange_info}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main() 