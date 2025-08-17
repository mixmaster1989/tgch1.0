#!/usr/bin/env python3
"""
Тест логики ребалансировки
"""

from balance_monitor import BalanceMonitor
import asyncio

async def test_rebalancing():
    monitor = BalanceMonitor()
    
    print("🧪 ТЕСТ ЛОГИКИ РЕБАЛАНСИРОВКИ")
    print("=" * 50)
    
    # Получаем текущее распределение
    allocation = monitor.get_current_portfolio_allocation()
    needs_rebalancing = monitor.needs_rebalancing(allocation)
    
    print(f"📊 Текущее распределение:")
    print(f"   BTC: {allocation.get('btc_percent', 0):.1f}% (должно быть 60%)")
    print(f"   ETH: {allocation.get('eth_percent', 0):.1f}% (должно быть 40%)")
    print(f"   Нужна ребалансировка: {needs_rebalancing}")
    
    # Получаем баланс USDC
    usdc_balance = monitor.get_usdc_balance()
    print(f"\n💰 Доступно USDC: ${usdc_balance:.2f}")
    
    if usdc_balance >= monitor.min_balance_threshold:
        print(f"\n🎯 ТЕСТИРУЕМ ПЛАН ПОКУПКИ:")
        
        # Рассчитываем план покупки
        purchase_plan = monitor.calculate_purchase_amounts(usdc_balance, 'USDC')
        
        if purchase_plan:
            print(f"   План покупки:")
            for symbol, data in purchase_plan.items():
                print(f"   - {symbol}: ${data['amount']:.2f} ({data['quantity']:.6f})")
        else:
            print(f"   ❌ План покупки пустой!")
    else:
        print(f"\n❌ Недостаточно USDC для покупки (нужно ${monitor.min_balance_threshold})")
    
    # Показываем, что должно произойти
    btc_percent = allocation.get('btc_percent', 0)
    eth_percent = allocation.get('eth_percent', 0)
    
    print(f"\n🔍 АНАЛИЗ ЛОГИКИ:")
    if btc_percent > 60:
        print(f"   ✅ BTC слишком много ({btc_percent:.1f}% > 60%)")
        print(f"   🎯 Система должна купить ТОЛЬКО ETH")
    elif eth_percent > 40:
        print(f"   ✅ ETH слишком много ({eth_percent:.1f}% > 40%)")
        print(f"   🎯 Система должна купить ТОЛЬКО BTC")
    else:
        print(f"   ✅ Оба актива меньше нормы")
        print(f"   🎯 Система должна купить оба пропорционально")

if __name__ == "__main__":
    asyncio.run(test_rebalancing()) 