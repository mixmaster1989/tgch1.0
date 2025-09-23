#!/usr/bin/env python3
"""
Немедленная балансировка USDT/USDC
"""

from stablecoin_balancer import StablecoinBalancer

def main():
    print("⚖️ Немедленная балансировка USDT/USDC...")
    
    balancer = StablecoinBalancer()
    balancer.min_balance_diff = 5.0  # Снижаем порог
    balancer.last_balance_time = 0   # Сбрасываем таймер
    
    # Получаем балансы
    balances = balancer.get_stablecoin_balances()
    print(f"💰 ДО: USDT=${balances['USDT']:.2f}, USDC=${balances['USDC']:.2f}")
    
    # Рассчитываем конвертацию
    conversion = balancer.calculate_rebalance(balances['USDT'], balances['USDC'])
    
    if conversion:
        print(f"🔄 Конвертируем: {conversion['from']} → {conversion['to']}, ${conversion['amount']:.2f}")
        
        # Выполняем конвертацию
        result = balancer.execute_conversion(conversion)
        
        if result['success']:
            print(f"✅ Успешно! Ордер: {result['order_id']}")
            
            # Проверяем новые балансы
            new_balances = balancer.get_stablecoin_balances()
            print(f"💰 ПОСЛЕ: USDT=${new_balances['USDT']:.2f}, USDC=${new_balances['USDC']:.2f}")
            
            # Отправляем отчет
            balancer.send_balance_report(balances, conversion, result)
        else:
            print(f"❌ Ошибка: {result['error']}")
    else:
        print("✅ Балансировка не нужна")

if __name__ == "__main__":
    main()