#!/usr/bin/env python3
"""
Запуск автоматической торговли по скану рынка
"""

import sys
import os
from auto_trading_cycle import AutoTradingCycle

def main():
    """Главная функция запуска"""
    print("🚀 ЗАПУСК АВТОМАТИЧЕСКОЙ ТОРГОВЛИ ПО СКАНУ РЫНКА")
    print("=" * 70)
    
    # Проверяем аргументы командной строки
    simulation_mode = True  # По умолчанию симуляция
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "real":
            simulation_mode = False
            print("⚠️ РЕЖИМ РЕАЛЬНОЙ ТОРГОВЛИ!")
            print("⚠️ БУДУТ ТРАТИТЬСЯ РЕАЛЬНЫЕ ДЕНЬГИ!")
            confirm = input("Подтвердите запуск реальной торговли (yes/no): ")
            if confirm.lower() != 'yes':
                print("❌ Запуск отменен")
                return
        elif sys.argv[1] == "simulation":
            simulation_mode = True
            print("🎮 РЕЖИМ СИМУЛЯЦИИ - деньги не тратятся")
        else:
            print("Использование:")
            print("  python3 run_auto_trader.py simulation  # Симуляция (по умолчанию)")
            print("  python3 run_auto_trader.py real        # Реальная торговля")
            return
    
    print(f"📊 Режим: {'СИМУЛЯЦИЯ' if simulation_mode else 'РЕАЛЬНАЯ ТОРГОВЛЯ'}")
    print("⏰ Интервал циклов: 5 минут")
    print("🎯 Автоматические покупки по найденным возможностям")
    print("=" * 70)
    
    try:
        # Создаем автоматический торговый цикл
        auto_trader = AutoTradingCycle(simulation_mode=simulation_mode)
        
        # Запускаем торговлю
        import asyncio
        asyncio.run(auto_trader.start_auto_trading())
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 