"""
Модуль для работы с главным меню криптомодуля
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

from .data_sources.crypto_data_manager import get_data_manager

# Получаем логгер для модуля
logger = logging.getLogger('crypto.main_menu')

# Импортируем необходимые модули
try:
    from aiogram import Router, F
    from aiogram.types import Message, CallbackQuery
    from aiogram.filters import Command
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from datetime import datetime
    
    # Импортируем менеджер данных
    from .data_sources.crypto_data_manager import get_data_manager
    data_manager = get_data_manager()
    
    # Проверяем, инициализирован ли менеджер данных корректно
    if not hasattr(data_manager, 'api') or not data_manager.api:
        logger.warning("API клиент не инициализирован в data_manager")
        data_manager = None
        
except ImportError as ie:
    logger.error(f"Ошибка импорта необходимых модулей: {ie}")
    data_manager = None
finally:
    # Убедимся, что все необходимые компоненты инициализированы
    if not all([data_manager, alert_service]):
        logger.warning("Не все компоненты инициализированы")
        
# Создаем роутер для обработчиков
router = Router()

# Глобальная переменная для хранения экземпляра бота
_bot = None

@router.message(Command("crypto"))
async def cmd_crypto(message: Message):
    """
    Обработчик команды /crypto
    Показывает главное меню криптомодуля
    """
    try:
        # Создаем клавиатуру
        builder = InlineKeyboardBuilder()
        builder.button(text="📊 Рыночный обзор", callback_data="crypto_market_overview")
        
        # Добавляем кнопку управления ключами только если есть несколько API-ключей
        if data_manager and data_manager.cryptorank_api_keys and len(data_manager.cryptorank_api_keys) > 1:
            builder.button(text=f"🔄 Управление ключами ({len(data_manager.cryptorank_api_keys)} шт)", callback_data="crypto_key_management")
        
        builder.adjust(1)
        
        await message.answer(
            "🪙 *Криптовалютный модуль*\n\n"
            "Выберите действие из меню ниже:",
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка в главном меню: {e}")
        await message.reply("❌ Произошла ошибка при открытии главного меню")

@router.callback_query(F.data == "crypto_market_overview")
async def callback_market_overview(callback: CallbackQuery):
    """
    Обработчик для кнопки "Рыночный обзор"
    """
    await callback.answer("Загрузка рыночного обзора...")
    
    try:
        # Получаем данные о рынке
        data_manager = get_data_manager()
        overview = await data_manager.get_market_overview()
        
        # Форматируем данные для отображения
        total_market_cap = f"${overview['total_market_cap'] / 1_000_000_000:.2f}B"
        total_volume = f"${overview['total_volume_24h'] / 1_000_000_000:.2f}B"
        btc_dominance = f"{overview['btc_dominance']:.2f}%"
        
        # Форматируем список растущих монет
        gainers_text = ""
        for i, coin in enumerate(overview['top_gainers']):
            symbol = coin.get('symbol', '')
            price = coin.get('price', 0)
            change = coin.get('price_change_percent_24h', 0)
            gainers_text += f"{i+1}. {symbol} - ${price:.4f} (+{change:.2f}%)\n"
        
        # Форматируем список падающих монет
        losers_text = ""
        for i, coin in enumerate(overview['top_losers']):
            symbol = coin.get('symbol', '')
            price = coin.get('price', 0)
            change = coin.get('price_change_percent_24h', 0)
            losers_text += f"{i+1}. {symbol} - ${price:.4f} ({change:.2f}%)\n"
        
        # Форматируем время обновления
        update_time = overview['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        
        # Отправляем сообщение с обзором рынка
        await callback.message.edit_text(
            f"📊 *Рыночный обзор криптовалют*\n\n"
            f"Общая капитализация: {total_market_cap}\n"
            f"Доминирование BTC: {btc_dominance}\n"
            f"Объем торгов (24ч): {total_volume}\n\n"
            f"🟢 *Топ растущих монет (24ч):*\n{gainers_text}\n"
            f"🔴 *Топ падающих монет (24ч):*\n{losers_text}\n"
            f"Обновлено: {update_time}",
            reply_markup=InlineKeyboardBuilder().button(
                text="🔙 Назад", callback_data="crypto_back_to_main"
            ).as_markup(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка при получении рыночного обзора: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при получении рыночного обзора.\n\n"
            "Пожалуйста, попробуйте позже.",
            reply_markup=InlineKeyboardBuilder().button(
                text="🔙 Назад", callback_data="crypto_back_to_main"
            ).as_markup()
        )

@router.callback_query(F.data == "crypto_back_to_main")
async def callback_back_to_main(callback: CallbackQuery):
    """
    Обработчик для кнопки "Назад" в криптомодуле
    """
    await callback.answer()
    
    # Возвращаемся в главное меню криптомодуля
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Рыночный обзор", callback_data="crypto_market_overview")
    builder.button(text="🔔 Уведомления", callback_data="crypto_alerts")
    builder.button(text="📈 Smart Money", callback_data="crypto_smart_money")
    builder.button(text="🔍 Поиск монеты", callback_data="crypto_search_coin")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "🪙 *Криптовалютный модуль*\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "crypto_key_management")
async def callback_key_management(callback: CallbackQuery):
    """
    Обработчик нажатия на кнопку управления ключами
    Отображает информацию о доступных API-ключах
    """
    if not data_manager:
        await callback.message.reply("⚠️ Менеджер данных не инициализирован")
        return
    
    # Формируем сообщение с информацией о ключах
    keys_info = ""
    
    if data_manager.cryptorank_api_keys:
        for i, key in enumerate(data_manager.cryptorank_api_keys):
            # Скрываем часть ключа для безопасности
            masked_key = key[:10] + "..." if len(key) > 10 else key
            status = "(текущий)" if i == data_manager.current_api_key_index else ""
            keys_info += f"{i+1}. ***{masked_key} {status}\n"
    
    # Получаем текущий интервал обновления
    interval_minutes = data_manager.min_update_interval.total_seconds() / 60
    
    result = (
        f"🔄 *Управление API-ключами*\n\n"
        f"Текущий ключ: {data_manager.current_api_key_index+1} из {len(data_manager.cryptorank_api_keys)}\n"
        f"Используется для генерации сигналов и обновления данных\n\n"
        f"⏳ Интервал обновления: {interval_minutes:.0f} минут\n"
        "Для изменения интервала используйте команду `/set_interval <минут>`\n\n"
        "🔐 Доступные ключи:\n"
        f'{keys_info if keys_info else "Нет дополнительных ключей"}\n\n'
        "Бот автоматически переключится на следующий ключ при достижении лимита\n"
        "Или вы можете вручную изменить интервал обновления через команду `/set_interval <минут>`"
    )
    
    await callback.message.edit_text(result, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "crypto_test_santiment")
async def callback_test_santiment(callback: CallbackQuery):
    """
    Обработчик нажатия на кнопку тестирования Santiment API
    """
    from crypto.handlers import cmd_test_santiment
    await cmd_test_santiment(callback.message)
    await callback.answer()

def register_crypto_menu_handlers(dp):
    """
    Регистрирует обработчики для главного меню криптомодуля
    
    Args:
        dp: Диспетчер aiogram
    """
    dp.include_router(router)
    logger.info("Обработчики меню криптомодуля зарегистрированы")

def set_bot(bot):
    """
    Устанавливает экземпляр бота для обработчиков
    
    Args:
        bot: Экземпляр бота aiogram
    """
    global _bot
    _bot = bot
    
    # Инициализируем сервисы
    try:
        if data_manager:
            logger.info("Бот установлен для менеджера данных")
            # Передаем бота в сервисы
            from .notification.alert_service import alert_service
            alert_service.set_bot(bot)
    except Exception as e:
        logger.error(f"Ошибка при установке бота: {e}")
