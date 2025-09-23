from active_50_50_balancer import Active5050Balancer

balancer = Active5050Balancer()

# Проверяем балансы
usdc = balancer.get_usdc_balance()
usdt = balancer.get_usdt_balance()

print('💰 ТЕКУЩИЕ БАЛАНСЫ:')
print(f'   USDC: ${usdc:.2f}')
print(f'   USDT: ${usdt:.2f}')
print(f'   Всего стейблкоинов: ${usdc + usdt:.2f}')
print()

# Проверяем возможность балансировки
if usdc >= balancer.min_balance_threshold:
    print(f'✅ USDC достаточно для балансировки (${usdc:.2f} >= ${balancer.min_balance_threshold:.2f})')
    
    # Рассчитываем безопасную сумму
    safe_amount = balancer.calculate_safe_operation_amount(usdc)
    print(f'🛡️ Безопасная сумма для операции: ${safe_amount:.2f} USDC')
    
    if safe_amount >= 5.0:
        print('🎯 БАЛАНСИРОВКА ВОЗМОЖНА!')
    else:
        print('❌ Сумма слишком мала для балансировки')
else:
    print(f'❌ USDC недостаточно (${usdc:.2f} < ${balancer.min_balance_threshold:.2f})')
    print('💡 Нужна конвертация USDT → USDC')
    
    # Проверяем, можем ли мы конвертировать
    if usdt >= 10.0:
        print(f'✅ USDT достаточно для конвертации (${usdt:.2f})')
        print('🔄 Балансировщик сможет автоматически конвертировать при следующей операции')
    else:
        print(f'❌ USDT тоже недостаточно (${usdt:.2f})')
