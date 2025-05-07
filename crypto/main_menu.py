"""
Модуль для работы с главным меню криптомодуля
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from .analytics.market_analyzer import MarketAnalyzer
from .notification.message_formatter import MessageFormatter
from .utils.keyboard import get_crypto_main_keyboard

# Получаем логгер для модуля
logger = logging.getLogger('crypto.main_menu')

# Глобальная переменная для хранения экземпляра бота
_bot = None

def set_bot(bot):
    """Устанавливает экземпляр бота для использования в обработчиках"""
    global _bot
    _bot = bot
    logger.info("Бот установлен для главного меню криптомодуля")

def register_crypto_menu_handlers(dp):
    """
    Регистрирует обработчики для главного меню криптомодуля
    
    Args:
        dp: Экземпляр диспетчера aiogram
    """
    # Создаем роутер для меню
    menu_router = Router()
    
    # Регистрируем обработчики
    menu_router.callback_query.register(handle_back_to_main, F.data == "crypto_back_to_main")
    menu_router.callback_query.register(handle_refresh_market, F.data == "crypto_refresh_market")
    
    # Подключаем роутер к диспетчеру
    dp.include_router(menu_router)
    
    logger.info("Обработчики меню криптомодуля зарегистрированы")

async def handle_back_to_main(callback: CallbackQuery):
    """
    Обработчик для возврата в главное меню
    """
    try:
        await callback.answer()
        
        await callback.message.edit_text(
            "🔐 *Режим криптоанализа*\n\n"
            "Выберите опцию из меню ниже:",
            reply_markup=get_crypto_main_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Пользователь {callback.from_user.id} вернулся в главное меню криптомодуля")
    except Exception as e:
        logger.error(f"Ошибка при возврате в главное меню: {e}", exc_info=True)

async def handle_refresh_market(callback: CallbackQuery):
    """
    Обработчик для обновления данных о рынке
    """
    try:
        # Показываем индикатор загрузки
        await callback.answer("Обновление данных...")
        
        # Отправляем сообщение о загрузке
        await callback.message.edit_text(
            "📊 *Обновление данных о рынке*\n\n"
            "Пожалуйста, подождите...",
            parse_mode="Markdown"
        )
        
        # Получаем обзор рынка
        analyzer = MarketAnalyzer()
        overview = await analyzer.get_market_overview()
        
        if overview:
            # Форматируем сообщение
            formatter = MessageFormatter()
            message_data = formatter.format_market_overview(overview)
            
            # Обновляем сообщение
            await callback.message.edit_text(
                text=message_data["text"],
                reply_markup=message_data["keyboard"],
                parse_mode=message_data["parse_mode"]
            )
            logger.info(f"Обновлены данные о рынке для пользователя {callback.from_user.id}")
        else:
            # В случае ошибки
            await callback.message.edit_text(
                "❌ *Ошибка при получении данных*\n\n"
                "Не удалось получить обновленные данные о рынке. Пожалуйста, попробуйте позже.",
                reply_markup=get_crypto_main_keyboard(),
                parse_mode="Markdown"
            )
            logger.error(f"Не удалось получить обзор рынка для пользователя {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при обновлении данных о рынке: {e}", exc_info=True)
        
        # В случае исключения
        await callback.message.edit_text(
            "❌ *Произошла ошибка*\n\n"
            "Не удалось обновить данные о рынке. Пожалуйста, попробуйте позже.",
            reply_markup=get_crypto_main_keyboard(),
            parse_mode="Markdown"
        )