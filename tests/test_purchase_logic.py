#!/usr/bin/env python3
"""
Тест новой логики расчета суммы покупки
"""

def test_purchase_amount_calculation():
    """Тестируем новую логику расчета суммы покупки"""
    
    print("🧪 ТЕСТ НОВОЙ ЛОГИКИ РАСЧЕТА СУММЫ ПОКУПКИ")
    print("=" * 50)
    
    # Тестовые балансы
    test_balances = [5.0, 10.0, 15.65, 20.0, 30.0, 50.0, 100.0]
    
    for balance in test_balances:
        print(f"\n💰 Баланс: ${balance:.2f}")
        
        # Старая логика (30% от баланса)
        old_amount = min(balance * 0.3, 50.0)
        
        # Новая логика
        if balance < 20.0:
            new_amount = balance * 0.6
        else:
            new_amount = min(balance * 0.3, 50.0)
        
        # Обеспечиваем минимальную сумму $5
        if new_amount < 5.0 and balance >= 5.0:
            new_amount = 5.0
        
        print(f"   Старая логика: ${old_amount:.2f}")
        print(f"   Новая логика:  ${new_amount:.2f}")
        
        if new_amount >= 5.0:
            print(f"   ✅ Может совершить покупку")
        else:
            print(f"   ❌ Недостаточно для покупки")
    
    print("\n" + "=" * 50)
    print("📊 АНАЛИЗ РЕЗУЛЬТАТОВ:")
    print("=" * 50)
    
    # Анализ для баланса $15.65 (как в вашем случае)
    balance_15_65 = 15.65
    
    old_amount = min(balance_15_65 * 0.3, 50.0)  # $4.69
    new_amount = balance_15_65 * 0.6  # $9.39
    
    print(f"💰 Баланс $15.65:")
    print(f"   Старая логика: ${old_amount:.2f} (❌ меньше $5)")
    print(f"   Новая логика:  ${new_amount:.2f} (✅ больше $5)")
    print(f"   Улучшение: +${new_amount - old_amount:.2f}")

if __name__ == "__main__":
    test_purchase_amount_calculation()
