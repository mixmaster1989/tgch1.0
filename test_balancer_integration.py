#!/usr/bin/env python3
"""
Тестовый скрипт для проверки интеграции балансировщика с закупщиками альтов
"""

import asyncio
from active_50_50_balancer import Active5050Balancer
from market_scanner import MarketScanner
from alt_monitor import AltsMonitor

async def test_balancer_permission():
    """Тестируем метод проверки разрешения балансировщика"""
    print("🧪 Тестируем метод проверки разрешения балансировщика...")
    
    balancer = Active5050Balancer()
    
    # Тестируем с разными суммами
    test_amounts = [10.0, 50.0, 100.0]
    
    for amount in test_amounts:
        print(f"\n💰 Тестируем сумму: ${amount}")
        permission = balancer.check_purchase_permission(amount, "ALTS")
        
        print(f"   Разрешено: {permission['allowed']}")
        print(f"   Причина: {permission['reason']}")
        print(f"   Альты: {permission['current_alts_ratio']*100:.1f}%")
        print(f"   BTC/ETH: {permission['current_btceth_ratio']*100:.1f}%")

def test_market_scanner_integration():
    """Тестируем интеграцию с market_scanner"""
    print("\n🧪 Тестируем интеграцию с market_scanner...")
    
    scanner = MarketScanner()
    
    # Проверяем что балансировщик инициализирован
    if hasattr(scanner, 'balancer'):
        print("   ✅ Балансировщик инициализирован в market_scanner")
    else:
        print("   ❌ Балансировщик НЕ инициализирован в market_scanner")

def test_alt_monitor_integration():
    """Тестируем интеграцию с alt_monitor"""
    print("\n🧪 Тестируем интеграцию с alt_monitor...")
    
    monitor = AltsMonitor()
    
    # Проверяем что балансировщик инициализирован
    if hasattr(monitor, 'balancer'):
        print("   ✅ Балансировщик инициализирован в alt_monitor")
    else:
        print("   ❌ Балансировщик НЕ инициализирован в alt_monitor")

async def main():
    """Главная функция тестирования"""
    print("�� ТЕСТИРОВАНИЕ ИНТЕГРАЦИИ БАЛАНСИРОВЩИКА С ЗАКУПЩИКАМИ АЛЬТОВ")
    print("=" * 70)
    
    # Тестируем метод проверки разрешения
    await test_balancer_permission()
    
    # Тестируем интеграцию с market_scanner
    test_market_scanner_integration()
    
    # Тестируем интеграцию с alt_monitor
    test_alt_monitor_integration()
    
    print("\n" + "=" * 70)
    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(main())
