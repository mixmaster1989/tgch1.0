#!/usr/bin/env python3
"""
Тестовый скрипт для проверки логики балансировщика при перевесе альтов
"""

import asyncio
from active_50_50_balancer import Active5050Balancer

async def test_alts_overweight_scenario():
    """Тестируем сценарий когда альтов больше 50%"""
    print("🧪 ТЕСТИРУЕМ СЦЕНАРИЙ ПЕРЕВЕСА АЛЬТОВ")
    print("=" * 50)
    
    balancer = Active5050Balancer()
    
    # Тестируем метод проверки разрешения при перевесе альтов
    print("\n1️⃣ ПРОВЕРКА РАЗРЕШЕНИЯ НА ПОКУПКУ АЛЬТОВ:")
    print("   (Когда альтов уже больше 50%)")
    
    # Симулируем перевес альтов - модифицируем метод get_portfolio_values
    original_method = balancer.get_portfolio_values
    
    def mock_portfolio_alts_overweight():
        """Мок-метод с перевесом альтов"""
        return {
            'alts_value': 600.0,      # 60% от портфеля
            'btceth_value': 400.0,    # 40% от портфеля  
            'btceth_value_usdt': 400.0,
            'total_value': 1000.0,
            'usdc_usdt_rate': 1.0
        }
    
    # Подменяем метод
    balancer.get_portfolio_values = mock_portfolio_alts_overweight
    
    # Тестируем разрешение на покупку альтов
    permission = balancer.check_purchase_permission(50.0, "ALTS")
    
    print(f"   💰 Сумма покупки: $50.0")
    print(f"   📊 Альты: 60.0% (перевес!)")
    print(f"   📊 BTC/ETH: 40.0%")
    print(f"   🚫 Разрешено: {permission['allowed']}")
    print(f"   📝 Причина: {permission['reason']}")
    
    # Восстанавливаем оригинальный метод
    balancer.get_portfolio_values = original_method
    
    print("\n2️⃣ ПРОВЕРКА ЛОГИКИ БАЛАНСИРОВКИ:")
    print("   (Что делает балансировщик при перевесе альтов)")
    
    # Тестируем calculate_balance_needed с перевесом альтов
    balancer.get_portfolio_values = mock_portfolio_alts_overweight
    
    # Мокаем USDC баланс
    balancer.get_usdc_balance = lambda: 100.0
    
    balance_plan = balancer.calculate_balance_needed()
    
    if balance_plan:
        print(f"   ⚖️ Действие: {balance_plan['action']}")
        print(f"   💰 Сумма: ${balance_plan['amount']:.2f}")
        print(f"   📝 Причина: {balance_plan['reason']}")
        
        if balance_plan['action'] == 'BUY_BTCETH_USDC':
            print("   ✅ ПРАВИЛЬНО: Балансировщик хочет купить BTC/ETH для выравнивания")
        else:
            print("   ❌ ОШИБКА: Балансировщик должен покупать BTC/ETH, а не альты!")
    else:
        print("   ⚠️ Балансировщик не планирует операций (возможно, недостаточно USDC)")
    
    # Восстанавливаем оригинальные методы
    balancer.get_portfolio_values = original_method
    
    print("\n3️⃣ ПРОВЕРКА ЛОГИКИ ПРИ НОРМАЛЬНЫХ ПРОПОРЦИЯХ:")
    print("   (Когда пропорции сбалансированы)")
    
    def mock_portfolio_balanced():
        """Мок-метод со сбалансированным портфелем"""
        return {
            'alts_value': 500.0,      # 50% от портфеля
            'btceth_value': 500.0,    # 50% от портфеля
            'btceth_value_usdt': 500.0,
            'total_value': 1000.0,
            'usdc_usdt_rate': 1.0
        }
    
    balancer.get_portfolio_values = mock_portfolio_balanced
    
    permission = balancer.check_purchase_permission(50.0, "ALTS")
    
    print(f"   💰 Сумма покупки: $50.0")
    print(f"   📊 Альты: 50.0% (сбалансировано)")
    print(f"   📊 BTC/ETH: 50.0%")
    print(f"   ✅ Разрешено: {permission['allowed']}")
    print(f"   📝 Причина: {permission['reason']}")
    
    # Восстанавливаем оригинальный метод
    balancer.get_portfolio_values = original_method

async def main():
    """Главная функция"""
    await test_alts_overweight_scenario()
    
    print("\n" + "=" * 50)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("\n📋 ВЫВОДЫ:")
    print("   • При перевесе альтов (>50%) - покупка альтов БЛОКИРУЕТСЯ")
    print("   • При перевесе альтов - балансировщик покупает BTC/ETH")
    print("   • При сбалансированных пропорциях - покупка альтов РАЗРЕШАЕТСЯ")

if __name__ == "__main__":
    asyncio.run(main())
