#!/usr/bin/env python3
"""
Тест сканирования аккаунта и автоматической подписки на символы
"""

import asyncio
import sys
import os
from datetime import datetime

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_data_manager import ComprehensiveDataManager

class TestLogger:
    """Логгер для записи результатов тестов в файл"""
    
    def __init__(self, filename="test_results.txt"):
        self.filename = filename
        self.log_buffer = []
        
    def log(self, message):
        """Добавляет сообщение в буфер и выводит на экран"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        print(formatted_message)
        self.log_buffer.append(formatted_message)
    
    def save_to_file(self):
        """Сохраняет все логи в файл"""
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ СИСТЕМЫ СКАНИРОВАНИЯ АККАУНТА\n")
                f.write("=" * 80 + "\n")
                f.write(f"Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                
                for log_entry in self.log_buffer:
                    f.write(log_entry + "\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("ТЕСТ ЗАВЕРШЕН\n")
                f.write("=" * 80 + "\n")
            
            print(f"\n✅ Результаты сохранены в файл: {self.filename}")
            
        except Exception as e:
            print(f"❌ Ошибка сохранения в файл: {e}")

async def test_account_scanning(logger):
    """Тестирует сканирование аккаунта и подписку на символы"""
    try:
        logger.log("🧪 Тест сканирования аккаунта и подписки на символы")
        logger.log("=" * 60)
        
        # Создаем менеджер данных
        logger.log("Создание менеджера данных...")
        data_manager = ComprehensiveDataManager()
        logger.log("✅ Менеджер данных создан")
        
        logger.log("1️⃣ Тестируем получение символов из аккаунта...")
        try:
            symbols = data_manager._get_account_symbols()
            logger.log(f"   Результат: {symbols}")
            logger.log(f"   Количество символов: {len(symbols)}")
        except Exception as e:
            logger.log(f"   ❌ Ошибка получения символов: {e}")
        logger.log("")
        
        logger.log("2️⃣ Тестируем получение сводки портфеля...")
        try:
            portfolio = data_manager.get_portfolio_summary()
            if portfolio:
                logger.log(f"   Общая стоимость: ${portfolio.get('total_usdt', 0):.2f}")
                logger.log(f"   Активные символы: {', '.join(portfolio.get('active_symbols', []))}")
                
                if portfolio.get('asset_values'):
                    logger.log("   💎 Стоимость активов:")
                    for asset, value in portfolio['asset_values'].items():
                        if value > 0:
                            logger.log(f"      {asset}: ${value:.2f}")
                
                if portfolio.get('positions'):
                    logger.log(f"   📈 Фьючерсные позиции: {len(portfolio['positions'])}")
                
                if portfolio.get('open_orders'):
                    logger.log(f"   📋 Открытые ордера: {len(portfolio['open_orders'])}")
            else:
                logger.log("   ⚠️ Сводка портфеля недоступна")
        except Exception as e:
            logger.log(f"   ❌ Ошибка получения сводки: {e}")
        logger.log("")
        
        logger.log("3️⃣ Тестируем принудительное обновление подписок...")
        try:
            await data_manager.refresh_account_subscriptions()
            logger.log("   ✅ Обновление подписок выполнено")
        except Exception as e:
            logger.log(f"   ❌ Ошибка обновления подписок: {e}")
        logger.log("")
        
        logger.log("4️⃣ Проверяем текущие подписки...")
        try:
            if hasattr(data_manager, '_last_account_symbols'):
                current_symbols = data_manager._last_account_symbols
                logger.log(f"   Текущие подписки: {', '.join(sorted(current_symbols))}")
                logger.log(f"   Количество подписок: {len(current_symbols)}")
            else:
                logger.log("   Подписки еще не установлены")
        except Exception as e:
            logger.log(f"   ❌ Ошибка проверки подписок: {e}")
        logger.log("")
        
        logger.log("5️⃣ Проверяем доступные методы...")
        try:
            methods = [method for method in dir(data_manager) if not method.startswith('_')]
            logger.log(f"   Доступные методы: {len(methods)}")
            logger.log(f"   Основные методы: {', '.join(methods[:20])}")  # Показываем первые 20
        except Exception as e:
            logger.log(f"   ❌ Ошибка проверки методов: {e}")
        logger.log("")
        
        logger.log("✅ Тест завершен успешно!")
        
    except Exception as e:
        logger.log(f"❌ Ошибка в тесте: {e}")
        import traceback
        error_trace = traceback.format_exc()
        logger.log(f"Детали ошибки:\n{error_trace}")

async def test_full_startup(logger):
    """Тестирует полный запуск системы"""
    try:
        logger.log("🚀 Тест полного запуска системы")
        logger.log("=" * 60)
        
        # Создаем менеджер данных
        logger.log("Создание менеджера данных...")
        data_manager = ComprehensiveDataManager()
        logger.log("✅ Менеджер данных создан")
        
        logger.log("1️⃣ Запускаем менеджер данных...")
        try:
            await data_manager.start()
            logger.log("   ✅ Менеджер данных запущен")
        except Exception as e:
            logger.log(f"   ❌ Ошибка запуска: {e}")
            return
        
        logger.log("2️⃣ Ждем 10 секунд для инициализации...")
        await asyncio.sleep(10)
        logger.log("   ✅ Ожидание завершено")
        
        logger.log("3️⃣ Проверяем статус...")
        try:
            if hasattr(data_manager, '_last_account_symbols'):
                symbols = data_manager._last_account_symbols
                logger.log(f"   Подписки установлены для: {', '.join(sorted(symbols))}")
                logger.log(f"   Количество подписок: {len(symbols)}")
            else:
                logger.log("   Подписки не установлены")
        except Exception as e:
            logger.log(f"   ❌ Ошибка проверки статуса: {e}")
        
        logger.log("4️⃣ Останавливаем систему...")
        try:
            await data_manager.stop()
            logger.log("   ✅ Система остановлена")
        except Exception as e:
            logger.log(f"   ❌ Ошибка остановки: {e}")
        
        logger.log("✅ Полный тест завершен успешно!")
        
    except Exception as e:
        logger.log(f"❌ Ошибка в полном тесте: {e}")
        import traceback
        error_trace = traceback.format_exc()
        logger.log(f"Детали ошибки:\n{error_trace}")

async def main():
    """Главная функция"""
    # Создаем логгер
    logger = TestLogger("test_results.txt")
    
    logger.log("🎯 ТЕСТИРОВАНИЕ СИСТЕМЫ СКАНИРОВАНИЯ АККАУНТА")
    logger.log("=" * 70)
    
    logger.log("Выберите тест:")
    logger.log("1. Базовый тест сканирования аккаунта")
    logger.log("2. Полный тест запуска системы")
    
    choice = input("Введите номер (1 или 2): ").strip()
    
    if choice == "1":
        logger.log("Запуск базового теста...")
        await test_account_scanning(logger)
    elif choice == "2":
        logger.log("Запуск полного теста...")
        await test_full_startup(logger)
    else:
        logger.log("Неверный выбор. Запускаю базовый тест...")
        await test_account_scanning(logger)
    
    # Сохраняем результаты в файл
    logger.save_to_file()
    
    logger.log("=" * 70)
    logger.log("📚 Результаты сохранены в файл test_results.txt")
    logger.log("📖 Прочитайте файл для получения полной информации")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Тест прерван пользователем")
    except Exception as e:
        print(f"\n\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc() 