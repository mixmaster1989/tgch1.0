#!/usr/bin/env python3
"""
Проверка новых настроек менеджера скальперов
"""

from scalper_manager import ScalperManager

def main():
    print("🧪 Проверяем новые настройки менеджера...")
    print("=" * 50)

    manager = ScalperManager()

    print(f"Минимальный баланс: ${manager.min_usdc_balance_after_scalper:.2f}")
    print(f"Размер позиции: ${manager.position_size_usdc:.2f}")
    print(f"Баланс USDC: ${manager.get_usdc_balance():.2f}")

    print("\nПроверяем возможность запуска:")
    for symbol in ['BTCUSDC', 'ETHUSDC']:
        can_create, reason = manager.can_create_new_scalper(symbol)
        status = "✅ Можно" if can_create else "❌ Нельзя"
        print(f"   {symbol}: {status} - {reason}")

    print("\nТестируем запуск скальпера...")
    success = manager.start_new_scalper('BTCUSDC')
    if success:
        print("✅ BTC скальпер запущен успешно!")
        print(f"   Всего запущено: {len(manager.running_scalpers['BTCUSDC'])}")
    else:
        print("❌ Не удалось запустить BTC скальпер")

    print("\nОтправляем тестовый отчет...")
    manager.send_hourly_report()

if __name__ == "__main__":
    main()







