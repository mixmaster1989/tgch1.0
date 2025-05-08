"""
Модуль для работы с локальной базой данных криптовалют
"""

import sqlite3
import json
import logging
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

# Получаем логгер для модуля
logger = logging.getLogger('crypto.data_sources.crypto_database')

class CryptoDatabase:
    """
    Класс для работы с локальной базой данных криптовалют
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Инициализирует базу данных
        
        Args:
            db_path: Путь к файлу базы данных (по умолчанию создается в директории модуля)
        """
        if db_path is None:
            db_path = str(Path(__file__).parent / "crypto_data.db")
        
        self.db_path = db_path
        self._init_db()
        logger.info(f"Инициализирована база данных: {db_path}")
    
    def _init_db(self):
        """
        Инициализирует структуру базы данных
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Таблица для хранения информации о монетах
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS coins (
                id TEXT PRIMARY KEY,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                data JSON NOT NULL,
                last_updated TIMESTAMP NOT NULL
            )
        ''')
        
        # Таблица для хранения исторических данных о ценах
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                coin_id TEXT,
                timestamp TIMESTAMP,
                price REAL NOT NULL,
                volume REAL,
                market_cap REAL,
                PRIMARY KEY (coin_id, timestamp),
                FOREIGN KEY (coin_id) REFERENCES coins(id)
            )
        ''')
        
        # Таблица для хранения рыночных данных
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS market_data (
                timestamp TIMESTAMP PRIMARY KEY,
                total_market_cap REAL,
                total_volume REAL,
                btc_dominance REAL,
                data JSON
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def save_coins(self, coins: List[Dict[str, Any]]):
        """
        Сохраняет информацию о монетах в базу данных
        
        Args:
            coins: Список словарей с информацией о монетах
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        for coin in coins:
            try:
                coin_id = coin.get('id', '')
                symbol = coin.get('symbol', '')
                name = coin.get('name', '')
                
                if not coin_id or not symbol:
                    continue
                
                # Сериализуем данные в JSON
                data_json = json.dumps(coin)
                
                # Вставляем или обновляем запись
                cursor.execute('''
                    INSERT OR REPLACE INTO coins (id, symbol, name, data, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                ''', (coin_id, symbol, name, data_json, now))
                
                # Если есть данные о цене, добавляем их в историю
                if 'price' in coin:
                    price = float(coin['price'] or 0)
                    volume = float(coin.get('volume24h', 0) or 0)
                    market_cap = float(coin.get('marketCap', 0) or 0)
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO price_history (coin_id, timestamp, price, volume, market_cap)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (coin_id, now, price, volume, market_cap))
            except Exception as e:
                logger.error(f"Ошибка при сохранении монеты {coin.get('symbol', 'unknown')}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Сохранено {len(coins)} монет в базу данных")
    
    async def save_market_data(self, market_data: Dict[str, Any]):
        """
        Сохраняет рыночные данные в базу данных
        
        Args:
            market_data: Словарь с рыночными данными
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        
        try:
            total_market_cap = float(market_data.get('totalMarketCap', 0) or 0)
            total_volume = float(market_data.get('total24hVolume', 0) or 0)
            btc_dominance = float(market_data.get('btcDominance', 0) or 0)
            
            # Сериализуем данные в JSON
            data_json = json.dumps(market_data)
            
            cursor.execute('''
                INSERT OR REPLACE INTO market_data (timestamp, total_market_cap, total_volume, btc_dominance, data)
                VALUES (?, ?, ?, ?, ?)
            ''', (now, total_market_cap, total_volume, btc_dominance, data_json))
            
            conn.commit()
            logger.info("Сохранены рыночные данные в базу данных")
        except Exception as e:
            logger.error(f"Ошибка при сохранении рыночных данных: {e}")
        finally:
            conn.close()
    
    async def get_coins(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Получает информацию о монетах из базы данных
        
        Args:
            limit: Максимальное количество монет
            offset: Смещение для пагинации
            
        Returns:
            List[Dict[str, Any]]: Список монет
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT data FROM coins
                ORDER BY json_extract(data, '$.rank')
                LIMIT ? OFFSET ?
            ''', (limit, offset))
            
            rows = cursor.fetchall()
            coins = []
            
            for row in rows:
                try:
                    coin_data = json.loads(row[0])
                    coins.append(coin_data)
                except json.JSONDecodeError:
                    logger.error("Ошибка декодирования JSON данных монеты")
            
            return coins
        except Exception as e:
            logger.error(f"Ошибка при получении монет из базы данных: {e}")
            return []
        finally:
            conn.close()
    
    async def get_coin_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Получает информацию о монете по символу
        
        Args:
            symbol: Символ монеты
            
        Returns:
            Optional[Dict[str, Any]]: Информация о монете или None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT data FROM coins
                WHERE symbol = ? COLLATE NOCASE
            ''', (symbol,))
            
            row = cursor.fetchone()
            
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    logger.error("Ошибка декодирования JSON данных монеты")
            
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении монеты {symbol} из базы данных: {e}")
            return None
        finally:
            conn.close()
    
    async def get_price_history(self, coin_id: str, days: int = 7) -> List[Dict[str, Any]]:
        """
        Получает историю цен монеты
        
        Args:
            coin_id: ID монеты
            days: Количество дней истории
            
        Returns:
            List[Dict[str, Any]]: История цен
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            cursor.execute('''
                SELECT timestamp, price, volume, market_cap FROM price_history
                WHERE coin_id = ? AND timestamp >= ?
                ORDER BY timestamp
            ''', (coin_id, start_date))
            
            rows = cursor.fetchall()
            history = []
            
            for row in rows:
                history.append({
                    'timestamp': row[0],
                    'price': row[1],
                    'volume': row[2],
                    'marketCap': row[3]
                })
            
            return history
        except Exception as e:
            logger.error(f"Ошибка при получении истории цен для монеты {coin_id}: {e}")
            return []
        finally:
            conn.close()
    
    async def get_latest_market_data(self) -> Optional[Dict[str, Any]]:
        """
        Получает последние рыночные данные
        
        Returns:
            Optional[Dict[str, Any]]: Рыночные данные или None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT data FROM market_data
                ORDER BY timestamp DESC
                LIMIT 1
            ''')
            
            row = cursor.fetchone()
            
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    logger.error("Ошибка декодирования JSON рыночных данных")
            
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении рыночных данных: {e}")
            return None
        finally:
            conn.close()
    
    async def get_data_freshness(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Получает информацию о свежести данных
        
        Returns:
            Tuple[Optional[datetime], Optional[datetime]]: (последнее обновление монет, последнее обновление рынка)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Получаем время последнего обновления монет
            cursor.execute('''
                SELECT MAX(last_updated) FROM coins
            ''')
            coins_updated = cursor.fetchone()[0]
            
            # Получаем время последнего обновления рыночных данных
            cursor.execute('''
                SELECT MAX(timestamp) FROM market_data
            ''')
            market_updated = cursor.fetchone()[0]
            
            if coins_updated:
                coins_updated = datetime.fromisoformat(coins_updated)
            
            if market_updated:
                market_updated = datetime.fromisoformat(market_updated)
            
            return (coins_updated, market_updated)
        except Exception as e:
            logger.error(f"Ошибка при получении информации о свежести данных: {e}")
            return (None, None)
        finally:
            conn.close()
    
    async def cleanup_old_data(self, days: int = 30):
        """
        Удаляет устаревшие данные из базы
        
        Args:
            days: Количество дней, после которых данные считаются устаревшими
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Удаляем старые данные о ценах
            cursor.execute('''
                DELETE FROM price_history
                WHERE timestamp < ?
            ''', (cutoff_date,))
            
            # Удаляем старые рыночные данные, оставляя последние 100 записей
            cursor.execute('''
                DELETE FROM market_data
                WHERE timestamp < ? AND timestamp NOT IN (
                    SELECT timestamp FROM market_data
                    ORDER BY timestamp DESC
                    LIMIT 100
                )
            ''', (cutoff_date,))
            
            conn.commit()
            logger.info(f"Удалены устаревшие данные старше {days} дней")
        except Exception as e:
            logger.error(f"Ошибка при удалении устаревших данных: {e}")
        finally:
            conn.close()