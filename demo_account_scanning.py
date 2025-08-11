#!/usr/bin/env python3
"""
Демонстрация системы автоматического сканирования аккаунта
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_data_manager import ComprehensiveDataManager

class AccountScanningDemo:
    """Демонстрация работы системы сканирования аккаунта"""
    
    def __init__(self):
        self.data_manager = None
        self.is_running = False
    
    async def start_demo(self):
        """Запуск демонстрации"""
        try:
            print("🎭 ДЕМОНСТРАЦИЯ СИСТЕМЫ СКАНИРОВАНИЯ АККАУНТА")
            print("=" * 70)
            
            # Создаем менеджер данных
            print("1️⃣ Создание менеджера данных...")
            self.data_manager = ComprehensiveDataManager()
            print("   ✅ Менеджер создан")
            print()
            
            # Демонстрируем сканирование аккаунта
            print("2️⃣ Демонстрация сканирования аккаунта...")
            await self._demo_account_scanning()
            print()
            
            # Демонстрируем получение сводки портфеля
            print("3️⃣ Демонстрация сводки портфеля...")
            await self._demo_portfolio_summary()
            print()
            
            # Демонстрируем обновление подписок
            print("4️⃣ Демонстрация обновления подписок...")
            await self._demo_subscription_update()
            print()
            
            # Запускаем полную систему
            print("5️⃣ Запуск полной системы...")
            await self._demo_full_system()
            print()
            
            print("🎉 ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
            
        except Exception as e:
            print(f"❌ Ошибка в демонстрации: {e}")
            import traceback
            traceback.print_exc()
    
    async def _demo_account_scanning(self):
        """Демонстрация сканирования аккаунта"""
        try:
            print("   🔍 Сканируем аккаунт...")
            symbols = self.data_manager._get_account_symbols()
            
            print(f"   📊 Найдено символов: {len(symbols)}")
            if symbols:
                print(f"   💰 Символы: {', '.join(symbols)}")
            else:
                print("   ⚠️ Символы не найдены, используется базовый список")
            
        except Exception as e:
            print(f"   ❌ Ошибка сканирования: {e}")
    
    async def _demo_portfolio_summary(self):
        """Демонстрация сводки портфеля"""
        try:
            print("   📊 Получаем сводку портфеля...")
            portfolio = self.data_manager.get_portfolio_summary()
            
            if portfolio:
                print(f"   💰 Общая стоимость: ${portfolio.get('total_usdt', 0):.2f}")
                print(f"   🔍 Активные символы: {', '.join(portfolio.get('active_symbols', []))}")
                
                if portfolio.get('asset_values'):
                    print("   💎 Стоимость активов:")
                    for asset, value in portfolio['asset_values'].items():
                        if value > 0:
                            print(f"      {asset}: ${value:.2f}")
            else:
                print("   ⚠️ Сводка портфеля недоступна")
            
        except Exception as e:
            print(f"   ❌ Ошибка получения сводки: {e}")
    
    async def _demo_subscription_update(self):
        """Демонстрация обновления подписок"""
        try:
            print("   🔄 Обновляем подписки на символы...")
            await self.data_manager.refresh_account_subscriptions()
            
            if hasattr(self.data_manager, '_last_account_symbols'):
                current_symbols = self.data_manager._last_account_symbols
                print(f"   ✅ Подписки обновлены для {len(current_symbols)} символов")
                if current_symbols:
                    print(f"   📡 Подписки: {', '.join(sorted(current_symbols))}")
            else:
                print("   ⚠️ Подписки не установлены")
            
        except Exception as e:
            print(f"   ❌ Ошибка обновления подписок: {e}")
    
    async def _demo_full_system(self):
        """Демонстрация полной системы"""
        try:
            print("   🚀 Запускаем полную систему...")
            await self.data_manager.start()
            
            print("   ⏳ Ждем 5 секунд для инициализации...")
            await asyncio.sleep(5)
            
            print("   📊 Проверяем статус системы...")
            if hasattr(self.data_manager, '_last_account_symbols'):
                symbols = self.data_manager._last_account_symbols
                print(f"   ✅ Система работает с {len(symbols)} символами")
                if symbols:
                    print(f"   🔍 Активные символы: {', '.join(sorted(symbols))}")
            
            print("   🛑 Останавливаем систему...")
            await self.data_manager.stop()
            print("   ✅ Система остановлена")
            
        except Exception as e:
            print(f"   ❌ Ошибка в полной системе: {e}")
    
    def show_system_info(self):
        """Показывает информацию о системе"""
        print("\n📋 ИНФОРМАЦИЯ О СИСТЕМЕ")
        print("=" * 50)
        print("🔍 Автоматическое сканирование аккаунта:")
        print("   • При запуске - сканируется весь аккаунт")
        print("   • Во время работы - каждую минуту проверяются изменения")
        print("   • Автоматически обновляются WebSocket подписки")
        print()
        print("📊 Что сканируется:")
        print("   • Спот балансы (BTC, ETH, ADA, SOL и т.д.)")
        print("   • Фьючерсные позиции")
        print("   • Открытые ордера")
        print()
        print("🔄 Автоматические действия:")
        print("   • Подписка на новые символы")
        print("   • Отписка от удаленных символов")
        print("   • Загрузка исторических данных")
        print("   • Обновление технических индикаторов")
        print()
        print("💡 Преимущества:")
        print("   • Не нужно вручную указывать символы")
        print("   • Всегда актуальные данные")
        print("   • Эффективное использование ресурсов")
        print("   • Мониторинг портфеля в реальном времени")

async def main():
    """Главная функция"""
    print("🎯 ДЕМОНСТРАЦИЯ СИСТЕМЫ СКАНИРОВАНИЯ АККАУНТА")
    print("=" * 70)
    
    # Показываем информацию о системе
    demo = AccountScanningDemo()
    demo.show_system_info()
    
    # Спрашиваем пользователя
    print("\n❓ Хотите запустить демонстрацию? (y/n): ", end="")
    choice = input().strip().lower()
    
    if choice in ['y', 'yes', 'да', 'д']:
        print("\n🚀 Запускаем демонстрацию...")
        await demo.start_demo()
    else:
        print("\n👋 Демонстрация не запущена. До свидания!")
    
    print("\n" + "=" * 70)
    print("📚 Дополнительная информация:")
    print("   • README_ACCOUNT_SCANNING.md - подробное описание")
    print("   • test_account_scanning.py - тестирование")
    print("   • comprehensive_data_manager.py - основной код")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Демонстрация прервана пользователем")
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc() 