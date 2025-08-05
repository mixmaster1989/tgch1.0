#!/usr/bin/env python3
"""
Запуск торгового процессора с симуляцией
"""

from trading_engine import TradingEngine
from datetime import datetime

def run_simulation():
    print("=== ЗАПУСК ТОРГОВОГО ПРОЦЕССОРА ===")
    print(f"Время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Режим: СИМУЛЯЦИЯ (деньги не тратятся)")
    print("=" * 50)
    
    # Создаем торговый движок в режиме симуляции
    engine = TradingEngine(simulation_mode=True)
    
    try:
        # Запускаем полный торговый цикл
        results = engine.run_trading_cycle()
        
        print("\n" + "=" * 50)
        print("РЕЗУЛЬТАТЫ СИМУЛЯЦИИ:")
        print("=" * 50)
        
        # Отчет по покупкам
        if results['buy_orders']:
            print(f"\nПОКУПКИ ({len(results['buy_orders'])}):")
            for order in results['buy_orders']:
                if order['result']['success']:
                    rec = order['recommendation']
                    result = order['result']
                    print(f"✅ {order['symbol']}")
                    print(f"   Количество: {result['quantity']}")
                    print(f"   Цена: ${result['price']:.6f}")
                    print(f"   Сумма: ${result['total']:.2f}")
                    print(f"   Уверенность ИИ: {rec['confidence']:.2f}")
                    print(f"   Причины: {', '.join(rec['reasons'])}")
                else:
                    print(f"❌ {order['symbol']}: {order['result']['error']}")
        else:
            print("\nПокупок не найдено")
        
        # Отчет по продажам
        if results['sell_orders']:
            print(f"\nПРОДАЖИ ({len(results['sell_orders'])}):")
            for order in results['sell_orders']:
                if order['result']['success']:
                    result = order['result']
                    print(f"✅ {order['symbol']}")
                    print(f"   Количество: {result['quantity']}")
                    print(f"   Цена: ${result['price']:.6f}")
                    print(f"   Сумма: ${result['total']:.2f}")
                else:
                    print(f"❌ {order['symbol']}: {order['result']['error']}")
        else:
            print("\nПродаж не найдено")
        
        # Ошибки
        if results['errors']:
            print(f"\nОШИБКИ ({len(results['errors'])}):")
            for error in results['errors']:
                print(f"❌ {error}")
        
        print("\n" + "=" * 50)
        print("СИМУЛЯЦИЯ ЗАВЕРШЕНА")
        print("=" * 50)
        
    except KeyboardInterrupt:
        print("\n\nСимуляция остановлена пользователем")
    except Exception as e:
        print(f"\n\nОшибка симуляции: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_simulation()