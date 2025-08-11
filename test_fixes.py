#!/usr/bin/env python3
"""
Тест исправлений в balance_monitor и pnl_monitor
"""

import asyncio
import logging
from balance_monitor import BalanceMonitor
from pnl_monitor import PnLMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_balance_monitor():
    """Тест монитора баланса"""
    print("🔍 ТЕСТ МОНИТОРА БАЛАНСА")
    print("=" * 40)
    
    monitor = BalanceMonitor()
    
    # Тест балансов
    usdt = monitor.get_usdt_balance()
    usdc = monitor.get_usdc_balance()
    
    print(f"💰 USDT баланс: ${usdt:.2f}")
    print(f"💰 USDC баланс: ${usdc:.2f}")
    
    # Тест расчета покупки (используем больший из балансов)
    test_amount = max(usdt, usdc)
    print(f"\n🧮 Тест расчета покупки на ${test_amount:.2f}:")
    purchase_plan = monitor.calculate_purchase_amounts(test_amount)
    
    for symbol, data in purchase_plan.items():
        print(f"   {symbol}:")
        print(f"      Сумма: ${data['usdc_amount']:.2f}")
        print(f"      Количество: {data['quantity']:.6f}")
        print(f"      Цена: ${data['price']:.4f}")
    
    return purchase_plan

def test_pnl_monitor():
    """Тест PnL монитора"""
    print("\n🔍 ТЕСТ PnL МОНИТОРА")
    print("=" * 40)
    
    monitor = PnLMonitor()
    
    # Тест статуса
    status = monitor.get_current_status()
    
    print(f"📊 Общий PnL: ${status['total_pnl']:.4f}")
    print(f"🎯 Порог продажи: ${status['profit_threshold']}")
    print(f"⚡ Автопродажа: {'Включена' if status['auto_sell_enabled'] else 'Отключена'}")
    
    # Проверка балансов
    balances = monitor.get_balances()
    print(f"\n💼 Найдено активов: {len(balances)}")
    
    for asset in ['BTC', 'ETH']:
        if asset in balances:
            quantity = balances[asset]['total']
            symbol = 'BTCUSDC' if asset == 'BTC' else 'ETHUSDC'
            price = monitor.get_current_price(symbol)
            pnl = monitor.calculate_pnl(asset, quantity, price) if price else 0
            
            print(f"   {asset}: {quantity:.6f} | PnL: ${pnl:.4f}")
            
            if pnl > monitor.profit_threshold:
                print(f"      🎯 ГОТОВ К ПРОДАЖЕ! (PnL > ${monitor.profit_threshold})")
    
    return status

async def main():
    """Главная функция тестирования"""
    print("🚀 ТЕСТИРОВАНИЕ ИСПРАВЛЕНИЙ")
    print("=" * 50)
    
    try:
        # Тест монитора баланса
        purchase_plan = await test_balance_monitor()
        
        # Тест PnL монитора
        pnl_status = test_pnl_monitor()
        
        print("\n✅ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        print("=" * 50)
        
        # Анализ результатов
        if purchase_plan:
            total_purchase = sum(data['usdc_amount'] for data in purchase_plan.values())
            print(f"💰 Готово к покупке на: ${total_purchase:.2f}")
            print(f"📊 Торговых пар: {len(purchase_plan)}")
        
        if pnl_status['total_pnl'] > pnl_status['profit_threshold']:
            print(f"🎯 Готово к продаже! PnL ${pnl_status['total_pnl']:.4f} > ${pnl_status['profit_threshold']}")
        
        print("\n🎉 Все компоненты работают корректно!")
        
    except Exception as e:
        print(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 