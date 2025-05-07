import logging
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from .config import crypto_config

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для обработчиков команд криптовалютного меню
crypto_menu_router = Router()

# Глобальная переменная для хранения экземпляра бота
bot_instance = None

# Функция для установки экземпляра бота
def set_bot(bot):
    global bot_instance
    bot_instance = bot

# Клавиатуры
def get_crypto_main_menu():
    """Создает основную клавиатуру для криптовалютного модуля"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Анализ рынка"), KeyboardButton(text="🔍 Мониторинг")],
            [KeyboardButton(text="📈 Торговые пары"), KeyboardButton(text="📉 Сигналы")],
            [KeyboardButton(text="⚙️ Настройки крипто"), KeyboardButton(text="🔙 Назад к боту")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_crypto_analysis_menu():
    """Создает клавиатуру для меню анализа"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Объемы"), KeyboardButton(text="💰 Фандинг")],
            [KeyboardButton(text="🐋 Киты"), KeyboardButton(text="📈 Ликвидность")],
            [KeyboardButton(text="🔙 Назад к крипто")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_crypto_pairs_menu():
    """Создает клавиатуру для меню торговых пар"""
    # Получаем текущие пары из конфигурации
    pairs = crypto_config.get('monitoring', {}).get('pairs', ['BTCUSDT', 'ETHUSDT'])
    
    # Создаем кнопки для каждой пары (по 2 в строке)
    pair_buttons = []
    row = []
    
    for i, pair in enumerate(pairs):
        row.append(KeyboardButton(text=f"{pair}"))
        
        # Добавляем по 2 кнопки в строку
        if len(row) == 2 or i == len(pairs) - 1:
            pair_buttons.append(row)
            row = []
    
    # Добавляем кнопки управления
    pair_buttons.append([
        KeyboardButton(text="➕ Добавить пару"), 
        KeyboardButton(text="➖ Удалить пару")
    ])
    pair_buttons.append([KeyboardButton(text="🔙 Назад к крипто")])
    
    return ReplyKeyboardMarkup(keyboard=pair_buttons, resize_keyboard=True)

# Обработчики команд
@crypto_menu_router.message(F.text == "📊 Анализ рынка")
async def crypto_analysis(message: types.Message):
    """Обработчик кнопки 'Анализ рынка'"""
    logger.info(f"Пользователь {message.from_user.id} выбрал 'Анализ рынка'")
    
    await message.answer(
        "📊 Анализ рынка\n\n"
        "Выберите тип анализа:",
        reply_markup=get_crypto_analysis_menu()
    )

@crypto_menu_router.message(F.text == "🔍 Мониторинг")
async def crypto_monitoring(message: types.Message):
    """Обработчик кнопки 'Мониторинг'"""
    logger.info(f"Пользователь {message.from_user.id} выбрал 'Мониторинг'")
    
    # Импортируем функцию из telegram_interface
    from .telegram_interface import process_crypto_monitoring, bot_instance
    
    # Создаем временное сообщение
    temp_msg = await message.answer("⏳ Загрузка информации о мониторинге...")
    
    # Создаем callback-запрос для использования существующего обработчика
    callback = types.CallbackQuery(
        id="crypto_monitoring",
        from_user=message.from_user,
        chat_instance=str(message.chat.id),
        message=temp_msg,
        data="crypto_monitoring"
    )
    
    # Устанавливаем бота для callback
    callback.bot = bot_instance
    
    # Вызываем обработчик
    await process_crypto_monitoring(callback)

@crypto_menu_router.message(F.text == "📈 Торговые пары")
async def crypto_pairs(message: types.Message):
    """Обработчик кнопки 'Торговые пары'"""
    logger.info(f"Пользователь {message.from_user.id} выбрал 'Торговые пары'")
    
    # Получаем текущие пары
    pairs = crypto_config.get('monitoring', {}).get('pairs', ['BTCUSDT', 'ETHUSDT'])
    
    await message.answer(
        "📈 Управление торговыми парами\n\n"
        f"Текущие пары: {', '.join(pairs)}\n\n"
        "Выберите пару для просмотра или действие:",
        reply_markup=get_crypto_pairs_menu()
    )

@crypto_menu_router.message(F.text == "📉 Сигналы")
async def crypto_signals(message: types.Message):
    """Обработчик кнопки 'Сигналы'"""
    logger.info(f"Пользователь {message.from_user.id} выбрал 'Сигналы'")
    
    # Получаем настройки сигналов
    signals_enabled = crypto_config.get('signals', {}).get('enabled', True)
    channel_id = crypto_config.get('signals', {}).get('channel_id')
    include_charts = crypto_config.get('signals', {}).get('include_charts', True)
    
    status = "✅ Включены" if signals_enabled else "❌ Отключены"
    channel = f"@{channel_id}" if channel_id else "Не настроен"
    charts = "✅ Включены" if include_charts else "❌ Отключены"
    
    await message.answer(
        "📉 Настройки сигналов\n\n"
        f"Статус: {status}\n"
        f"Канал: {channel}\n"
        f"Графики: {charts}\n\n"
        "Для изменения настроек используйте меню 'Настройки крипто'",
        reply_markup=get_crypto_main_menu()
    )

@crypto_menu_router.message(F.text == "⚙️ Настройки крипто")
async def crypto_settings(message: types.Message):
    """Обработчик кнопки 'Настройки крипто'"""
    logger.info(f"Пользователь {message.from_user.id} выбрал 'Настройки крипто'")
    
    # Импортируем функцию из telegram_interface
    from .telegram_interface import get_crypto_settings_keyboard, bot_instance
    
    # Отправляем сообщение с настройками
    await message.answer(
        "⚙️ Настройки криптовалютного модуля\n\n"
        "Здесь вы можете настроить параметры мониторинга и анализа.",
        reply_markup=get_crypto_settings_keyboard()
    )

@crypto_menu_router.message(F.text == "🔙 Назад к крипто")
async def back_to_crypto(message: types.Message):
    """Обработчик кнопки 'Назад к крипто'"""
    logger.info(f"Пользователь {message.from_user.id} вернулся в главное меню крипто")
    
    await message.answer(
        "🚀 Криптовалютный анализатор Smart Money\n\n"
        "Выберите действие:",
        reply_markup=get_crypto_main_menu()
    )

@crypto_menu_router.message(F.text == "🔙 Назад к боту")
async def back_to_bot(message: types.Message):
    """Обработчик кнопки 'Назад к боту'"""
    logger.info(f"Пользователь {message.from_user.id} вернулся в главное меню бота")
    
    # Импортируем функцию из handlers
    from handlers import get_main_keyboard, ADMIN_ID
    
    # Возвращаемся в главное меню бота
    is_admin = message.from_user.id == ADMIN_ID
    await message.answer(
        "Вы вернулись в главное меню бота.",
        reply_markup=get_main_keyboard(is_admin)
    )

# Обработчики для подменю анализа
@crypto_menu_router.message(F.text == "📊 Объемы")
async def crypto_volumes(message: types.Message):
    """Обработчик кнопки 'Объемы'"""
    logger.info(f"Пользователь {message.from_user.id} выбрал анализ объемов")
    
    await message.answer(
        "⏳ Анализ объемов торгов...\n\n"
        "Это может занять некоторое время."
    )
    
    # Импортируем необходимые классы
    from .data_sources import DataSourceManager
    from .smart_money_analyzer import SmartMoneyAnalyzer
    
    try:
        # Инициализируем источники данных
        data_manager = DataSourceManager()
        await data_manager.initialize()
        
        # Создаем анализатор
        analyzer = SmartMoneyAnalyzer(data_manager)
        
        # Анализируем объемы для всех пар
        results = {}
        for pair in analyzer.pairs:
            volume_signals = await analyzer.analyze_volumes(pair)
            if volume_signals:
                results[pair] = volume_signals
        
        # Формируем сообщение с результатами
        if results:
            message_text = "📊 Результаты анализа объемов:\n\n"
            
            for pair, signals in results.items():
                message_text += f"**{pair}**\n"
                
                for signal in signals:
                    direction = "🟢 LONG" if signal.get("direction") == "long" else "🔴 SHORT"
                    timeframe = signal.get("timeframe", "")
                    ratio = signal.get("ratio", 0)
                    
                    message_text += f"{direction} ({timeframe}): объем в {ratio:.2f}x раз выше среднего\n"
                
                message_text += "\n"
        else:
            message_text = "📊 Анализ объемов:\n\nНе обнаружено значительных всплесков объема."
        
        # Закрываем соединения
        await data_manager.close()
        
        # Отправляем результаты
        await message.answer(message_text, reply_markup=get_crypto_analysis_menu())
    
    except Exception as e:
        logger.error(f"Ошибка при анализе объемов: {e}")
        await message.answer(
            f"❌ Произошла ошибка при анализе объемов: {e}",
            reply_markup=get_crypto_analysis_menu()
        )

@crypto_menu_router.message(F.text == "💰 Фандинг")
async def crypto_funding(message: types.Message):
    """Обработчик кнопки 'Фандинг'"""
    logger.info(f"Пользователь {message.from_user.id} выбрал анализ фандинга")
    
    await message.answer(
        "⏳ Анализ Funding Rate...\n\n"
        "Это может занять некоторое время."
    )
    
    # Импортируем необходимые классы
    from .data_sources import DataSourceManager
    from .smart_money_analyzer import SmartMoneyAnalyzer
    
    try:
        # Инициализируем источники данных
        data_manager = DataSourceManager()
        await data_manager.initialize()
        
        # Создаем анализатор
        analyzer = SmartMoneyAnalyzer(data_manager)
        
        # Анализируем Funding Rate для всех пар
        results = {}
        for pair in analyzer.pairs:
            funding_signals = await analyzer.analyze_funding_rate(pair)
            if funding_signals:
                results[pair] = funding_signals
        
        # Формируем сообщение с результатами
        if results:
            message_text = "💰 Результаты анализа Funding Rate:\n\n"
            
            for pair, signals in results.items():
                message_text += f"**{pair}**\n"
                
                for signal in signals:
                    direction = "🟢 LONG" if signal.get("direction") == "long" else "🔴 SHORT"
                    funding_rate = signal.get("funding_rate", 0)
                    
                    message_text += f"{direction}: Funding Rate = {funding_rate:.4f}%\n"
                
                message_text += "\n"
        else:
            message_text = "💰 Анализ Funding Rate:\n\nНе обнаружено значительных отклонений Funding Rate."
        
        # Закрываем соединения
        await data_manager.close()
        
        # Отправляем результаты
        await message.answer(message_text, reply_markup=get_crypto_analysis_menu())
    
    except Exception as e:
        logger.error(f"Ошибка при анализе Funding Rate: {e}")
        await message.answer(
            f"❌ Произошла ошибка при анализе Funding Rate: {e}",
            reply_markup=get_crypto_analysis_menu()
        )

# Функция для регистрации обработчиков
def register_crypto_menu_handlers(dp):
    """Регистрация обработчиков команд меню криптовалютного модуля"""
    logger.info("Регистрация обработчиков команд меню криптовалютного модуля")
    
    # Получаем экземпляр бота из глобальной переменной в handlers.py
    from handlers import bot_instance
    set_bot(bot_instance)
    
    dp.include_router(crypto_menu_router)