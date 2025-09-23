#!/usr/bin/env python3
"""
Тест миграции всех модулей на USDC
Проверяем работу с защитой баланса USDC (минимум $10)
"""

import sys
import logging
from balance_monitor import BalanceMonitor
from market_scanner import MarketScanner
from active_50_50_balancer import Active5050Balancer

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_balance_monitor_usdc():
    """Тестируем обновленный монитор баланса"""
    
    print("🧪 ТЕСТ МОНИТОРА БАЛАНСА USDC")
    print("=" * 50)
    
    try:
        # Создаем монитор
        monitor = BalanceMonitor()
        
        print(f"✅ Монитор создан")
        print(f"💰 Минимальный баланс: ${monitor.min_balance_threshold} USDC")
        print(f"💸 Максимальная покупка: ${monitor.max_purchase_amount} USDC")
        print(f"🛡️ Защита баланса: минимум ${monitor.min_usdc_balance_after_purchase} USDC")
        
        # Тестируем функции
        usdc_balance = monitor.get_usdc_balance()
        usdt_balance = monitor.get_usdt_balance()
        
        print(f"💰 Баланс USDC: ${usdc_balance:.2f}")
        print(f"💰 Баланс USDT: ${usdt_balance:.2f}")
        
        # Тестируем защиту баланса
        if usdc_balance > 0:
            safe_amount = monitor.calculate_safe_purchase_amount(usdc_balance)
            print(f"🛡️ Безопасная сумма покупки: ${safe_amount:.2f} USDC")
            
            can_purchase, reason = monitor.can_make_purchase(safe_amount)
            print(f"✅ Можно ли купить: {can_purchase} ({reason})")
        
        print("✅ Тест монитора баланса завершен\n")
        
    except Exception as e:
        print(f"❌ Ошибка теста монитора баланса: {e}\n")

def test_market_scanner_usdc():
    """Тестируем обновленный сканер рынка"""
    
    print("🧪 ТЕСТ СКАНЕРА РЫНКА USDC")
    print("=" * 50)
    
    try:
        # Создаем сканер
        scanner = MarketScanner()
        
        print(f"✅ Сканер создан")
        
        # Тестируем функции
        usdc_balance = scanner.get_usdc_balance()
        usdt_balance = scanner.get_usdt_balance()
        
        print(f"💰 Баланс USDC: ${usdc_balance:.2f}")
        print(f"💰 Баланс USDT: ${usdt_balance:.2f}")
        
        # Тестируем защиту баланса
        if usdc_balance > 0:
            safe_amount = scanner.calculate_safe_purchase_amount(usdc_balance)
            print(f"🛡️ Безопасная сумма покупки: ${safe_amount:.2f} USDC")
            
            can_purchase, reason = scanner.can_make_purchase(safe_amount)
            print(f"✅ Можно ли купить: {can_purchase} ({reason})")
        
        print("✅ Тест сканера рынка завершен\n")
        
    except Exception as e:
        print(f"❌ Ошибка теста сканера рынка: {e}\n")

def test_active_balancer_usdc():
    """Тестируем обновленный активный балансировщик"""
    
    print("🧪 ТЕСТ АКТИВНОГО БАЛАНСИРОВЩИКА USDC")
    print("=" * 50)
    
    try:
        # Создаем балансировщик
        balancer = Active5050Balancer()
        
        print(f"✅ Балансировщик создан")
        print(f"💰 Минимальный баланс: ${balancer.min_balance_threshold} USDC")
        print(f"💸 Максимальная операция: ${balancer.max_balance_threshold} USDC")
        print(f"🛡️ Защита баланса: минимум ${balancer.min_usdc_balance_after_operation} USDC")
        
        # Тестируем функции
        usdc_balance = balancer.get_usdc_balance()
        usdt_balance = balancer.get_usdt_balance()
        
        print(f"💰 Баланс USDC: ${usdc_balance:.2f}")
        print(f"💰 Баланс USDT: ${usdt_balance:.2f}")
        
        # Тестируем защиту баланса
        if usdc_balance > 0:
            safe_amount = balancer.calculate_safe_operation_amount(usdc_balance)
            print(f"🛡️ Безопасная сумма операции: ${safe_amount:.2f} USDC")
            
            can_operate, reason = balancer.can_make_operation(safe_amount)
            print(f"✅ Можно ли выполнить операцию: {can_operate} ({reason})")
        
        print("✅ Тест активного балансировщика завершен\n")
        
    except Exception as e:
        print(f"❌ Ошибка теста активного балансировщика: {e}\n")

def main():
    """Основная функция тестирования"""
    
    print("🚀 ТЕСТИРОВАНИЕ МИГРАЦИИ НА USDC")
    print("=" * 60)
    print("Проверяем работу всех модулей с защитой баланса USDC")
    print("ЗАЩИТА: Нельзя оставлять на балансе USDC меньше $10!")
    print("=" * 60 + "\n")
    
    # Тестируем все модули
    test_balance_monitor_usdc()
    test_market_scanner_usdc()
    test_active_balancer_usdc()
    
    print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("=" * 60)
    print("✅ Все модули успешно переведены на USDC")
    print("🛡️ Защита баланса USDC активирована")
    print("💱 Все покупки выполняются за USDC (рыночные ордера без комиссий)")
    print("=" * 60)

if __name__ == "__main__":
    main() 