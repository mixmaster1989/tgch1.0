#!/usr/bin/env python3
"""
Скрипт для запуска миграций БД
"""

import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.models import DatabaseModels

def main():
    """Запуск миграций"""
    print("🗄️ Запуск миграций базы данных...")
    
    try:
        # Создаем модели и запускаем миграции
        models = DatabaseModels()
        models.create_tables()
        
        print("✅ Все таблицы созданы успешно!")
        
        # Показываем статус
        print("\n📊 Статус таблиц:")
        tables = [
            'prices', 'klines', 'technical_indicators', 'correlations',
            'market_data', 'account_data', 'news_data', 'orderbook_data',
            'trades_data', 'trade_history_data'
        ]
        
        for table in tables:
            print(f"   ✅ {table}")
        
        print(f"\n🎉 Всего создано таблиц: {len(tables)}")
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 