#!/usr/bin/env python3
"""
Тест системы автоматических покупок BTC/ETH
"""

import asyncio
from balance_monitor import BalanceMonitor
from auto_purchase_config import get_config

def test_balance_monitor():
    """Тест монитора баланса"""
    print("🧪 ТЕСТ МОНИТОРА БАЛАНСА")
    print("=" * 50)
    
    try:
        # Создаем монитор
        monitor = BalanceMonitor()
        print("✅ Монитор создан")
        
        # Получаем текущий баланс
        balance = monitor.get_usdt_balance()
        print(f"💰 Текущий баланс USDT: ${balance:.2f}")
        
        # Получаем цены BTC/ETH
        btc_price = monitor.get_current_price('BTCUSDT')
        eth_price = monitor.get_current_price('ETHUSDT')
        
        if btc_price:
            print(f"📈 Цена BTC: ${btc_price:.2f}")
        else:
            print("❌ Не удалось получить цену BTC")
            
        if eth_price:
            print(f"📈 Цена ETH: ${eth_price:.2f}")
        else:
            print("❌ Не удалось получить цену ETH")
        
        # Тестируем расчет покупки
        if balance >= monitor.min_balance_threshold:
            print(f"\n📊 Тест расчета покупки на ${balance:.2f}:")
            purchase_plan = monitor.calculate_purchase_amounts(balance)
            
            if purchase_plan:
                for symbol, data in purchase_plan.items():
                    print(f"   {symbol}:")
                    print(f"     💰 Сумма: ${data['usdt_amount']:.2f}")
                    print(f"     📈 Количество: {data['quantity']:.6f}")
                    print(f"     💵 Цена: ${data['price']:.4f}")
            else:
                print("❌ Не удалось рассчитать план покупки")
        else:
            print(f"⚠️ Баланс слишком мал для покупки (${balance:.2f} < ${monitor.min_balance_threshold})")
        
        # Тестируем условия покупки
        print(f"\n🔍 Проверка условий покупки:")
        print(f"   Минимальный баланс: ${monitor.min_balance_threshold}")
        print(f"   Максимальная покупка: ${monitor.max_purchase_amount}")
        print(f"   Интервал проверки: {monitor.balance_check_interval} сек")
        print(f"   Мин. интервал покупок: {monitor.min_purchase_interval} сек")
        print(f"   BTC: {monitor.btc_allocation*100}% | ETH: {monitor.eth_allocation*100}%")
        
        can_purchase = monitor.can_make_purchase()
        print(f"   Можно покупать: {'✅' if can_purchase else '❌'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка теста: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration():
    """Тест конфигурации"""
    print("\n🧪 ТЕСТ КОНФИГУРАЦИИ")
    print("=" * 50)
    
    try:
        config = get_config()
        print("✅ Конфигурация загружена")
        
        # Проверяем основные разделы
        sections = ['balance_monitor', 'allocation', 'orders', 'safety', 'notifications']
        for section in sections:
            if section in config:
                print(f"✅ {section}: OK")
            else:
                print(f"❌ {section}: ОТСУТСТВУЕТ")
        
        # Показываем ключевые настройки
        balance_config = config['balance_monitor']
        allocation_config = config['allocation']
        
        print(f"\n📊 Ключевые настройки:")
        print(f"   Минимальный баланс: ${balance_config['min_balance_threshold']}")
        print(f"   Максимальная покупка: ${balance_config['max_purchase_amount']}")
        print(f"   BTC: {allocation_config['btc_allocation']*100}%")
        print(f"   ETH: {allocation_config['eth_allocation']*100}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка конфигурации: {e}")
        return False

async def test_purchase_simulation():
    """Тест симуляции покупки"""
    print("\n🧪 ТЕСТ СИМУЛЯЦИИ ПОКУПКИ")
    print("=" * 50)
    
    try:
        monitor = BalanceMonitor()
        
        # Симулируем баланс для теста
        test_balance = 50.0  # $50
        print(f"💰 Тестовый баланс: ${test_balance}")
        
        # Рассчитываем план покупки
        purchase_plan = monitor.calculate_purchase_amounts(test_balance)
        
        if purchase_plan:
            print("📋 План покупки:")
            total_spent = 0
            
            for symbol, data in purchase_plan.items():
                print(f"   {symbol}:")
                print(f"     💰 Сумма: ${data['usdt_amount']:.2f}")
                print(f"     📈 Количество: {data['quantity']:.6f}")
                print(f"     💵 Цена: ${data['price']:.4f}")
                total_spent += data['usdt_amount']
            
            print(f"\n💸 Общая сумма: ${total_spent:.2f}")
            
            # Спрашиваем пользователя о симуляции
            response = input("\n❓ Симулировать покупку? (y/n): ")
            if response.lower() == 'y':
                print("🔄 Симуляция покупки...")
                
                # Симулируем покупку (без реальных ордеров)
                results = {
                    'success': True,
                    'timestamp': asyncio.get_event_loop().time(),
                    'available_usdt': test_balance,
                    'purchases': [],
                    'total_spent': total_spent
                }
                
                for symbol, data in purchase_plan.items():
                    results['purchases'].append({
                        'symbol': symbol,
                        'quantity': data['quantity'],
                        'usdt_amount': data['usdt_amount'],
                        'price': data['price'],
                        'order_id': f'SIM_{symbol}_{int(asyncio.get_event_loop().time())}'
                    })
                
                # Форматируем отчет
                report = monitor.format_purchase_report(results)
                print("\n📋 ОТЧЕТ О ПОКУПКЕ:")
                print("-" * 50)
                print(report)
                
                # Спрашиваем об отправке в Telegram
                telegram_response = input("\n❓ Отправить отчет в Telegram? (y/n): ")
                if telegram_response.lower() == 'y':
                    result = monitor.send_telegram_message(report)
                    if result and result.get('ok'):
                        print("✅ Отчет отправлен в Telegram")
                    else:
                        print("❌ Ошибка отправки в Telegram")
            else:
                print("⏭️ Симуляция отменена")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка симуляции: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Главная функция тестирования"""
    print("🚀 ТЕСТ СИСТЕМЫ АВТОМАТИЧЕСКИХ ПОКУПОК")
    print("=" * 60)
    
    # Тест 1: Конфигурация
    config_ok = test_configuration()
    
    # Тест 2: Монитор баланса
    monitor_ok = test_balance_monitor()
    
    # Тест 3: Симуляция покупки
    simulation_ok = await test_purchase_simulation()
    
    # Итоги
    print("\n" + "=" * 60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    print("=" * 60)
    print(f"Конфигурация: {'✅' if config_ok else '❌'}")
    print(f"Монитор баланса: {'✅' if monitor_ok else '❌'}")
    print(f"Симуляция покупки: {'✅' if simulation_ok else '❌'}")
    
    if all([config_ok, monitor_ok, simulation_ok]):
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к работе.")
        print("\n🚀 Для запуска используйте:")
        print("   python3 run_auto_purchase.py start")
    else:
        print("\n⚠️ Некоторые тесты не пройдены. Проверьте настройки.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 