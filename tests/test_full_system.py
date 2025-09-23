#!/usr/bin/env python3
"""
Тестовый скрипт для запуска полноценной системы с ScalperManager
"""

import sys
import time
from scalper_manager import ScalperManager

def test_full_system():
    print("🚀 Запуск полноценной системы с ScalperManager...")
    print("=" * 60)

    try:
        # Создаем менеджер
        manager = ScalperManager()

        print("✅ ScalperManager создан")

        # Получаем баланс USDC
        account_info = manager.mex_api.get_account_info()
        usdc_balance = 0.0
        if 'balances' in account_info:
            for balance in account_info['balances']:
                if balance.get('asset') == 'USDC':
                    usdc_balance = float(balance.get('free', 0))
                    break

        print(f"📊 Баланс USDC: ${usdc_balance:.2f}")
        print(f"🎯 Настройки: позиция ${manager.position_size_usdc:.2f}, минимум ${manager.min_usdc_balance_after_scalper:.2f}")

        # Запускаем менеджер в отдельном потоке
        import threading
        import asyncio

        def run_manager():
            asyncio.run(manager.run())

        manager_thread = threading.Thread(target=run_manager, daemon=True)
        manager_thread.start()
        print("✅ Менеджер запущен в отдельном потоке")

        # Даем время на инициализацию
        time.sleep(5)

        # Проверяем статус
        status = manager.get_manager_status()
        print("📊 Статус менеджера:")
        print(f"   BTC скальперов: {status['btc_running']}")
        print(f"   ETH скальперов: {status['eth_running']}")
        print(f"   Всего экземпляров: {status['btc_running'] + status['eth_running']}")

        # Ждем немного чтобы увидеть работу
        print("\n⏳ Ждем 30 секунд для наблюдения за работой...")
        time.sleep(30)

        # Останавливаем менеджер
        print("\n🛑 Останавливаем систему...")
        manager.is_running = False  # Устанавливаем флаг остановки
        manager_thread.join(timeout=5)

        print("✅ Система остановлена успешно")

    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False

    return True

if __name__ == "__main__":
    success = test_full_system()
    if success:
        print("\n🎉 Тест завершен успешно!")
    else:
        print("\n💥 Тест провален!")
        sys.exit(1)
