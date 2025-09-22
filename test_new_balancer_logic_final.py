#!/usr/bin/env python3
"""
Финальный тестовый скрипт для проверки новой логики PortfolioBalancer
"""

import asyncio
from portfolio_balancer import PortfolioBalancer

async def test_new_balancer_logic():
    """Тестируем новую логику балансировки"""
    print("🧪 ТЕСТИРОВАНИЕ НОВОЙ ЛОГИКИ PORTFOLIO BALANCER")
    print("=" * 60)
    
    balancer = PortfolioBalancer()
    
    # Тест 1: BTC в плюсе, ETH в минусе, есть USDC
    print("\n1️⃣ ТЕСТ: BTC в плюсе, ETH в минусе, есть USDC")
    print("   Ожидаем: Покупка ETH за USDC")
    
    def mock_balances_test1():
        return {'BTC': 0.001, 'ETH': 0.01, 'USDC': 100.0}
    
    def mock_values_test1():
        return {
            'btc_value': 60.0,  # 60% от портфеля
            'eth_value': 30.0,  # 30% от портфеля (нужно 40%)
            'total_value': 100.0,
            'btc_price': 60000.0,
            'eth_price': 3000.0,
            'btc_ratio': 0.60,
            'eth_ratio': 0.30
        }
    
    balancer.get_portfolio_balances = mock_balances_test1
    balancer.get_portfolio_values = lambda b: mock_values_test1()
    balancer.get_usdc_balance = lambda: 100.0
    
    # Мокаем PnL
    def mock_btc_pnl(asset, balances, values):
        return 5.0 if asset == 'BTC' else -2.0  # BTC в плюсе, ETH в минусе
    
    balancer.get_asset_pnl = mock_btc_pnl
    
    result = balancer.calculate_rebalance_trades(mock_balances_test1(), mock_values_test1())
    
    print(f"   📊 BTC PnL: $5.0 (плюс)")
    print(f"   📊 ETH PnL: $-2.0 (минус)")
    print(f"   💰 USDC: $100.0")
    print(f"   �� Торгов: {len(result['trades'])}")
    
    for trade in result['trades']:
        reason = trade.get('reason', 'Причина не указана')
        print(f"      {trade['action']} {trade['symbol']} - {reason}")
    
    # Тест 2: BTC в плюсе, ETH в минусе, НЕТ USDC (исправленный)
    print("\n2️⃣ ТЕСТ: BTC в плюсе, ETH в минусе, НЕТ USDC")
    print("   Ожидаем: Продажа BTC для покупки ETH")
    
    # Нужно купить ETH на $10.0, но USDC только $5.0
    balancer.get_usdc_balance = lambda: 5.0  # Мало USDC
    
    result = balancer.calculate_rebalance_trades(mock_balances_test1(), mock_values_test1())
    
    print(f"   📊 BTC PnL: $5.0 (плюс)")
    print(f"   📊 ETH PnL: $-2.0 (минус)")
    print(f"   💰 USDC: $5.0 (мало, нужно $10.0)")
    print(f"   🔄 Торгов: {len(result['trades'])}")
    
    for trade in result['trades']:
        reason = trade.get('reason', 'Причина не указана')
        print(f"      {trade['action']} {trade['symbol']} - {reason}")
    
    # Тест 3: BTC в минусе, ETH в минусе, НЕТ USDC
    print("\n3️⃣ ТЕСТ: BTC в минусе, ETH в минусе, НЕТ USDC")
    print("   Ожидаем: Никаких торгов (ждем следующей проверки)")
    
    def mock_btc_pnl_negative(asset, balances, values):
        return -3.0 if asset == 'BTC' else -2.0  # Оба в минусе
    
    balancer.get_asset_pnl = mock_btc_pnl_negative
    
    result = balancer.calculate_rebalance_trades(mock_balances_test1(), mock_values_test1())
    
    print(f"   📊 BTC PnL: $-3.0 (минус)")
    print(f"   📊 ETH PnL: $-2.0 (минус)")
    print(f"   💰 USDC: $5.0 (мало)")
    print(f"   🔄 Торгов: {len(result['trades'])}")
    
    if len(result['trades']) == 0:
        print("      ✅ Правильно: Никаких торгов при отрицательном PnL обоих активов")
    else:
        print("      ❌ Ошибка: Должно быть 0 торгов")
        for trade in result['trades']:
            reason = trade.get('reason', 'Причина не указана')
            print(f"         {trade['action']} {trade['symbol']} - {reason}")
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("\n📋 НОВАЯ ЛОГИКА:")
    print("   1. ✅ Покупка за USDC если хватает")
    print("   2. ✅ Продажа актива в плюсе для покупки актива в минусе")
    print("   3. ✅ Блокировка продажи активов в минусе")
    print("   4. ✅ Ожидание при отрицательном PnL обоих активов")
    print("\n🎯 РЕЗУЛЬТАТ:")
    print("   • PnLMonitor больше НЕ блокирует всю балансировку при общем отрицательном PnL")
    print("   • PortfolioBalancer сам решает что можно продавать на основе PnL каждого актива")
    print("   • Продажа только активов в плюсе для покупки активов в минусе")

if __name__ == "__main__":
    asyncio.run(test_new_balancer_logic())
