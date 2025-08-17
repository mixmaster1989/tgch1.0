#!/usr/bin/env python3
"""
Отладка монитора баланса
"""

from balance_monitor import BalanceMonitor
import asyncio

async def debug_monitor():
    monitor = BalanceMonitor()
    
    print("🔍 ОТЛАДКА МОНИТОРА БАЛАНСА")
    print("=" * 50)
    
    # Проверяем балансы
    usdc_balance = monitor.get_usdc_balance()
    usdt_balance = monitor.get_usdt_balance()
    
    print(f"💰 Балансы:")
    print(f"   USDC: ${usdc_balance:.2f}")
    print(f"   USDT: ${usdt_balance:.2f}")
    
    print(f"\n⚙️ Настройки:")
    print(f"   Минимальный баланс: ${monitor.min_balance_threshold}")
    print(f"   Максимальная покупка: ${monitor.max_purchase_amount}")
    print(f"   BTC распределение: {monitor.btc_allocation*100}%")
    print(f"   ETH распределение: {monitor.eth_allocation*100}%")
    
    # Проверяем условия покупки
    can_buy = usdc_balance >= monitor.min_balance_threshold
    can_make_purchase = monitor.can_make_purchase()
    
    print(f"\n✅ Условия покупки:")
    print(f"   Баланс достаточен: {can_buy}")
    print(f"   Можно покупать: {can_make_purchase}")
    
    if can_buy and can_make_purchase:
        print(f"\n🎯 ВЫПОЛНЯЕМ ПОКУПКУ!")
        
        # Рассчитываем план покупки
        purchase_plan = monitor.calculate_purchase_amounts(usdc_balance, 'USDC')
        print(f"   План покупки: {purchase_plan}")
        
        if purchase_plan:
            # Выполняем покупку
            results = await monitor.execute_auto_purchase(usdc_balance, 'USDC')
            print(f"   Результат: {results}")
        else:
            print(f"   ❌ План покупки пустой!")
    else:
        print(f"\n❌ ПОКУПКА НЕ ВОЗМОЖНА!")
        if not can_buy:
            print(f"   Причина: Баланс ${usdc_balance:.2f} < ${monitor.min_balance_threshold}")
        if not can_make_purchase:
            print(f"   Причина: Слишком рано для покупки")

if __name__ == "__main__":
    asyncio.run(debug_monitor()) 