"""
Модуль для работы с настройками пользователей
"""

import logging
import json
import os
from typing import Dict, Any, List, Optional
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .utils.keyboard import get_crypto_main_keyboard

# Получаем логгер для модуля
logger = logging.getLogger('crypto.settings')

# Путь к директории с настройками пользователей
SETTINGS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'user_settings')

# Создаем директорию для настроек, если она не существует
os.makedirs(SETTINGS_DIR, exist_ok=True)

class UserSettings:
    """
    Класс для работы с настройками пользователей
    """
    
    @staticmethod
    def get_user_settings_path(user_id: int) -> str:
        """
        Возвращает путь к файлу с настройками пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            str: Путь к файлу с настройками
        """
        return os.path.join(SETTINGS_DIR, f"user_{user_id}.json")
    
    @staticmethod
    def get_default_settings() -> Dict[str, Any]:
        """
        Возвращает настройки по умолчанию
        
        Returns:
            Dict[str, Any]: Настройки по умолчанию
        """
        return {
            "notifications": {
                "enabled": True,
                "volume_spike": True,
                "large_orders": True,
                "funding_rate": True
            },
            "watchlist": [
                "BTC/USDT",
                "ETH/USDT",
                "SOL/USDT",
                "BNB/USDT",
                "XRP/USDT"
            ],
            "thresholds": {
                "volume_spike": 1.8,
                "large_order_btc": 10.0,
                "funding_rate": 0.05
            }
        }
    
    @staticmethod
    def load_user_settings(user_id: int) -> Dict[str, Any]:
        """
        Загружает настройки пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Dict[str, Any]: Настройки пользователя
        """
        settings_path = UserSettings.get_user_settings_path(user_id)
        
        try:
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as file:
                    settings = json.load(file)
                    logger.info(f"Загружены настройки для пользователя {user_id}")
                    return settings
            else:
                # Если файл не существует, создаем настройки по умолчанию
                default_settings = UserSettings.get_default_settings()
                UserSettings.save_user_settings(user_id, default_settings)
                logger.info(f"Созданы настройки по умолчанию для пользователя {user_id}")
                return default_settings
        except Exception as e:
            logger.error(f"Ошибка при загрузке настроек пользователя {user_id}: {e}", exc_info=True)
            return UserSettings.get_default_settings()
    
    @staticmethod
    def save_user_settings(user_id: int, settings: Dict[str, Any]) -> bool:
        """
        Сохраняет настройки пользователя
        
        Args:
            user_id: ID пользователя
            settings: Настройки для сохранения
            
        Returns:
            bool: True в случае успеха, False в случае ошибки
        """
        settings_path = UserSettings.get_user_settings_path(user_id)
        
        try:
            with open(settings_path, 'w', encoding='utf-8') as file:
                json.dump(settings, file, indent=4)
                logger.info(f"Сохранены настройки для пользователя {user_id}")
                return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении настроек пользователя {user_id}: {e}", exc_info=True)
            return False
    
    @staticmethod
    def update_user_setting(user_id: int, setting_path: List[str], value: Any) -> bool:
        """
        Обновляет конкретную настройку пользователя
        
        Args:
            user_id: ID пользователя
            setting_path: Путь к настройке в виде списка ключей
            value: Новое значение
            
        Returns:
            bool: True в случае успеха, False в случае ошибки
        """
        settings = UserSettings.load_user_settings(user_id)
        
        # Обновляем настройку по указанному пути
        current = settings
        for key in setting_path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[setting_path[-1]] = value
        
        return UserSettings.save_user_settings(user_id, settings)
    
    @staticmethod
    def toggle_notification_setting(user_id: int, notification_type: str) -> bool:
        """
        Переключает настройку уведомлений
        
        Args:
            user_id: ID пользователя
            notification_type: Тип уведомления
            
        Returns:
            bool: Новое значение настройки
        """
        settings = UserSettings.load_user_settings(user_id)
        
        # Проверяем, существует ли такой тип уведомления
        if notification_type in settings["notifications"]:
            # Инвертируем значение
            new_value = not settings["notifications"][notification_type]
            settings["notifications"][notification_type] = new_value
            
            # Сохраняем настройки
            UserSettings.save_user_settings(user_id, settings)
            
            return new_value
        
        return False
    
    @staticmethod
    def add_to_watchlist(user_id: int, pair: str) -> bool:
        """
        Добавляет пару в список отслеживаемых
        
        Args:
            user_id: ID пользователя
            pair: Торговая пара
            
        Returns:
            bool: True в случае успеха, False в случае ошибки
        """
        settings = UserSettings.load_user_settings(user_id)
        
        if pair not in settings["watchlist"]:
            settings["watchlist"].append(pair)
            return UserSettings.save_user_settings(user_id, settings)
        
        return True
    
    @staticmethod
    def remove_from_watchlist(user_id: int, pair: str) -> bool:
        """
        Удаляет пару из списка отслеживаемых
        
        Args:
            user_id: ID пользователя
            pair: Торговая пара
            
        Returns:
            bool: True в случае успеха, False в случае ошибки
        """
        settings = UserSettings.load_user_settings(user_id)
        
        if pair in settings["watchlist"]:
            settings["watchlist"].remove(pair)
            return UserSettings.save_user_settings(user_id, settings)
        
        return True

