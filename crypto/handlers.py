"""
Основные обработчики команд для криптомодуля.
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from .utils.keyboard import get_crypto_main_keyboard

# Получаем логгер для модуля
logger = logging.getLogger('crypto.handlers')

# Глобальная переменная для хранения экземпляра бота
_bot = None

def set_bot(bot):
    """Устанавливает экземпляр бота для использования в обработчиках"""
    global _bot
    _bot = bot
    logger.info("Бот установлен для криптомодуля")

def setup_crypto_handlers(router: Router):
    """
    Настраивает все обработчики для криптомодуля
    
    Args:
        router: Роутер для регистрации обработчиков
    """
    # Команда для входа в режим криптоанализа
    router.message.register(cmd_crypto_mode, Command("crypto_mode"))
    router.message.register(cmd_crypto_mode, Command("crypto"))  # Добавляем совместимость со старой командой
    
    # Обработчики для кнопок главного меню
    router.callback_query.register(show_market_overview, F.data == "crypto_market_overview")
    router.callback_query.register(show_smart_money_signals, F.data == "crypto_smart_money")
    router.callback_query.register(show_settings, F.data == "crypto_settings")
    
    logger.info("Обработчики криптомодуля зарегистрированы")

async def cmd_crypto_mode(message: Message):
    """
    Обработчик команды /crypto_mode - вход в режим криптоанализа
    """
    try:
        keyboard = get_crypto_main_keyboard()
        
        await message.answer(
            "🔐 *Режим криптоанализа активирован*\n\n"
            "Выберите опцию из меню ниже:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        logger.info(f"Пользователь {message.from_user.id} активировал режим криптоанализа")
    except Exception as e:
        logger.error(f"Ошибка при активации режима криптоанализа: {e}", exc_info=True)
        await message.answer("Произошла ошибка при активации режима криптоанализа. Попробуйте позже.")

async def show_market_overview(callback: CallbackQuery):
    """
    Показывает обзор рынка криптовалют
    """
    try:
        await callback.answer()
        
        # Здесь будет логика получения данных о рынке
        await callback.message.edit_text(
            "📊 *Обзор рынка криптовалют*\n\n"
            "Загрузка данных...\n\n"
            "Эта функция будет доступна в ближайшее время.",
            reply_markup=get_crypto_main_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Пользователь {callback.from_user.id} запросил обзор рынка")
    except Exception as e:
        logger.error(f"Ошибка при показе обзора рынка: {e}", exc_info=True)
        await callback.message.edit_text(
            "Произошла ошибка при загрузке обзора рынка. Попробуйте позже.",
            reply_markup=get_crypto_main_keyboard()
        )

async def show_smart_money_signals(callback: CallbackQuery):
    """
    Показывает сигналы Smart Money
    """
    try:
        await callback.answer()
        
        # Здесь будет логика получения сигналов Smart Money
        await callback.message.edit_text(
            "🔍 *Сигналы Smart Money*\n\n"
            "Анализ движений крупного капитала...\n\n"
            "Эта функция будет доступна в ближайшее время.",
            reply_markup=get_crypto_main_keyboard(),
            parse_mode="Markdown"
        )
        logger.info(f"Пользователь {callback.from_user.id} запросил сигналы Smart Money")
    except Exception as e:
        logger.error(f"Ошибка при показе сигналов Smart Money: {e}", exc_info=True)
        await callback.message.edit_text(
            "Произошла ошибка при загрузке сигналов. Попробуйте позже.",
            reply_markup=get_crypto_main_keyboard()
        )

async def show_settings(callback: CallbackQuery):
    """
    Показывает настройки криптомодуля
    """
    try:
        await callback.answer()
        
        # Создаем клавиатуру для настроек
        builder = InlineKeyboardBuilder()
        builder.button(text="Настроить оповещения", callback_data="crypto_settings_alerts")
        builder.button(text="Выбрать монеты", callback_data="crypto_settings_coins")
        builder.button(text="Назад", callback_data="crypto_back_to_main")
        builder.adjust(1)
        
        await callback.message.edit_text(
            "⚙️ *Настройки криптомодуля*\n\n"
            "Выберите параметры для настройки:",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
        logger.info(f"Пользователь {callback.from_user.id} открыл настройки криптомодуля")
    except Exception as e:
        logger.error(f"Ошибка при показе настроек: {e}", exc_info=True)
        await callback.message.edit_text(
            "Произошла ошибка при загрузке настроек. Попробуйте позже.",
            reply_markup=get_crypto_main_keyboard()
        )