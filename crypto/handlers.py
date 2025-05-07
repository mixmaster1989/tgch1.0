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
    
    # Обработчики для настроек
    from .settings import show_notification_settings, show_watchlist_settings
    router.callback_query.register(show_notification_settings, F.data == "crypto_settings_alerts")
    router.callback_query.register(show_watchlist_settings, F.data == "crypto_settings_coins")
    
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
        # Показываем индикатор загрузки
        await callback.answer("Загрузка данных...")
        
        # Отправляем сообщение о загрузке
        await callback.message.edit_text(
            "📊 *Обзор рынка криптовалют*\n\n"
            "Загрузка данных...\n\n"
            "Пожалуйста, подождите...",
            parse_mode="Markdown"
        )
        
        # Получаем обзор рынка
        from .analytics.market_analyzer import MarketAnalyzer
        from .notification.message_formatter import MessageFormatter
        
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
            logger.info(f"Показан обзор рынка для пользователя {callback.from_user.id}")
        else:
            # В случае ошибки
            await callback.message.edit_text(
                "❌ *Ошибка при получении данных*\n\n"
                "Не удалось получить данные о рынке. Пожалуйста, попробуйте позже.",
                reply_markup=get_crypto_main_keyboard(),
                parse_mode="Markdown"
            )
            logger.error(f"Не удалось получить обзор рынка для пользователя {callback.from_user.id}")
    except Exception as e:
        logger.error(f"Ошибка при показе обзора рынка: {e}", exc_info=True)
        await callback.message.edit_text(
            "Произошла ошибка при загрузке обзора рынка. Попробуйте позже.",
            reply_markup=get_crypto_main_keyboard()
        )

async def show_smart_money_signals(callback: CallbackQuery):
    """
    Показывает сигналы Smart Money на основе всплесков объема
    """
    try:
        # Показываем индикатор загрузки
        await callback.answer("Анализ данных...")
        
        # Отправляем сообщение о загрузке
        await callback.message.edit_text(
            "🔍 *Сигналы Smart Money*\n\n"
            "Анализ движений крупного капитала...\n\n"
            "Пожалуйста, подождите...",
            parse_mode="Markdown"
        )
        
        # Получаем сигналы о всплесках объема
        from .analytics.market_analyzer import MarketAnalyzer
        from .notification.message_formatter import MessageFormatter
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        
        analyzer = MarketAnalyzer()
        signals = await analyzer.detect_volume_spikes()
        
        if signals:
            # Сортируем сигналы по уверенности (от высокой к низкой)
            signals.sort(key=lambda s: s.confidence, reverse=True)
            
            # Ограничиваем количество сигналов для отображения
            signals_to_show = signals[:5]  # Показываем только топ-5 сигналов
            
            # Формируем сообщение
            message_text = "🔍 *Сигналы Smart Money - Всплески объема*\n\n"
            
            for i, signal in enumerate(signals_to_show):
                direction_emoji = "🟢" if signal.direction.value == "long" else "🔴"
                direction_text = "LONG" if signal.direction.value == "long" else "SHORT"
                
                message_text += (
                    f"{i+1}. {direction_emoji} *{signal.pair}* | {direction_text} | ${signal.price:.4f}\n"
                    f"   Уверенность: {'▓' * int(signal.confidence * 10)}{' ' * (10 - int(signal.confidence * 10))} ({signal.confidence:.2f})\n"
                    f"   {signal.description.split('.')[0]}.\n\n"
                )
            
            message_text += f"\nВсего найдено сигналов: {len(signals)}\nОбновлено: {signals[0].timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Создаем клавиатуру
            builder = InlineKeyboardBuilder()
            builder.button(text="🔄 Обновить сигналы", callback_data="crypto_smart_money")
            builder.button(text="🔙 Вернуться в меню", callback_data="crypto_back_to_main")
            builder.adjust(1)
            
            # Отправляем сообщение
            await callback.message.edit_text(
                text=message_text,
                reply_markup=builder.as_markup(),
                parse_mode="Markdown"
            )
            logger.info(f"Показаны сигналы Smart Money для пользователя {callback.from_user.id}")
        else:
            # Если сигналов нет
            await callback.message.edit_text(
                "🔍 *Сигналы Smart Money*\n\n"
                "В данный момент не обнаружено значимых сигналов.\n\n"
                "Попробуйте проверить позже или настроить параметры анализа в настройках.",
                reply_markup=get_crypto_main_keyboard(),
                parse_mode="Markdown"
            )
            logger.info(f"Для пользователя {callback.from_user.id} не найдено сигналов Smart Money")
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
        builder.button(text="🔔 Настроить оповещения", callback_data="crypto_settings_alerts")
        builder.button(text="📋 Список монет", callback_data="crypto_settings_coins")
        builder.button(text="📊 Параметры анализа", callback_data="crypto_settings_thresholds")
        builder.button(text="🔙 Назад", callback_data="crypto_back_to_main")
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