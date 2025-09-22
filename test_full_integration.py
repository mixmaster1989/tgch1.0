#!/usr/bin/env python3
"""
Тестовый скрипт для проверки полной интеграции
"""

import asyncio
from active_50_50_balancer import Active5050Balancer
from market_scanner import MarketScanner
from alt_monitor import AltsMonitor
from portfolio_balancer import PortfolioBalancer

async def test_full_integration():
    """Тестируем полную интеграцию всех компонентов"""
    print("🧪 ТЕСТИРОВАНИЕ ПОЛНОЙ ИНТЕГРАЦИИ")
    print("=" * 50)
    
    # 1. Тестируем балансировщик с конвертацией USDT → USDC
    print("\n1️⃣ ТЕСТИРУЕМ БАЛАНСИРОВЩИК С КОНВЕРТАЦИЕЙ:")
    balancer = Active5050Balancer()
    
    # Проверяем что BTC-ETH балансировщик инициализирован
    if hasattr(balancer, 'btc_eth_balancer'):
        print("   ✅ BTC-ETH балансировщик инициализирован")
    else:
        print("   ❌ BTC-ETH балансировщик НЕ инициализирован")
    
    # 2. Тестируем market_scanner с уведомлениями
    print("\n2️⃣ ТЕСТИРУЕМ MARKET_SCANNER С УВЕДОМЛЕНИЯМИ:")
    scanner = MarketScanner()
    
    if hasattr(scanner, 'balancer'):
        print("   ✅ Балансировщик инициализирован в market_scanner")
    else:
        print("   ❌ Балансировщик НЕ инициализирован в market_scanner")
    
    # 3. Тестируем alt_monitor с уведомлениями
    print("\n3️⃣ ТЕСТИРУЕМ ALT_MONITOR С УВЕДОМЛЕНИЯМИ:")
    monitor = AltsMonitor()
    
    if hasattr(monitor, 'balancer'):
        print("   ✅ Балансировщик инициализирован в alt_monitor")
    else:
        print("   ❌ Балансировщик НЕ инициализирован в alt_monitor")
    
    # 4. Тестируем PortfolioBalancer
    print("\n4️⃣ ТЕСТИРУЕМ PORTFOLIO_BALANCER:")
    portfolio_balancer = PortfolioBalancer()
    
    print(f"   📊 Целевые пропорции: BTC {portfolio_balancer.target_btc_ratio*100:.0f}% / ETH {portfolio_balancer.target_eth_ratio*100:.0f}%")
    print(f"   📈 Порог балансировки: {portfolio_balancer.rebalance_threshold*100:.0f}%")
    print(f"   💰 Минимальная сумма: ${portfolio_balancer.min_rebalance_amount}")
    
    # 5. Тестируем сценарий перевеса альтов
    print("\n5️⃣ ТЕСТИРУЕМ СЦЕНАРИЙ ПЕРЕВЕСА АЛЬТОВ:")
    
    # Симулируем перевес альтов
    def mock_portfolio_alts_overweight():
        return {
            'alts_value': 600.0,      # 60% от портфеля
            'btceth_value': 400.0,    # 40% от портфеля  
            'btceth_value_usdt': 400.0,
            'total_value': 1000.0,
            'usdc_usdt_rate': 1.0
        }
    
    balancer.get_portfolio_values = mock_portfolio_alts_overweight
    balancer.get_usdc_balance = lambda: 100.0
    
    # Тестируем разрешение на покупку альтов
    permission = balancer.check_purchase_permission(50.0, "ALTS")
    
    print(f"   📊 Альты: 60.0% (перевес!)")
    print(f"   📊 BTC/ETH: 40.0%")
    print(f"   🚫 Разрешено: {permission['allowed']}")
    print(f"   📝 Причина: {permission['reason']}")
    
    if not permission['allowed']:
        print("   ✅ ПРАВИЛЬНО: Покупка альтов заблокирована при перевесе")
        
        # Тестируем план балансировки
        balance_plan = balancer.calculate_balance_needed()
        if balance_plan and balance_plan['action'] == 'BUY_BTCETH_USDC':
            print("   ✅ ПРАВИЛЬНО: Балансировщик планирует купить BTC/ETH")
            print(f"   💰 Сумма: ${balance_plan['amount']:.2f}")
        else:
            print("   ❌ ОШИБКА: Балансировщик не планирует покупку BTC/ETH")
    
    print("\n" + "=" * 50)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("\n📋 ИТОГОВАЯ ЛОГИКА:")
    print("   1. Закупщики альтов запрашивают разрешение у балансировщика")
    print("   2. При перевесе альтов (>50%) - покупка БЛОКИРУЕТСЯ")
    print("   3. Балансировщик конвертирует USDT → USDC")
    print("   4. Балансировщик покупает BTC/ETH за USDC")
    print("   5. Запускается BTC-ETH балансировщик (60/40)")
    print("   6. Все действия с уведомлениями в Telegram")

if __name__ == "__main__":
    asyncio.run(test_full_integration())
