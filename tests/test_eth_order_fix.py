#!/usr/bin/env python3
"""
Тест исправления ордера ETH
"""

from balance_monitor import BalanceMonitor
import asyncio

async def test_eth_order():
    monitor = BalanceMonitor()
    
    print("🧪 ТЕСТ ИСПРАВЛЕНИЯ ОРДЕРА ETH")
    print("=" * 50)
    
    # Симулируем достаточный баланс USDC
    original_get_usdc_balance = monitor.get_usdc_balance
    
    def mock_usdc_balance():
        return 15.0  # Симулируем $15 USDC
    
    monitor.get_usdc_balance = mock_usdc_balance
    
    print(f"💰 Симулируем баланс USDC: ${monitor.get_usdc_balance():.2f}")
    
    # Получаем текущее распределение
    allocation = monitor.get_current_portfolio_allocation()
    needs_rebalancing = monitor.needs_rebalancing(allocation)
    
    print(f"📊 Текущее распределение:")
    print(f"   BTC: {allocation.get('btc_percent', 0):.1f}% (должно быть 60%)")
    print(f"   ETH: {allocation.get('eth_percent', 0):.1f}% (должно быть 40%)")
    print(f"   Нужна ребалансировка: {needs_rebalancing}")
    
    if needs_rebalancing:
        print(f"\n🎯 ТЕСТИРУЕМ ПЛАН РЕБАЛАНСИРОВКИ:")
        
        # Рассчитываем план покупки
        purchase_plan = monitor.calculate_purchase_amounts(monitor.get_usdc_balance(), 'USDC')
        
        if purchase_plan:
            print(f"   План покупки:")
            for symbol, data in purchase_plan.items():
                print(f"   - {symbol}: ${data['amount']:.2f} ({data['quantity']:.6f})")
                
                # Проверяем минимальные требования
                if symbol == 'ETHUSDC':
                    if data['quantity'] < 0.001:
                        print(f"     ⚠️ Количество ETH {data['quantity']:.6f} меньше минимума 0.001")
                    else:
                        print(f"     ✅ Количество ETH {data['quantity']:.6f} соответствует минимуму")
                elif symbol == 'BTCUSDC':
                    if data['quantity'] < 0.0001:
                        print(f"     ⚠️ Количество BTC {data['quantity']:.6f} меньше минимума 0.0001")
                    else:
                        print(f"     ✅ Количество BTC {data['quantity']:.6f} соответствует минимуму")
        else:
            print(f"   ❌ План покупки пустой!")
    
    # Восстанавливаем оригинальный метод
    monitor.get_usdc_balance = original_get_usdc_balance
    
    print(f"\n🔧 ИСПРАВЛЕНИЯ:")
    print(f"   ✅ Добавлены ретраи (3 попытки)")
    print(f"   ✅ Проверка минимальных количеств")
    print(f"   ✅ Проверка баланса перед ордером")
    print(f"   ✅ Обработка ошибки 'Insufficient position'")
    print(f"   ✅ Пауза между попытками (2 сек)")

if __name__ == "__main__":
    asyncio.run(test_eth_order()) 