# Обработчики для настроек
async def show_notification_settings(callback: CallbackQuery):
    """
    Показывает настройки уведомлений
    """
    try:
        await callback.answer()
        
        # Загружаем настройки пользователя
        user_id = callback.from_user.id
        settings = UserSettings.load_user_settings(user_id)
        
        # Создаем клавиатуру
        builder = InlineKeyboardBuilder()
        
        # Добавляем кнопки для настроек уведомлений
        for notification_type, enabled in settings["notifications"].items():
            status = "✅" if enabled else "❌"
            display_name = notification_type.replace("_", " ").title()
            builder.button(
                text=f"{display_name}: {status}",
                callback_data=f"crypto_toggle_notification_{notification_type}"
            )
        
        # Добавляем кнопку возврата
        builder.button(text="🔙 Назад", callback_data="crypto_settings")
        
        # Настраиваем расположение кнопок
        builder.adjust(1)
        
        # Отправляем сообщение
        await callback.message.edit_text(
            "⚙️ *Настройки уведомлений*\n\n"
            "Выберите типы уведомлений, которые вы хотите получать:",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        logger.info(f"Пользователь {user_id} открыл настройки уведомлений")
    except Exception as e:
        logger.error(f"Ошибка при показе настроек уведомлений: {e}", exc_info=True)
        await callback.message.edit_text(
            "Произошла ошибка при загрузке настроек. Попробуйте позже.",
            reply_markup=get_crypto_main_keyboard()
        )

async def show_watchlist_settings(callback: CallbackQuery):
    """
    Показывает настройки списка отслеживаемых пар
    """
    try:
        await callback.answer()
        
        # Загружаем настройки пользователя
        user_id = callback.from_user.id
        settings = UserSettings.load_user_settings(user_id)
        
        # Формируем сообщение
        message_text = "📋 *Список отслеживаемых пар*\n\n"
        
        if settings["watchlist"]:
            for i, pair in enumerate(settings["watchlist"]):
                message_text += f"{i+1}. {pair}\n"
        else:
            message_text += "Список пуст. Добавьте пары для отслеживания.\n"
        
        message_text += "\nВыберите действие:"
        
        # Создаем клавиатуру
        builder = InlineKeyboardBuilder()
        builder.button(text="➕ Добавить пару", callback_data="crypto_add_to_watchlist")
        builder.button(text="➖ Удалить пару", callback_data="crypto_remove_from_watchlist")
        builder.button(text="🔙 Назад", callback_data="crypto_settings")
        builder.adjust(1)
        
        # Отправляем сообщение
        await callback.message.edit_text(
            message_text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        logger.info(f"Пользователь {user_id} открыл настройки списка отслеживаемых пар")
    except Exception as e:
        logger.error(f"Ошибка при показе настроек списка отслеживаемых пар: {e}", exc_info=True)
        await callback.message.edit_text(
            "Произошла ошибка при загрузке настроек. Попробуйте позже.",
            reply_markup=get_crypto_main_keyboard()
        )