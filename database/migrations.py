"""
Миграции базы данных
Управление структурой БД и версиями
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db_connection
from database.models import DatabaseModels

class DatabaseMigrations:
    """Класс для управления миграциями БД"""
    
    def __init__(self):
        self.db = get_db_connection()
        self.models = DatabaseModels()
        self.migrations_table = "schema_migrations"
        
    def create_migrations_table(self):
        """Создание таблицы для отслеживания миграций"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
    
    def get_applied_migrations(self) -> List[str]:
        """Получение списка примененных миграций"""
        with self.db.get_cursor() as cursor:
            cursor.execute("SELECT version FROM schema_migrations ORDER BY applied_at")
            return [row[0] for row in cursor.fetchall()]
    
    def mark_migration_applied(self, version: str, name: str):
        """Отметка миграции как примененной"""
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO schema_migrations (version, name) VALUES (%s, %s)",
                (version, name)
            )
    
    def run_migrations(self):
        """Запуск всех миграций"""
        print("🔄 Запуск миграций базы данных...")
        
        # Создаем таблицу миграций
        self.create_migrations_table()
        
        # Получаем примененные миграции
        applied = self.get_applied_migrations()
        
        # Определяем миграции
        migrations = [
            {
                'version': '001',
                'name': 'Initial schema',
                'up': self._migration_001_initial_schema
            },
            {
                'version': '002', 
                'name': 'Add indexes for performance',
                'up': self._migration_002_add_indexes
            },
            {
                'version': '003',
                'name': 'Add partitioning for prices table',
                'up': self._migration_003_add_partitioning
            },
            {
                'version': '004',
                'name': 'Add Order Book and Trade tables',
                'up': self._migration_004_add_orderbook_tables
            }
        ]
        
        # Применяем миграции
        for migration in migrations:
            if migration['version'] not in applied:
                print(f"📦 Применение миграции {migration['version']}: {migration['name']}")
                try:
                    migration['up']()
                    self.mark_migration_applied(migration['version'], migration['name'])
                    print(f"✅ Миграция {migration['version']} применена")
                except Exception as e:
                    print(f"❌ Ошибка миграции {migration['version']}: {e}")
                    raise
            else:
                print(f"⏭️ Миграция {migration['version']} уже применена")
        
        print("✅ Все миграции выполнены")
    
    def _migration_001_initial_schema(self):
        """Миграция 001: Создание базовой схемы"""
        self.models.create_tables()
    
    def _migration_002_add_indexes(self):
        """Миграция 002: Добавление индексов для производительности"""
        with self.db.get_cursor() as cursor:
            # Индексы для быстрого поиска по времени
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_prices_timestamp 
                ON prices(timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_klines_timestamp 
                ON klines(timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_indicators_timestamp 
                ON technical_indicators(timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_correlations_timestamp 
                ON correlations(timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_market_data_timestamp 
                ON market_data(timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_account_data_timestamp 
                ON account_data(timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_news_data_timestamp 
                ON news_data(timestamp);
            """)
    
    def _migration_003_add_partitioning(self):
        """Миграция 003: Добавление партиционирования для больших таблиц"""
        with self.db.get_cursor() as cursor:
            # Создаем партиционированную таблицу цен по дням
            cursor.execute("""
                -- Создаем партиционированную таблицу цен
                CREATE TABLE IF NOT EXISTS prices_partitioned (
                    id SERIAL,
                    symbol VARCHAR(20) NOT NULL,
                    price DECIMAL(20,8) NOT NULL,
                    timestamp BIGINT NOT NULL,
                    source VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) PARTITION BY RANGE (timestamp);
                
                -- Создаем партиции для последних 30 дней
                DO $$
                DECLARE
                    i INTEGER;
                    start_time BIGINT;
                    end_time BIGINT;
                BEGIN
                    FOR i IN 0..29 LOOP
                        start_time := EXTRACT(EPOCH FROM (CURRENT_DATE - i)) * 1000;
                        end_time := EXTRACT(EPOCH FROM (CURRENT_DATE - i + 1)) * 1000;
                        
                        EXECUTE format('
                            CREATE TABLE IF NOT EXISTS prices_%s 
                            PARTITION OF prices_partitioned 
                            FOR VALUES FROM (%s) TO (%s)
                        ', 
                        to_char(CURRENT_DATE - i, 'YYYYMMDD'),
                        start_time,
                        end_time
                        );
                    END LOOP;
                END $$;
            """)
    
    def _migration_004_add_orderbook_tables(self):
        """Миграция 004: Добавление таблиц для Order Book и Trade данных"""
        # Создаем таблицы через модели
        self.models._create_orderbook_table()
        self.models._create_trades_table()
        self.models._create_trade_history_table()
        
        print("✅ Таблицы Order Book и Trade данных созданы")
    
    def rollback_migration(self, version: str):
        """Откат миграции"""
        print(f"🔄 Откат миграции {version}...")
        
        if version == '004':
            self._rollback_004()
        elif version == '003':
            self._rollback_003()
        elif version == '002':
            self._rollback_002()
        elif version == '001':
            self._rollback_001()
        else:
            print(f"❌ Неизвестная миграция: {version}")
            return
        
        # Удаляем запись о миграции
        with self.db.get_cursor() as cursor:
            cursor.execute("DELETE FROM schema_migrations WHERE version = %s", (version,))
        
        print(f"✅ Миграция {version} откачена")
    
    def _rollback_001(self):
        """Откат миграции 001"""
        self.models.drop_all_tables()
    
    def _rollback_002(self):
        """Откат миграции 002"""
        with self.db.get_cursor() as cursor:
            indexes = [
                'idx_prices_timestamp', 'idx_klines_timestamp', 'idx_indicators_timestamp',
                'idx_correlations_timestamp', 'idx_market_data_timestamp',
                'idx_account_data_timestamp', 'idx_news_data_timestamp'
            ]
            for index in indexes:
                cursor.execute(f"DROP INDEX IF EXISTS {index}")
    
    def _rollback_003(self):
        """Откат миграции 003"""
        with self.db.get_cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS prices_partitioned CASCADE")
    
    def _rollback_004(self):
        """Откат миграции 004"""
        with self.db.get_cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS orderbook_data CASCADE")
            cursor.execute("DROP TABLE IF EXISTS trades_data CASCADE")
            cursor.execute("DROP TABLE IF EXISTS trade_history_data CASCADE")
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Получение статуса миграций"""
        with self.db.get_cursor() as cursor:
            cursor.execute("""
                SELECT version, name, applied_at 
                FROM schema_migrations 
                ORDER BY applied_at
            """)
            migrations = cursor.fetchall()
        
        return {
            'total_migrations': len(migrations),
            'migrations': [
                {
                    'version': row[0],
                    'name': row[1],
                    'applied_at': row[2].isoformat() if row[2] else None
                }
                for row in migrations
            ]
        }
    
    def reset_database(self):
        """Полный сброс базы данных (только для разработки!)"""
        print("⚠️ ВНИМАНИЕ: Полный сброс базы данных!")
        confirm = input("Введите 'YES' для подтверждения: ")
        
        if confirm == 'YES':
            with self.db.get_cursor() as cursor:
                # Удаляем все таблицы
                cursor.execute("""
                    DROP SCHEMA public CASCADE;
                    CREATE SCHEMA public;
                    GRANT ALL ON SCHEMA public TO postgres;
                    GRANT ALL ON SCHEMA public TO public;
                """)
            print("🗑️ База данных полностью сброшена")
        else:
            print("❌ Сброс отменен")


# Глобальный экземпляр для использования в других модулях
db_migrations = DatabaseMigrations()


def run_migrations():
    """Запуск миграций"""
    db_migrations.run_migrations()


if __name__ == "__main__":
    # Запуск миграций
    run_migrations()
    
    # Показать статус
    status = db_migrations.get_migration_status()
    print(f"\n📊 Статус миграций:")
    print(f"Всего миграций: {status['total_migrations']}")
    for migration in status['migrations']:
        print(f"  {migration['version']}: {migration['name']} ({migration['applied_at']})") 