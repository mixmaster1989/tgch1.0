#!/usr/bin/env python3
"""
Тест новых уведомлений с анти-хайп фильтром и общей стоимостью портфеля
"""

from balance_monitor import BalanceMonitor
from alt_monitor import AltsMonitor
from pnl_monitor import PnLMonitor

def test_balance_monitor_notifications():
    print("💰 ТЕСТ УВЕДОМЛЕНИЙ BALANCE MONITOR")
    print("="*50)
    
    monitor = BalanceMonitor()
    
    # Тестируем расчет покупки с новыми уведомлениями
    available_amount = 25.0
    
    print(f"💰 Тестируем покупку на ${available_amount}")
    
    # Получаем план покупки
    purchase_plan = monitor.calculate_purchase_amounts(available_amount, 'USDC')
    
    if purchase_plan:
        # Создаем тестовый результат
        from datetime import datetime
        test_results = {
            'success': True,
            'timestamp': datetime.now(),
            'available_usdc': available_amount,
            'currency': 'USDC',
            'purchases': [],
            'total_spent': 0.0
        }
        
        for symbol, data in purchase_plan.items():
            test_results['purchases'].append({
                'symbol': symbol,
                'quantity': data['quantity'],
                'usdc_amount': data['amount'],
                'amount': data['amount'],
                'currency': data['currency'],
                'price': data['price'],
                'limit_price': data['price'] * 0.9995,
                'order_id': 'TEST123456',
                'is_maker': True,
                'orderbook': {'best_bid': data['price'] * 0.999, 'best_ask': data['price'] * 1.001, 'spread_percent': 0.2},
                'filter_reason': data.get('filter_reason', 'normal'),
                'filter_multiplier': data.get('filter_multiplier', 1.0)
            })
            test_results['total_spent'] += data['amount']
        
        # Форматируем и показываем отчет
        report = monitor.format_purchase_report(test_results)
        print("\n📱 ОТЧЕТ О ПОКУПКЕ:")
        print(report.replace('<b>', '').replace('</b>', '').replace('<code>', '').replace('</code>', ''))
    else:
        print("❌ Нет плана покупки")

def test_alt_monitor_notifications():
    print("\n🧩 ТЕСТ УВЕДОМЛЕНИЙ ALT MONITOR")
    print("="*50)
    
    alt_monitor = AltsMonitor()
    
    # Тестируем отчет альтов
    alt_monitor.send_status_report_once()
    print("✅ Отчет альтов отправлен")

def test_pnl_monitor_notifications():
    print("\n📊 ТЕСТ УВЕДОМЛЕНИЙ PNL MONITOR")
    print("="*50)
    
    pnl_monitor = PnLMonitor()
    
    # Принудительно отправляем сводку
    pnl_monitor.last_summary_time = 0  # Сбрасываем таймер
    pnl_monitor.check_pnl_and_sell()
    print("✅ Сводка PnL отправлена")

def main():
    print("🧪 ТЕСТИРОВАНИЕ НОВЫХ УВЕДОМЛЕНИЙ")
    print("="*80)
    
    try:
        # Тест уведомлений balance monitor
        test_balance_monitor_notifications()
        
        # Тест уведомлений alt monitor  
        test_alt_monitor_notifications()
        
        # Тест уведомлений pnl monitor
        test_pnl_monitor_notifications()
        
        print("\n" + "="*80)
        print("✅ ТЕСТИРОВАНИЕ УВЕДОМЛЕНИЙ ЗАВЕРШЕНО")
        print("\n📱 НОВЫЕ ВОЗМОЖНОСТИ:")
        print("   🚀 Немедленные уведомления о покупках/продажах")
        print("   🛡️ Информация об анти-хайп фильтре в отчетах")
        print("   💰 Общая стоимость портфеля в сводках")
        print("   ⏰ Периодические сводки каждые 5 минут")
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ТЕСТИРОВАНИЯ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()