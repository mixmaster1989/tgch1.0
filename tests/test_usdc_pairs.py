#!/usr/bin/env python3
"""
Тестовый скрипт для проверки USDC пар и конвертации
"""

from mex_api import MexAPI
import json

def main():
    api = MexAPI()
    
    print("🔍 Тестирование USDC пар и конвертации...")
    
    try:
        # 1. Проверяем наличие USDC в балансе
        print("\n1. Проверка баланса USDC:")
        account_info = api.get_account_info()
        usdc_balance = 0
        usdt_balance = 0
        
        for balance in account_info.get('balances', []):
            if balance['asset'] == 'USDC':
                usdc_balance = float(balance['free'])
                print(f"USDC баланс: {usdc_balance}")
            elif balance['asset'] == 'USDT':
                usdt_balance = float(balance['free'])
                print(f"USDT баланс: {usdt_balance}")
        
        # 2. Проверяем цены USDC пар
        usdc_pairs = ['BTCUSDC', 'ETHUSDC', 'BNBUSDC', 'ADAUSDC']
        print(f"\n2. Проверка цен USDC пар:")
        for pair in usdc_pairs:
            try:
                price_info = api.get_ticker_price(pair)
                print(f"{pair}: {price_info}")
            except Exception as e:
                print(f"{pair}: Ошибка - {e}")
        
        # 3. Проверяем стаканы USDC пар
        print(f"\n3. Проверка стаканов USDC пар:")
        for pair in usdc_pairs:
            try:
                depth_info = api.get_depth(pair, 5)
                print(f"{pair} стакан: {len(depth_info.get('bids', []))} bids, {len(depth_info.get('asks', []))} asks")
            except Exception as e:
                print(f"{pair} стакан: Ошибка - {e}")
        
        # 4. Тестируем размещение ордеров в USDC парах
        print(f"\n4. Тест размещения ордеров в USDC парах:")
        for pair in usdc_pairs:
            try:
                # Получаем текущую цену
                price_info = api.get_ticker_price(pair)
                if 'price' in price_info:
                    current_price = float(price_info['price'])
                    # Размещаем ордер с ценой ниже рыночной
                    test_price = current_price * 0.9  # 90% от текущей цены
                    test_quantity = 0.001  # Минимальное количество
                    
                    test_order = api.place_order(
                        symbol=pair,
                        side='BUY',
                        quantity=test_quantity,
                        price=test_price
                    )
                    print(f"{pair}: {test_order}")
                else:
                    print(f"{pair}: Не удалось получить цену")
            except Exception as e:
                print(f"{pair}: Ошибка размещения ордера - {e}")
        
        # 5. Проверяем возможность конвертации USDT в USDC
        print(f"\n5. Проверка конвертации USDT -> USDC:")
        if usdt_balance > 0:
            try:
                # Пытаемся купить USDC за USDT
                usdt_usdc_order = api.place_order(
                    symbol='USDCUSDT',  # Пара для конвертации
                    side='BUY',
                    quantity=1.0,  # Покупаем 1 USDC
                    price=1.0  # По цене 1:1
                )
                print(f"USDT -> USDC конвертация: {usdt_usdc_order}")
            except Exception as e:
                print(f"USDT -> USDC конвертация: Ошибка - {e}")
        else:
            print("Нет USDT для конвертации")
        
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")

if __name__ == "__main__":
    main() 