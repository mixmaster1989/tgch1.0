"""
Подключение к базам данных
PostgreSQL для исторических данных
Redis для кэша
"""

import os
import psycopg2
import redis
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Менеджер подключений к базам данных"""
    
    def __init__(self):
        # PostgreSQL настройки
        self.pg_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'mexca_trade'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
        
        # Redis настройки
        self.redis_config = {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': os.getenv('REDIS_PORT', '6379'),
            'db': os.getenv('REDIS_DB', '0'),
            'password': os.getenv('REDIS_PASSWORD', None)
        }
        
        self.pg_connection = None
        self.redis_connection = None
        
    def get_postgres_connection(self):
        """Получение подключения к PostgreSQL"""
        try:
            if not self.pg_connection or self.pg_connection.closed:
                self.pg_connection = psycopg2.connect(**self.pg_config)
                logger.info("Подключение к PostgreSQL установлено")
            return self.pg_connection
        except Exception as e:
            logger.error(f"Ошибка подключения к PostgreSQL: {e}")
            raise
    
    def get_redis_connection(self):
        """Получение подключения к Redis"""
        try:
            if not self.redis_connection:
                self.redis_connection = redis.Redis(**self.redis_config)
                # Проверяем подключение
                self.redis_connection.ping()
                logger.info("Подключение к Redis установлено")
            return self.redis_connection
        except Exception as e:
            logger.error(f"Ошибка подключения к Redis: {e}")
            raise
    
    @contextmanager
    def get_cursor(self):
        """Контекстный менеджер для работы с курсором PostgreSQL"""
        conn = self.get_postgres_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка в транзакции: {e}")
            raise
        finally:
            cursor.close()
    
    def test_connections(self) -> Dict[str, bool]:
        """Тестирование подключений"""
        results = {}
        
        # Тест PostgreSQL
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                results['postgresql'] = True
                logger.info("✅ PostgreSQL подключение работает")
        except Exception as e:
            results['postgresql'] = False
            logger.error(f"❌ PostgreSQL подключение не работает: {e}")
        
        # Тест Redis
        try:
            redis_conn = self.get_redis_connection()
            redis_conn.ping()
            results['redis'] = True
            logger.info("✅ Redis подключение работает")
        except Exception as e:
            results['redis'] = False
            logger.error(f"❌ Redis подключение не работает: {e}")
        
        return results
    
    def close_connections(self):
        """Закрытие всех подключений"""
        try:
            if self.pg_connection and not self.pg_connection.closed:
                self.pg_connection.close()
                logger.info("PostgreSQL подключение закрыто")
        except Exception as e:
            logger.error(f"Ошибка закрытия PostgreSQL: {e}")
        
        try:
            if self.redis_connection:
                self.redis_connection.close()
                logger.info("Redis подключение закрыто")
        except Exception as e:
            logger.error(f"Ошибка закрытия Redis: {e}")


# Глобальный экземпляр для использования в других модулях
db_connection = DatabaseConnection()


def get_db_connection() -> DatabaseConnection:
    """Получение глобального подключения к БД"""
    return db_connection


if __name__ == "__main__":
    # Тест подключений
    connection = DatabaseConnection()
    results = connection.test_connections()
    
    print("Результаты тестирования подключений:")
    for db, status in results.items():
        print(f"  {db}: {'✅' if status else '❌'}")
    
    connection.close_connections() 