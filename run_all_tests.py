#!/usr/bin/env python3
"""
Запуск всех тестов исправления проблем
"""

import asyncio
import subprocess
import sys
import time

async def run_test(test_file: str, description: str) -> bool:
    """Запуск отдельного теста"""
    print(f"\n{'='*60}")
    print(f"🧪 ТЕСТ: {description}")
    print(f"📁 Файл: {test_file}")
    print(f"{'='*60}")
    
    try:
        # Запускаем тест
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        # Выводим результат
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"⚠️ Предупреждения:\n{result.stderr}")
            
        success = result.returncode == 0
        
        if success:
            print(f"✅ ТЕСТ ПРОЙДЕН: {description}")
        else:
            print(f"❌ ТЕСТ ПРОВАЛЕН: {description}")
            
        return success
        
    except subprocess.TimeoutExpired:
        print(f"⏰ ТЕСТ ПРЕРВАН ПО ТАЙМАУТУ: {description}")
        return False
    except Exception as e:
        print(f"❌ ОШИБКА ЗАПУСКА ТЕСТА: {e}")
        return False

async def main():
    """Главная функция запуска всех тестов"""
    print("🚀 ЗАПУСК ВСЕХ ТЕСТОВ ИСПРАВЛЕНИЯ ПРОБЛЕМ")
    print("=" * 60)
    
    tests = [
        ("test_ssl_fix.py", "Исправление SSL проблем"),
        ("test_websocket_stability.py", "Стабильность WebSocket"),
        ("test_correlation_cache.py", "Кэширование корреляций"),
        ("test_fallback_strategy.py", "Fallback стратегия"),
        ("test_error_handling.py", "Обработка ошибок")
    ]
    
    results = {}
    start_time = time.time()
    
    for test_file, description in tests:
        try:
            success = await run_test(test_file, description)
            results[description] = success
            
            # Пауза между тестами
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте {description}: {e}")
            results[description] = False
    
    # Итоговая сводка
    total_time = time.time() - start_time
    passed_tests = sum(1 for success in results.values() if success)
    total_tests = len(results)
    
    print(f"\n{'='*60}")
    print("📊 ИТОГОВАЯ СВОДКА ТЕСТОВ")
    print(f"{'='*60}")
    
    for description, success in results.items():
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"  {status}: {description}")
    
    print(f"\n📈 РЕЗУЛЬТАТЫ:")
    print(f"  Всего тестов: {total_tests}")
    print(f"  Пройдено: {passed_tests}")
    print(f"  Провалено: {total_tests - passed_tests}")
    print(f"  Успешность: {passed_tests/total_tests*100:.1f}%")
    print(f"  Время выполнения: {total_time:.1f} секунд")
    
    if passed_tests == total_tests:
        print(f"\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return True
    else:
        print(f"\n⚠️ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 