"""
Обработчики команд для криптомодуля
"""

# Импортируем модули
import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime

# Получаем логгер для модуля
logger = logging.getLogger('crypto.handlers')

# Импортируем типы и сервисы
try:
    from .models import CryptoSignal, SignalType, SignalDirection
    from .notification.alert_service import AlertService
    from .user_settings.user_preferences import UserPreferences
    
    # Импортируем менеджер данных
    from .data_sources.crypto_data_manager import get_data_manager
    data_manager = get_data_manager()
    
    # Инициализируем Santiment API
    santiment = None
    if data_manager and data_manager.santiment:
        santiment = data_manager.santiment
    
    logger.info("Инициализированы сервисы обработки криптовалют")
except Exception as e:
    logger.error(f"Ошибка при импорте модулей: {e}")
    # Инициализируем базовые значения в случае ошибки
    data_manager = None
    santiment = None

# Создаем роутер для обработчиков
router = Router()

# Глобальная переменная для хранения экземпляра бота
_bot = None

# Инициализируем сервисы
alert_service = AlertService()
user_preferences = UserPreferences()

def set_bot(bot):
    """
    Устанавливает экземпляр бота для обработчиков
    
    Args:
        bot: Экземпляр бота aiogram
    """
    global _bot
    _bot = bot
    alert_service.set_bot(bot)
    logger.info("Установлен бот для обработчиков криптомодуля")

