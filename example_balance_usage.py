#!/usr/bin/env python3
"""
Пример использования функций для получения баланса USDT и USDC
"""

from balance_utils import get_usdt_usdc_balance, get_balance_dict, get_free_balance, check_balance_sufficient
from datetime import datetime

def main():
    """Пример использования функций баланса"""
    print("🔍 ПРИМЕР ИСПОЛЬЗОВАНИЯ ФУНКЦИЙ БАЛАНСА")
    print("=" * 60)
    print(f"Время: {datetime.now()}")
    print()
    
    # 1. Получение общего баланса (включая заблокированные средства)
    print("1️⃣ Получение общего баланса:")
    usdt_total, usdc_total = get_usdt_usdc_balance()
    print(f"   USDT: {usdt_total:.8f}")
    print(f"   USDC: {usdc_total:.8f}")
    print()
    
    # 2. Получение свободного баланса
    print("2️⃣ Получение свободного баланса:")
    usdt_free, usdc_free = get_free_balance()
    print(f"   USDT (свободно): {usdt_free:.8f}")
    print(f"   USDC (свободно): {usdc_free:.8f}")
    print()
    
    # 3. Получение баланса в виде словаря
    print("3️⃣ Получение баланса в виде словаря:")
    balance_dict = get_balance_dict()
    print(f"   {balance_dict}")
    print()
    
    # 4. Проверка достаточности баланса
    print("4️⃣ Проверка достаточности баланса:")
    required_usdt = 10.0
    required_usdc = 5.0
    
    is_sufficient = check_balance_sufficient(required_usdt, required_usdc)
    print(f"   Требуется: USDT={required_usdt}, USDC={required_usdc}")
    print(f"   Доступно: USDT={usdt_free}, USDC={usdc_free}")
    print(f"   Достаточно: {'✅ Да' if is_sufficient else '❌ Нет'}")
    print()
    
    # 5. Расчет заблокированных средств
    print("5️⃣ Заблокированные средства:")
    usdt_locked = usdt_total - usdt_free
    usdc_locked = usdc_total - usdc_free
    print(f"   USDT заблокировано: {usdt_locked:.8f}")
    print(f"   USDC заблокировано: {usdc_locked:.8f}")
    print()
    
    print("=" * 60)
    print("✅ Пример завершен!")

if __name__ == "__main__":
    main() 