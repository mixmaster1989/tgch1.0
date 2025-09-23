#!/usr/bin/env python3
"""
Проверка реальных балансов стейблкоинов через API
"""

from mex_api import MexAPI

def main():
    print("💰 Проверка реальных балансов стейблкоинов...")
    
    api = MexAPI()
    account_info = api.get_account_info()
    
    if 'balances' not in account_info:
        print(f"❌ Ошибка API: {account_info}")
        return
    
    stables = {}
    for balance in account_info['balances']:
        asset = balance['asset']
        if asset in ['USDT', 'USDC']:
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            stables[asset] = {
                'free': free,
                'locked': locked, 
                'total': total
            }
    
    print(f"\n📊 РЕАЛЬНЫЕ БАЛАНСЫ СТЕЙБЛОВ:")
    for asset, data in stables.items():
        print(f"💰 {asset}:")
        print(f"   🆓 Свободно: ${data['free']:.2f}")
        print(f"   🔒 Заблокировано: ${data['locked']:.2f}")
        print(f"   📊 Всего: ${data['total']:.2f}")
    
    if 'USDT' in stables and 'USDC' in stables:
        total = stables['USDT']['total'] + stables['USDC']['total']
        usdt_percent = (stables['USDT']['total'] / total * 100) if total > 0 else 0
        usdc_percent = (stables['USDC']['total'] / total * 100) if total > 0 else 0
        
        print(f"\n⚖️ РАСПРЕДЕЛЕНИЕ:")
        print(f"💚 USDT: {usdt_percent:.1f}%")
        print(f"💙 USDC: {usdc_percent:.1f}%")
        print(f"💰 Общая сумма: ${total:.2f}")
        
        diff = abs(stables['USDT']['total'] - stables['USDC']['total'])
        print(f"📏 Разница: ${diff:.2f}")

if __name__ == "__main__":
    main()