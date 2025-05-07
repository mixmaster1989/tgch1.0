"""
Модуль для управления пользовательскими настройками
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional, Set
import aiosqlite
from pathlib import Path

# Получаем логгер для модуля
logger = logging.getLogger('crypto.user_settings.preferences')

class UserPreferences:
    """
    Класс для управления пользовательскими настройками
    """
    
    def __init__(self):
        """
        Инициализирует менеджер пользовательских настроек
        """
        # Путь к базе данных настроек
        self.db_path = Path(__file__).parent / "user_settings.db"
        
        # Создаем директорию, если она не существует
        self.db_path.parent.mkdir(exist_ok=True)
        
        logger.info("Инициализирован менеджер пользовательских настроек")
    
    async def _init_db(self):
        """
        Инициализирует базу данных, если она не существует
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Создаем таблицу для настроек пользователей
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id INTEGER PRIMARY KEY,
                    settings TEXT NOT NULL
                )
            ''')
            
            # Создаем таблицу для отслеживаемых монет
            await db.execute('''
                CREATE TABLE IF NOT EXISTS watched_coins (
                    user_id INTEGER,
                    coin_symbol TEXT,
                    PRIMARY KEY (user_id, coin_symbol)
                )
            ''')
            
            # Создаем таблицу для психологических уровней
            await db.execute('''
                CREATE TABLE IF NOT EXISTS price_levels (
                    user_id INTEGER,
                    coin_symbol TEXT,
                    price_level REAL,
                    PRIMARY KEY (user_id, coin_symbol, price_level)
                )
            ''')
            
            await db.commit()
    
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """
        Получает настройки пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict[str, Any]: Настройки пользователя
        """
        await self._init_db()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT settings FROM user_settings WHERE user_id = ?",
                (user_id,)
            )
            row = await cursor.fetchone()
            
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    logger.error(f"Ошибка декодирования настроек для пользователя {user_id}")
            
            # Возвращаем настройки по умолчанию
            return {
                "notifications": {
                    "price_change": True,
                    "psychological_levels": True,
                    "volume_spikes": True
                },
                "thresholds": {
                    "price_change_percent": 5.0,
                    "volume_spike_ratio": 2.0
                }
            }
    
    async def save_user_settings(self, user_id: int, settings: Dict[str, Any]) -> bool:
        """
        Сохраняет настройки пользователя
        
        Args:
            user_id: ID пользователя
            settings: Настройки пользователя
            
        Returns:
            bool: True, если настройки успешно сохранены
        """
        await self._init_db()
        
        try:
            settings_json = json.dumps(settings)
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT OR REPLACE INTO user_settings (user_id, settings) VALUES (?, ?)",
                    (user_id, settings_json)
                )
                await db.commit()
            
            logger.info(f"Сохранены настройки для пользователя {user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении настроек для пользователя {user_id}: {e}", exc_info=True)
            return False
    
    async def add_watched_coin(self, user_id: int, coin_symbol: str) -> bool:
        """
        Добавляет монету в список отслеживаемых
        
        Args:
            user_id: ID пользователя
            coin_symbol: Символ монеты
            
        Returns:
            bool: True, если монета успешно добавлена
        """
        await self._init_db()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT OR IGNORE INTO watched_coins (user_id, coin_symbol) VALUES (?, ?)",
                    (user_id, coin_symbol.upper())
                )
                await db.commit()
            
            logger.info(f"Добавлена монета {coin_symbol} для пользователя {user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении монеты {coin_symbol} для пользователя {user_id}: {e}", exc_info=True)
            return False
    
    async def remove_watched_coin(self, user_id: int, coin_symbol: str) -> bool:
        """
        Удаляет монету из списка отслеживаемых
        
        Args:
            user_id: ID пользователя
            coin_symbol: Символ монеты
            
        Returns:
            bool: True, если монета успешно удалена
        """
        await self._init_db()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM watched_coins WHERE user_id = ? AND coin_symbol = ?",
                    (user_id, coin_symbol.upper())
                )
                await db.commit()
            
            logger.info(f"Удалена монета {coin_symbol} для пользователя {user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении монеты {coin_symbol} для пользователя {user_id}: {e}", exc_info=True)
            return False
    
    async def get_user_watched_coins(self, user_id: int = None) -> List[str]:
        """
        Получает список отслеживаемых монет пользователя
        
        Args:
            user_id: ID пользователя (если None, возвращает все отслеживаемые монеты)
            
        Returns:
            List[str]: Список символов отслеживаемых монет
        """
        await self._init_db()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                if user_id is None:
                    # Получаем все уникальные монеты
                    cursor = await db.execute("SELECT DISTINCT coin_symbol FROM watched_coins")
                else:
                    # Получаем монеты конкретного пользователя
                    cursor = await db.execute(
                        "SELECT coin_symbol FROM watched_coins WHERE user_id = ?",
                        (user_id,)
                    )
                
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Ошибка при получении списка отслеживаемых монет: {e}", exc_info=True)
            return []
    
    async def add_price_level(self, user_id: int, coin_symbol: str, price_level: float) -> bool:
        """
        Добавляет психологический уровень цены для монеты
        
        Args:
            user_id: ID пользователя
            coin_symbol: Символ монеты
            price_level: Уровень цены
            
        Returns:
            bool: True, если уровень успешно добавлен
        """
        await self._init_db()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT OR IGNORE INTO price_levels (user_id, coin_symbol, price_level) VALUES (?, ?, ?)",
                    (user_id, coin_symbol.upper(), price_level)
                )
                await db.commit()
            
            logger.info(f"Добавлен уровень цены {price_level} для монеты {coin_symbol} пользователя {user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при добавлении уровня цены для монеты {coin_symbol}: {e}", exc_info=True)
            return False
    
    async def remove_price_level(self, user_id: int, coin_symbol: str, price_level: float) -> bool:
        """
        Удаляет психологический уровень цены для монеты
        
        Args:
            user_id: ID пользователя
            coin_symbol: Символ монеты
            price_level: Уровень цены
            
        Returns:
            bool: True, если уровень успешно удален
        """
        await self._init_db()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "DELETE FROM price_levels WHERE user_id = ? AND coin_symbol = ? AND price_level = ?",
                    (user_id, coin_symbol.upper(), price_level)
                )
                await db.commit()
            
            logger.info(f"Удален уровень цены {price_level} для монеты {coin_symbol} пользователя {user_id}")
            return True
        except Exception as e:
            logger.error(f"Ошибка при удалении уровня цены для монеты {coin_symbol}: {e}", exc_info=True)
            return False
    
    async def get_price_levels(self, user_id: int, coin_symbol: str) -> List[float]:
        """
        Получает список психологических уровней цены для монеты
        
        Args:
            user_id: ID пользователя
            coin_symbol: Символ монеты
            
        Returns:
            List[float]: Список уровней цены
        """
        await self._init_db()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT price_level FROM price_levels WHERE user_id = ? AND coin_symbol = ? ORDER BY price_level",
                    (user_id, coin_symbol.upper())
                )
                
                rows = await cursor.fetchall()
                return [row[0] for row in rows]
        except Exception as e:
            logger.error(f"Ошибка при получении уровней цены для монеты {coin_symbol}: {e}", exc_info=True)
            return []