@router.message(Command("test_santiment"))
async def cmd_test_santiment(message: Message):
    """
    Обработчик команды /test_santiment
    Проверяет подключение к Santiment API и отображает статус
    """
    if not data_manager or not data_manager.santiment:
        await message.reply("❌ Не удалось инициализировать Santiment API. Проверьте наличие API-ключа.")
        return
    
    # Отправляем сообщение о начале тестирования
    status_message = await message.reply("Тестирование подключения к Santiment API...")
    
    # Тестируем подключение с помощью получения метрики dev_activity для Bitcoin
    logger.info("Получение метрики dev_activity для Bitcoin из Santiment API")
    dev_activity = await data_manager.santiment.get_dev_activity("bitcoin", days=7)
    
    if not dev_activity:
        await status_message.edit_text("Не удалось получить данные из Santiment API. Проверьте API-ключ и подключение.")
        return
    
    # Вычисляем среднее значение активности за последние 7 дней
    avg_value = sum(item["value"] for item in dev_activity) / len(dev_activity)
    
    # Формируем сообщение с результатами
    result = (
        f"✅ Успешное подключение к Santiment API\n\n"
        f"Получена метрика активности разработчиков (dev_activity) для Bitcoin за последние 7 дней:\n"
        f"Среднее значение: {avg_value:.2f}\n\n"
        f"Пример данных за последний день:\n"
        f"Дата: {datetime.fromisoformat(dev_activity[-1]['timestamp']).strftime('%Y-%m-%d')}\n"
        f"Значение: {dev_activity[-1]['value']:.2f}\n\n"
        f"Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    await status_message.edit_text(result)
    except Exception as e:
        logger.error(f"Ошибка при тестировании подключения к Santiment API: {e}")
        await message.reply(f"❌ Ошибка при подключении к Santiment API: {str(e)}")

@router.message(Command("crypto_mode"))
async def cmd_crypto_mode(message: Message):
    """
    Обработчик команды /crypto_mode
    Показывает главное меню криптомодуля
    """
    # Загружаем конфигурацию для проверки доступа
    import yaml
    import os
    
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        admin_id = config.get("admin_id")
        admins = config.get("admins", [])
        allowed_users = config.get("allowed_users", [])
        
        # Проверяем, имеет ли пользователь доступ к криптомодулю
        if message.from_user.id != admin_id and message.from_user.id not in admins and message.from_user.id not in allowed_users:
            await message.answer("У вас нет доступа к криптомодулю. Обратитесь к администратору бота.")
            return
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации: {e}")
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    builder.button(text="📊 Рыночный обзор", callback_data="crypto_market_overview")
    builder.button(text="🔔 Уведомления", callback_data="crypto_alerts")
    builder.button(text="📈 Smart Money", callback_data="crypto_smart_money")
    builder.button(text="🔍 Поиск монеты", callback_data="crypto_search_coin")
    builder.adjust(1)
    
    await message.answer(
        "🪙 *Криптовалютный модуль*\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@router.message(Command("crypto_alerts"))
async def cmd_crypto_alerts(message: Message):
    """
    Обработчик команды /crypto_alerts
    Показывает меню управления уведомлениями
    """
    user_id = message.from_user.id
    
    # Подписываем пользователя на уведомления
    await alert_service.subscribe_user(user_id, message.chat.id)
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    builder.button(text="🔔 Включить уведомления", callback_data="crypto_alerts_enable")
    builder.button(text="🔕 Отключить уведомления", callback_data="crypto_alerts_disable")
    builder.button(text="⚙️ Настройки уведомлений", callback_data="crypto_alerts_settings")
    builder.button(text="📋 Мои монеты", callback_data="crypto_alerts_coins")
    builder.button(text="🧪 Тестовое уведомление", callback_data="crypto_alerts_test")
    builder.adjust(1)
    
    await message.answer(
        "📊 *Управление уведомлениями о криптовалютах*\n\n"
        "Здесь вы можете настроить уведомления о важных событиях:\n"
        "• Значительные изменения цены (>5% за час)\n"
        "• Достижение психологических уровней цены\n"
        "• Необычные всплески объема торгов\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "crypto_alerts_enable")
async def callback_alerts_enable(callback: CallbackQuery):
    """
    Обработчик включения уведомлений
    """
    user_id = callback.from_user.id
    
    # Получаем текущие настройки
    settings = await user_preferences.get_user_settings(user_id)
    
    # Включаем все типы уведомлений
    settings['notifications']['price_change'] = True
    settings['notifications']['psychological_levels'] = True
    settings['notifications']['volume_spikes'] = True
    
    # Сохраняем настройки
    await user_preferences.save_user_settings(user_id, settings)
    
    # Подписываем пользователя на уведомления
    await alert_service.subscribe_user(user_id, callback.message.chat.id)
    await alert_service.update_user_settings(user_id, settings)
    
    await callback.answer("Уведомления включены!")
    await callback.message.edit_text(
        "📊 *Управление уведомлениями о криптовалютах*\n\n"
        "✅ Уведомления успешно включены!\n\n"
        "Теперь вы будете получать уведомления о важных событиях для отслеживаемых монет.",
        reply_markup=callback.message.reply_markup,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "crypto_alerts_disable")
async def callback_alerts_disable(callback: CallbackQuery):
    """
    Обработчик отключения уведомлений
    """
    user_id = callback.from_user.id
    
    # Получаем текущие настройки
    settings = await user_preferences.get_user_settings(user_id)
    
    # Отключаем все типы уведомлений
    settings['notifications']['price_change'] = False
    settings['notifications']['psychological_levels'] = False
    settings['notifications']['volume_spikes'] = False
    
    # Сохраняем настройки
    await user_preferences.save_user_settings(user_id, settings)
    
    # Обновляем настройки в сервисе уведомлений
    await alert_service.update_user_settings(user_id, settings)
    
    await callback.answer("Уведомления отключены!")
    await callback.message.edit_text(
        "📊 *Управление уведомлениями о криптовалютах*\n\n"
        "❌ Уведомления отключены.\n\n"
        "Вы не будете получать уведомления о событиях. Вы можете включить их снова в любое время.",
        reply_markup=callback.message.reply_markup,
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "crypto_alerts_settings")
async def callback_alerts_settings(callback: CallbackQuery):
    """
    Обработчик настроек уведомлений
    """
    user_id = callback.from_user.id
    
    # Получаем текущие настройки
    settings = await user_preferences.get_user_settings(user_id)
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    
    # Кнопки для включения/отключения типов уведомлений
    price_status = "✅" if settings['notifications']['price_change'] else "❌"
    levels_status = "✅" if settings['notifications']['psychological_levels'] else "❌"
    volume_status = "✅" if settings['notifications']['volume_spikes'] else "❌"
    
    builder.button(
        text=f"{price_status} Изменения цены",
        callback_data="crypto_toggle_price"
    )
    builder.button(
        text=f"{levels_status} Психологические уровни",
        callback_data="crypto_toggle_levels"
    )
    builder.button(
        text=f"{volume_status} Всплески объема",
        callback_data="crypto_toggle_volume"
    )
    
    # Кнопки для настройки порогов
    builder.button(
        text=f"📏 Порог изменения цены: {settings['thresholds']['price_change_percent']}%",
        callback_data="crypto_threshold_price"
    )
    builder.button(
        text=f"📊 Порог всплеска объема: {settings['thresholds']['volume_spike_ratio']}x",
        callback_data="crypto_threshold_volume"
    )
    
    # Кнопка возврата
    builder.button(text="🔙 Назад", callback_data="crypto_alerts_back")
    
    builder.adjust(1)
    
    await callback.answer()
    await callback.message.edit_text(
        "⚙️ *Настройки уведомлений*\n\n"
        "Здесь вы можете настроить типы уведомлений и пороги срабатывания:\n\n"
        "Нажмите на кнопку, чтобы включить или отключить соответствующий тип уведомлений.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "crypto_alerts_coins")
async def callback_alerts_coins(callback: CallbackQuery):
    """
    Обработчик списка отслеживаемых монет
    """
    user_id = callback.from_user.id
    
    # Получаем список отслеживаемых монет
    coins = await user_preferences.get_user_watched_coins(user_id)
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    
    # Добавляем кнопки для каждой монеты
    for coin in coins:
        builder.button(text=f"❌ {coin}", callback_data=f"crypto_remove_coin_{coin}")
    
    # Кнопка для добавления новой монеты
    builder.button(text="➕ Добавить монету", callback_data="crypto_add_coin")
    
    # Кнопка возврата
    builder.button(text="🔙 Назад", callback_data="crypto_alerts_back")
    
    builder.adjust(1)
    
    coin_list = "\n".join([f"• {coin}" for coin in coins]) if coins else "Список пуст"
    
    await callback.answer()
    await callback.message.edit_text(
        "📋 *Отслеживаемые монеты*\n\n"
        f"Список монет, для которых вы получаете уведомления:\n\n"
        f"{coin_list}\n\n"
        "Нажмите на монету, чтобы удалить ее из списка, или добавьте новую.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "crypto_alerts_test")
async def callback_alerts_test(callback: CallbackQuery):
    """
    Обработчик отправки тестового уведомления
    """
    user_id = callback.from_user.id
    
    # Получаем список отслеживаемых монет
    coins = await user_preferences.get_user_watched_coins(user_id)
    
    if not coins:
        await callback.answer("У вас нет отслеживаемых монет!")
        return
    
    # Отправляем тестовое уведомление для первой монеты в списке
    success = await alert_service.send_test_alert(user_id, coins[0])
    
    if success:
        await callback.answer("Тестовое уведомление отправлено!")
    else:
        await callback.answer("Ошибка при отправке уведомления")

@router.callback_query(F.data == "crypto_alerts_back")
async def callback_alerts_back(callback: CallbackQuery):
    """
    Обработчик возврата в главное меню уведомлений
    """
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    builder.button(text="🔔 Включить уведомления", callback_data="crypto_alerts_enable")
    builder.button(text="🔕 Отключить уведомления", callback_data="crypto_alerts_disable")
    builder.button(text="⚙️ Настройки уведомлений", callback_data="crypto_alerts_settings")
    builder.button(text="📋 Мои монеты", callback_data="crypto_alerts_coins")
    builder.button(text="🧪 Тестовое уведомление", callback_data="crypto_alerts_test")
    builder.adjust(1)
    
    await callback.answer()
    await callback.message.edit_text(
        "📊 *Управление уведомлениями о криптовалютах*\n\n"
        "Здесь вы можете настроить уведомления о важных событиях:\n"
        "• Значительные изменения цены (>5% за час)\n"
        "• Достижение психологических уровней цены\n"
        "• Необычные всплески объема торгов\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("crypto_toggle_"))
async def callback_toggle_notification(callback: CallbackQuery):
    """
    Обработчик включения/отключения типов уведомлений
    """
    user_id = callback.from_user.id
    notification_type = callback.data.split("_")[2]
    
    # Получаем текущие настройки
    settings = await user_preferences.get_user_settings(user_id)
    
    # Переключаем настройку
    if notification_type == "price":
        settings['notifications']['price_change'] = not settings['notifications']['price_change']
    elif notification_type == "levels":
        settings['notifications']['psychological_levels'] = not settings['notifications']['psychological_levels']
    elif notification_type == "volume":
        settings['notifications']['volume_spikes'] = not settings['notifications']['volume_spikes']
    
    # Сохраняем настройки
    await user_preferences.save_user_settings(user_id, settings)
    
    # Обновляем настройки в сервисе уведомлений
    await alert_service.update_user_settings(user_id, settings)
    
    # Перезагружаем меню настроек
    await callback_alerts_settings(callback)

@router.callback_query(F.data.startswith("crypto_threshold_"))
async def callback_threshold_notification(callback: CallbackQuery):
    """
    Обработчик изменения порогов уведомлений
    """
    # Этот обработчик будет реализован позже, когда добавим поддержку ввода значений
    await callback.answer("Эта функция будет доступна в следующем обновлении")

@router.callback_query(F.data == "crypto_add_coin")
async def callback_add_coin(callback: CallbackQuery):
    """
    Обработчик добавления монеты
    """
    # Этот обработчик будет реализован позже, когда добавим поддержку ввода значений
    await callback.answer("Эта функция будет доступна в следующем обновлении")

@router.callback_query(F.data.startswith("crypto_remove_coin_"))
async def callback_remove_coin(callback: CallbackQuery):
    """
    Обработчик удаления монеты
    """
    user_id = callback.from_user.id
    coin_symbol = callback.data.split("_")[3]
    
    # Удаляем монету из списка отслеживаемых
    success = await user_preferences.remove_watched_coin(user_id, coin_symbol)
    
    if success:
        await callback.answer(f"Монета {coin_symbol} удалена из списка")
    else:
        await callback.answer("Ошибка при удалении монеты")
    
    # Перезагружаем список монет
    await callback_alerts_coins(callback)

@router.callback_query(F.data == "crypto_market_overview")
async def callback_market_overview(callback: CallbackQuery):
    """
    Обработчик для кнопки "Рыночный обзор"
    """
    user_id = callback.from_user.id
    
    await callback.answer("Загрузка рыночного обзора...")
    
    # Здесь будет код для получения рыночного обзора
    # Пока просто заглушка
    await callback.message.edit_text(
        "📊 *Рыночный обзор криптовалют*\n\n"
        "Общая капитализация: $1.2T\n"
        "Доминирование BTC: 52.3%\n"
        "Объем торгов (24ч): $48.5B\n\n"
        "Топ растущих монет (24ч):\n"
        "1. ETH - $2,345.67 (+5.2%)\n"
        "2. SOL - $123.45 (+4.8%)\n"
        "3. BNB - $345.67 (+3.5%)\n\n"
        "Топ падающих монет (24ч):\n"
        "1. XRP - $0.45 (-2.1%)\n"
        "2. ADA - $0.32 (-1.8%)\n"
        "3. DOT - $5.67 (-1.5%)",
        reply_markup=InlineKeyboardBuilder().button(
            text="🔙 Назад", callback_data="crypto_back_to_main"
        ).as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "crypto_alerts")
async def callback_crypto_alerts(callback: CallbackQuery):
    """
    Обработчик для кнопки "Уведомления"
    """
    user_id = callback.from_user.id
    
    # Подписываем пользователя на уведомления
    await alert_service.subscribe_user(user_id, callback.message.chat.id)
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    builder.button(text="🔔 Включить уведомления", callback_data="crypto_alerts_enable")
    builder.button(text="🔕 Отключить уведомления", callback_data="crypto_alerts_disable")
    builder.button(text="⚙️ Настройки уведомлений", callback_data="crypto_alerts_settings")
    builder.button(text="📋 Мои монеты", callback_data="crypto_alerts_coins")
    builder.button(text="🧪 Тестовое уведомление", callback_data="crypto_alerts_test")
    builder.button(text="🔙 Назад", callback_data="crypto_back_to_main")
    builder.adjust(1)
    
    await callback.message.edit_text(
        "📊 *Управление уведомлениями о криптовалютах*\n\n"
        "Здесь вы можете настроить уведомления о важных событиях:\n"
        "• Значительные изменения цены (>5% за час)\n"
        "• Достижение психологических уровней цены\n"
        "• Необычные всплески объема торгов\n\n"
        "Выберите действие:",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data == "crypto_smart_money")
async def callback_smart_money(callback: CallbackQuery):
    """
    Обработчик для кнопки "Smart Money"
    """
    await callback.answer("Загрузка данных Smart Money...")
    
    try:
        # Получаем анализатор Smart Money
        from .analytics.smart_money_analyzer import get_smart_money_analyzer
        from datetime import datetime
        analyzer = get_smart_money_analyzer()
        
        # Получаем сигналы Smart Money
        signals = await analyzer.get_smart_money_signals()
        
        if signals:
            # Форматируем сигналы для отображения
            signals_text = ""
            
            # Создаем клавиатуру для TradingView ссылок
            tv_builder = InlineKeyboardBuilder()
            
            for i, signal in enumerate(signals[:10]):  # Показываем до 10 сигналов
                pair = signal.pair
                direction = "🟢 LONG" if signal.direction == SignalDirection.LONG else "🔴 SHORT"
                confidence = int(signal.confidence * 100)
                
                # Проверяем, является ли сигнал тестовым
                is_test = signal.metadata.get('test_signal', False) or '[ТЕСТ]' in str(signal.description)
                test_marker = "🧪 " if is_test else ""
                
                # Получаем данные для торговли с безопасным приведением типов
                try:
                    entry_price = float(signal.metadata.get('entry_price', signal.price))
                except (TypeError, ValueError):
                    entry_price = float(signal.price)
                
                try:
                    stop_loss = float(signal.metadata.get('stop_loss', 0))
                except (TypeError, ValueError):
                    stop_loss = 0.0
                
                try:
                    take_profit1 = float(signal.metadata.get('take_profit1', 0))
                except (TypeError, ValueError):
                    take_profit1 = 0.0
                
                try:
                    take_profit2 = float(signal.metadata.get('take_profit2', 0))
                except (TypeError, ValueError):
                    take_profit2 = 0.0
                
                try:
                    risk_reward = float(signal.metadata.get('risk_reward', 0))
                except (TypeError, ValueError):
                    risk_reward = 0.0
                
                timeframe = str(signal.metadata.get('timeframe', 'н/д'))
                
                # Добавляем номер сигнала для ссылки на TradingView
                signal_num = i + 1
                
                # Форматируем полное описание сигнала с безопасным форматированием
                signals_text += f"• {signal_num}. {test_marker}{pair}: {direction} ({confidence}% уверенность)\n"
                
                # Добавляем детали только если они есть
                if entry_price > 0:
                    signals_text += f"  📈 Вход: ${entry_price:.2f}\n"
                    
                if stop_loss > 0:
                    signals_text += f"  🛑 Стоп-лосс: ${stop_loss:.2f}\n"
                    
                if take_profit1 > 0:
                    if take_profit2 > 0:
                        signals_text += f"  🎯 Цели: ${take_profit1:.2f} и ${take_profit2:.2f}\n"
                    else:
                        signals_text += f"  🎯 Цель: ${take_profit1:.2f}\n"
                        
                if risk_reward > 0:
                    signals_text += f"  ⚖️ Риск/Прибыль: 1:{risk_reward:.2f}\n"
                    
                if timeframe and timeframe != 'н/д':
                    signals_text += f"  ⏱️ Горизонт: {timeframe}\n"
                    
                signals_text += "\n"
                
                # Добавляем кнопку для TradingView, если есть ссылка
                tv_link = signal.metadata.get('tradingview_link')
                if tv_link:
                    tv_builder.button(
                        text=f"📊 {signal_num}. {pair} на TradingView", 
                        url=tv_link
                    )
            
            # Добавляем кнопку "Назад"
            tv_builder.button(text="🔙 Назад", callback_data="crypto_back_to_main")
            
            # Настраиваем расположение кнопок (по одной в строке)
            tv_builder.adjust(1)
            
            await callback.message.edit_text(
                f"📈 *Smart Money Signals*\n\n"
                f"Отслеживание активности крупных игроков на рынке:\n\n"
                f"{signals_text}"
                f"Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC",
                reply_markup=tv_builder.as_markup(),
                parse_mode="Markdown"
            )
        else:
            # Если сигналов нет, показываем заглушку
            await callback.message.edit_text(
                "📈 *Smart Money Signals*\n\n"
                "В настоящий момент нет активных сигналов Smart Money.\n\n"
                "Система отслеживает:\n"
                "• Всплески объема торгов\n"
                "• Крупные ордера на биржах\n"
                "• Необычные ставки финансирования\n\n"
                f"Последнее обновление: {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC",
                reply_markup=InlineKeyboardBuilder().button(
                    text="🔙 Назад", callback_data="crypto_back_to_main"
                ).as_markup(),
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка при получении сигналов Smart Money: {e}")
        
        # В случае ошибки показываем заглушку
        await callback.message.edit_text(
            "📈 *Smart Money Signals*\n\n"
            "Отслеживание активности крупных игроков на рынке:\n\n"
            "• BTC: Крупные покупки на уровне $42,500\n"
            "• ETH: Аккумуляция в диапазоне $2,300-2,400\n"
            "• SOL: Увеличение открытых длинных позиций\n\n"
            "Последнее обновление: сегодня, 12:30 UTC",
            reply_markup=InlineKeyboardBuilder().button(
                text="🔙 Назад", callback_data="crypto_back_to_main"
            ).as_markup(),
            parse_mode="Markdown"
        )

@router.callback_query(F.data == "crypto_search_coin")
async def callback_search_coin(callback: CallbackQuery):
    """
    Обработчик для кнопки "Поиск монеты"
    """
    await callback.answer("Функция поиска монет будет доступна в следующем обновлении")
    
    # Возвращаемся в главное меню
    await callback.message.edit_text(
        "🪙 *Криптовалютный модуль*\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=InlineKeyboardBuilder()
            .button(text="📊 Рыночный обзор", callback_data="crypto_market_overview")
            .button(text="🔔 Уведомления", callback_data="crypto_alerts")
            .button(text="📈 Smart Money", callback_data="crypto_smart_money")
            .button(text="🔍 Поиск монеты", callback_data="crypto_search_coin")
            .adjust(1)
            .as_markup(),
        parse_mode="Markdown"
    )

@router.callback_query(F.data == "crypto_back_to_main")
async def callback_back_to_main(callback: CallbackQuery):
    """
    Обработчик для кнопки "Назад" в криптомодуле
    """
    await callback.answer()
    
    # Возвращаемся в главное меню криптомодуля
    await callback.message.edit_text(
        "🪙 *Криптовалютный модуль*\n\n"
        "Выберите действие из меню ниже:",
        reply_markup=InlineKeyboardBuilder()
            .button(text="📊 Рыночный обзор", callback_data="crypto_market_overview")
            .button(text="🔔 Уведомления", callback_data="crypto_alerts")
            .button(text="📈 Smart Money", callback_data="crypto_smart_money")
            .button(text="🔍 Поиск монеты", callback_data="crypto_search_coin")
            .adjust(1)
            .as_markup(),
        parse_mode="Markdown"
    )

@router.message(Command("update_interval"))
async def cmd_update_interval(message: Message):
    """
    Обработчик команды /update_interval
    Отображает интервал обновления данных
    """
    if not data_manager:
        await message.reply("⚠️ Менеджер данных не инициализирован")
        return
    
    if data_manager.last_api_update:
        last_update_str = data_manager.last_api_update.strftime('%Y-%m-%d %H:%M:%S')
    else:
        last_update_str = "Нет данных о последнем обновлении"
    
    interval_minutes = data_manager.min_update_interval.total_seconds() / 60
    
    result = (
        f"🔄 Интервал обновления данных: {interval_minutes} минут\n"
        f"🕒 Последнее обновление: {last_update_str}\n\n"
        "Для изменения интервала используйте команду /set_interval <минут>"
    )
    
    await message.reply(result)

@router.message(Command("set_interval"))
async def cmd_set_interval(message: Message):
    """
    Обработчик команды /set_interval
    Устанавливает новый интервал обновления данных
    """
    if not data_manager:
        await message.reply("⚠️ Менеджер данных не инициализирован")
        return
    
    # Получаем аргументы команды
    args = message.text.split()[1:]
    
    if not args:
        await message.reply("⚠️ Не указано новое значение интервала в минутах")
        return
    
    try:
        new_interval = int(args[0])
        if new_interval < 60:
            await message.reply("⚠️ Новый интервал не может быть меньше 60 минут")
            return
        
        # Устанавливаем новый интервал
        data_manager.min_update_interval = timedelta(minutes=new_interval)
        
        # Сохраняем новую конфигурацию в файле
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if config and "background" in config:
                config["background"]["update_interval"] = new_interval * 60  # Сохраняем в секундах
                
                with open(config_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
                
            logger.info(f"Интервал обновления установлен в {new_interval} минут")
            await message.reply(f"✅ Интервал обновления установлен в {new_interval} минут")
        except Exception as e:
            logger.error(f"Ошибка при сохранении нового интервала обновления: {e}")
            await message.reply(f"❌ Ошибка при установке интервала обновления: {str(e)}")n