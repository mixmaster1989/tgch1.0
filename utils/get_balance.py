#!/usr/bin/env python3
"""
Скрипт для получения текущего баланса USDT и USDC через API MEXC
"""

import json
from datetime import datetime
from mex_api import MexAPI

def get_usdt_usdc_balance():
    """Получить текущий баланс USDT и USDC"""
    try:
        print("🔍 ПОЛУЧЕНИЕ БАЛАНСА USDT И USDC")
        print("=" * 50)
        print(f"Время: {datetime.now()}")
        print()
        
        # Создаем API клиент
        api = MexAPI()
        
        # Получаем информацию об аккаунте
        print("📊 Запрос баланса через API...")
        account_info = api.get_account_info()
        
        if 'code' in account_info and account_info['code'] != 200:
            print(f"❌ ОШИБКА API: {account_info}")
            return None
        
        if 'error' in account_info:
            print(f"❌ ОШИБКА: {account_info}")
            return None
        
        print("✅ Баланс получен успешно!")
        print()
        
        # Ищем балансы USDT и USDC
        usdt_balance = 0.0
        usdc_balance = 0.0
        
        balances = account_info.get('balances', [])
        print(f"📋 Найдено {len(balances)} активов в аккаунте")
        
        for balance in balances:
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if asset == 'USDT':
                usdt_balance = total
                print(f"💰 USDT: {total:.8f} (свободно: {free:.8f}, заблокировано: {locked:.8f})")
            elif asset == 'USDC':
                usdc_balance = total
                print(f"💰 USDC: {total:.8f} (свободно: {free:.8f}, заблокировано: {locked:.8f})")
        
        print()
        print("=" * 50)
        print("📊 ИТОГОВЫЙ БАЛАНС:")
        print(f"   USDT: {usdt_balance:.8f}")
        print(f"   USDC: {usdc_balance:.8f}")
        print(f"   Общий баланс: {usdt_balance + usdc_balance:.8f}")
        print("=" * 50)
        
        return {
            'usdt': usdt_balance,
            'usdc': usdc_balance,
            'total': usdt_balance + usdc_balance,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        return None

def main():
    """Основная функция"""
    balance = get_usdt_usdc_balance()
    
    if balance:
        # Сохраняем результат в JSON файл
        with open('balance_result.json', 'w', encoding='utf-8') as f:
            json.dump(balance, f, ensure_ascii=False, indent=2)
        print(f"\n💾 Результат сохранен в файл: balance_result.json")
        
        # Возвращаем результат для использования в других скриптах
        return balance
    else:
        print("\n❌ Не удалось получить баланс")
        return None

if __name__ == "__main__":
    main() 