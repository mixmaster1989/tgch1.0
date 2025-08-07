#!/usr/bin/env python3
"""
Тест системы базы данных
Проверка подключений, моделей и кэша
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
from database.connection import DatabaseConnection
from database.models import DatabaseModels, PriceData, KlineData, TechnicalIndicator
from database.migrations import DatabaseMigrations
from cache.redis_manager import RedisCacheManager


def test_database_connections():
    """Тест подключений к базам данных"""
    print("🔌 Тестирование подключений к БД...")
    
    connection = DatabaseConnection()
    results = connection.test_connections()
    
    print("Результаты тестирования подключений:")
    for db, status in results.items():
        print(f"  {db}: {'✅' if status else '❌'}")
    
    connection.close_connections()
    return results


def test_database_models():
    """Тест моделей базы данных"""
    print("\n📊 Тестирование моделей БД...")
    
    try:
        models = DatabaseModels()
        models.create_tables()
        print("✅ Таблицы созданы успешно")
        
        # Проверяем создание таблиц
        connection = DatabaseConnection()
        with connection.get_cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Созданные таблицы: {tables}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания таблиц: {e}")
        return False


def test_redis_cache():
    """Тест Redis кэша"""
    print("\n⚡ Тестирование Redis кэша...")
    
    try:
        cache = RedisCacheManager()
        
        # Тест сохранения и получения цен
        cache.set_price("BTCUSDT", 45000.0)
        cache.set_price("ETHUSDT", 3000.0)
        
        btc_price = cache.get_price("BTCUSDT")
        eth_price = cache.get_price("ETHUSDT")
        
        print(f"💰 Цена BTC: {btc_price}")
        print(f"💰 Цена ETH: {eth_price}")
        
        # Тест технических индикаторов
        indicators = {
            'rsi_14': 65.5,
            'sma_20': 45000.0,
            'macd': {'macd': 50.0, 'signal': 45.0, 'histogram': 5.0}
        }
        cache.set_indicators("BTCUSDT", "1h", indicators)
        
        cached_indicators = cache.get_indicators("BTCUSDT", "1h")
        print(f"📈 Индикаторы BTC: {cached_indicators}")
        
        # Статистика кэша
        stats = cache.get_cache_stats()
        print(f"📊 Статистика кэша: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка Redis кэша: {e}")
        return False


def test_database_migrations():
    """Тест миграций базы данных"""
    print("\n🔄 Тестирование миграций БД...")
    
    try:
        migrations = DatabaseMigrations()
        migrations.run_migrations()
        
        # Получаем статус миграций
        status = migrations.get_migration_status()
        print(f"📦 Статус миграций:")
        print(f"  Всего миграций: {status['total_migrations']}")
        for migration in status['migrations']:
            print(f"  {migration['version']}: {migration['name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграций: {e}")
        return False


def test_data_operations():
    """Тест операций с данными"""
    print("\n💾 Тестирование операций с данными...")
    
    try:
        connection = DatabaseConnection()
        
        # Тест вставки данных
        with connection.get_cursor() as cursor:
            # Вставляем тестовую цену
            cursor.execute("""
                INSERT INTO prices (symbol, price, timestamp, source)
                VALUES (%s, %s, %s, %s)
            """, ("BTCUSDT", 45000.0, int(time.time() * 1000), "test"))
            
            # Вставляем тестовую свечу
            cursor.execute("""
                INSERT INTO klines (symbol, interval, open, high, low, close, volume, timestamp, close_time, quote_volume)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ("BTCUSDT", "1h", 45000.0, 45100.0, 44900.0, 45050.0, 100.5, 
                  int(time.time() * 1000), int(time.time() * 1000) + 3600000, 4500000.0))
        
        # Тест чтения данных
        with connection.get_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM prices WHERE symbol = %s", ("BTCUSDT",))
            price_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM klines WHERE symbol = %s", ("BTCUSDT",))
            kline_count = cursor.fetchone()[0]
        
        print(f"📊 Записано цен: {price_count}")
        print(f"📊 Записано свечей: {kline_count}")
        
        connection.close_connections()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка операций с данными: {e}")
        return False


def main():
    """Основная функция тестирования"""
    print("🧪 Запуск тестов системы базы данных...\n")
    
    results = {}
    
    # Тест подключений
    results['connections'] = test_database_connections()
    
    # Тест моделей
    results['models'] = test_database_models()
    
    # Тест кэша
    results['cache'] = test_redis_cache()
    
    # Тест миграций
    results['migrations'] = test_database_migrations()
    
    # Тест операций с данными
    results['operations'] = test_data_operations()
    
    # Итоговый отчет
    print("\n📋 ИТОГОВЫЙ ОТЧЕТ:")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results.items():
        if isinstance(result, dict):
            # Для подключений
            status = all(result.values())
            print(f"  {test_name}: {'✅' if status else '❌'}")
            if not status:
                all_passed = False
        else:
            # Для остальных тестов
            print(f"  {test_name}: {'✅' if result else '❌'}")
            if not result:
                all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система БД готова к использованию.")
    else:
        print("❌ НЕКОТОРЫЕ ТЕСТЫ ПРОВАЛЕНЫ. Проверьте настройки БД.")
    
    return all_passed


if __name__ == "__main__":
    main() 