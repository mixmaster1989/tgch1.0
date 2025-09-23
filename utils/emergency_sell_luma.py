#!/usr/bin/env python3
"""
ЭКСТРЕННАЯ ПРОДАЖА LUMAUSDT!
Срочно продаем купленный альт на $50
"""

import sys
import logging
from mex_api import MexAPI

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def emergency_sell_luma():
    """ЭКСТРЕННАЯ ПРОДАЖА LUMAUSDT"""
    
    print("🚨 ЭКСТРЕННАЯ ПРОДАЖА LUMAUSDT!")
    print("=" * 50)
    
    try:
        # Создаем API
        api = MexAPI()
        
        # Проверяем баланс LUMA
        account_info = api.get_account_info()
        luma_balance = 0.0
        
        for balance in account_info.get('balances', []):
            if balance['asset'] == 'LUMA':
                luma_balance = float(balance['free'])
                break
        
        if luma_balance <= 0:
            print("❌ LUMA не найден в балансе")
            return
        
        print(f"💰 Найден баланс LUMA: {luma_balance}")
        
        # Получаем текущую цену
        ticker = api.get_ticker_price('LUMAUSDT')
        if not ticker or 'price' not in ticker:
            print("❌ Не удалось получить цену LUMA")
            return
        
        current_price = float(ticker['price'])
        print(f"📊 Текущая цена LUMA: ${current_price}")
        
        # Рассчитываем примерную стоимость
        estimated_value = luma_balance * current_price
        print(f"💵 Примерная стоимость: ${estimated_value:.2f}")
        
        # ПОДТВЕРЖДЕНИЕ ПРОДАЖИ
        confirm = input(f"\n🚨 ПРОДАТЬ {luma_balance} LUMA по рыночной цене? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("❌ Продажа отменена")
            return
        
        print("🔥 ВЫПОЛНЯЕМ ЭКСТРЕННУЮ ПРОДАЖУ...")
        
        # Продаем ВСЕ LUMA по рыночной цене
        order = api.place_order(
            symbol='LUMAUSDT',
            side='SELL',
            quantity=luma_balance
        )
        
        if order and 'orderId' in order:
            print(f"✅ LUMA ПРОДАН УСПЕШНО!")
            print(f"🆔 Ордер: {order['orderId']}")
            print(f"📊 Количество: {luma_balance}")
            print(f"💰 Цена: ~${current_price}")
            print(f"💵 Примерная выручка: ${estimated_value:.2f}")
            
            # Проверяем новый баланс
            new_account = api.get_account_info()
            for balance in new_account.get('balances', []):
                if balance['asset'] == 'USDT':
                    usdt_balance = float(balance['free'])
                    print(f"💵 Новый баланс USDT: ${usdt_balance:.2f}")
                    break
                    
        else:
            print(f"❌ Ошибка продажи: {order}")
            
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        logger.error(f"Ошибка экстренной продажи: {e}")

def check_luma_balance():
    """Проверить баланс LUMA"""
    try:
        api = MexAPI()
        account_info = api.get_account_info()
        
        print("🔍 ПРОВЕРКА БАЛАНСА LUMA:")
        print("=" * 30)
        
        for balance in account_info.get('balances', []):
            if balance['asset'] == 'LUMA':
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                print(f"💰 LUMA:")
                print(f"   Свободно: {free}")
                print(f"   Заблокировано: {locked}")
                print(f"   Всего: {total}")
                
                if total > 0:
                    # Получаем цену
                    ticker = api.get_ticker_price('LUMAUSDT')
                    if ticker and 'price' in ticker:
                        price = float(ticker['price'])
                        value = total * price
                        print(f"   Текущая цена: ${price}")
                        print(f"   Стоимость: ${value:.2f}")
                
                return
        
        print("❌ LUMA не найден в балансе")
        
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")

def main():
    """Основная функция"""
    print("🚨 ЭКСТРЕННЫЙ СКРИПТ ПРОДАЖИ LUMAUSDT")
    print("=" * 50)
    
    while True:
        print("\nВыберите действие:")
        print("1. 🔍 Проверить баланс LUMA")
        print("2. 🚨 ЭКСТРЕННАЯ ПРОДАЖА LUMA")
        print("3. ❌ Выход")
        
        choice = input("\nВведите номер (1-3): ")
        
        if choice == '1':
            check_luma_balance()
        elif choice == '2':
            emergency_sell_luma()
        elif choice == '3':
            print("👋 Выход")
            break
        else:
            print("❌ Неверный выбор")

if __name__ == "__main__":
    main() 