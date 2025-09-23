#!/usr/bin/env python3
"""
Принудительный запуск балансировки стейблкоинов
"""

from stablecoin_balancer import StablecoinBalancer

def main():
    print("⚖️ Принудительная балансировка USDT/USDC...")
    
    balancer = StablecoinBalancer()
    balancer.min_balance_diff = 5.0  # Снижаем порог для теста
    
    # Принудительно запускаем проверку
    balancer.check_and_balance()
    
    print("✅ Проверка завершена")

if __name__ == "__main__":
    main()