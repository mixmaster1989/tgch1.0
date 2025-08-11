#!/usr/bin/env python3
"""
Тест балансировщика стейблкоинов
"""

from stablecoin_balancer import StablecoinBalancer

def main():
    print("🧪 Тестирование балансировщика стейблкоинов...")
    
    balancer = StablecoinBalancer()
    
    # Получаем текущие балансы
    balances = balancer.get_stablecoin_balances()
    print(f"💰 Текущие балансы:")
    print(f"   USDT: ${balances['USDT']:.2f}")
    print(f"   USDC: ${balances['USDC']:.2f}")
    print(f"   Всего: ${sum(balances.values()):.2f}")
    
    # Рассчитываем балансировку
    conversion = balancer.calculate_rebalance(balances['USDT'], balances['USDC'])
    
    if conversion:
        print(f"\n🔄 Нужна балансировка:")
        print(f"   {conversion['from']} → {conversion['to']}")
        print(f"   Сумма: ${conversion['amount']:.2f}")
        print(f"   Символ: {conversion['symbol']}")
        print(f"   Операция: {conversion['side']}")
        
        # Отправляем отчет без выполнения
        result = {'success': False, 'error': 'Тестовый режим'}
        balancer.send_balance_report(balances, conversion, result)
    else:
        print(f"\n✅ Балансировка не нужна")
        print(f"   Разница меньше ${balancer.min_balance_diff}")

if __name__ == "__main__":
    main()