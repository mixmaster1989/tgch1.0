import logging
import asyncio
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from .config import crypto_config
from .smart_money_analyzer import SmartMoneyAnalyzer
from .data_sources import DataSourceManager
from .signal_dispatcher import SignalDispatcher

# Настройка логирования
logger = logging.getLogger(__name__)

# Создаем роутер для обработчиков команд криптовалютного модуля
crypto_router = Router()

# Глобальные переменные для хранения экземпляров классов
data_manager = None
analyzer = None
signal_dispatcher = None
monitoring_task = None
bot_instance = None

# Функция для установки экземпляра бота
def set_bot(bot):
    global bot_instance
    bot_instance = bot

# Клавиатуры
def get_crypto_keyboard():
    """Создает клавиатуру для криптовалютного модуля"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Анализ рынка", callback_data="crypto_analyze"),
            InlineKeyboardButton(text="🔍 Мониторинг", callback_data="crypto_monitoring")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="crypto_settings"),
            InlineKeyboardButton(text="ℹ️ Помощь", callback_data="crypto_help")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="crypto_back")
        ]
    ])
    return keyboard

def get_crypto_settings_keyboard():
    """Создает клавиатуру настроек криптовалютного модуля"""
    # Получаем текущие настройки
    monitoring_enabled = crypto_config.get('signals', {}).get('enabled', True)
    include_charts = crypto_config.get('signals', {}).get('include_charts', True)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"{'✅' if monitoring_enabled else '❌'} Мониторинг", 
                callback_data="crypto_toggle_monitoring"
            ),
            InlineKeyboardButton(
                text=f"{'✅' if include_charts else '❌'} Графики", 
                callback_data="crypto_toggle_charts"
            )
        ],
        [
            InlineKeyboardButton(text="🔢 Торговые пары", callback_data="crypto_pairs"),
            InlineKeyboardButton(text="⏱ Таймфреймы", callback_data="crypto_timeframes")
        ],
        [
            InlineKeyboardButton(text="🔑 API ключи", callback_data="crypto_api_keys")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="crypto_back_to_main")
        ]
    ])
    return keyboard

def get_crypto_pairs_keyboard():
    """Создает клавиатуру для выбора торговых пар"""
    # Получаем текущие пары
    pairs = crypto_config.get('monitoring', {}).get('pairs', ['BTCUSDT', 'ETHUSDT'])
    
    # Создаем кнопки для каждой пары
    pair_buttons = []
    for i in range(0, len(pairs), 2):
        row = []
        for j in range(2):
            if i + j < len(pairs):
                pair = pairs[i + j]
                row.append(InlineKeyboardButton(text=pair, callback_data=f"crypto_pair_{pair}"))
        pair_buttons.append(row)
    
    # Добавляем кнопки управления
    pair_buttons.append([
        InlineKeyboardButton(text="➕ Добавить", callback_data="crypto_add_pair"),
        InlineKeyboardButton(text="🔙 Назад", callback_data="crypto_back_to_settings")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=pair_buttons)

# Обработчики команд
@crypto_router.message(Command("crypto"))
async def cmd_crypto(message: types.Message):
    """Обработчик команды /crypto"""
    logger.info(f"Пользователь {message.from_user.id} запустил команду /crypto")
    
    # Импортируем функцию из main_menu
    from .main_menu import get_crypto_main_menu
    
    await message.answer(
        "🚀 Криптовалютный анализатор Smart Money\n\n"
        "Этот модуль позволяет отслеживать активность крупных игроков (Smart Money) "
        "на криптовалютном рынке и получать сигналы о потенциальных движениях цены.\n\n"
        "Выберите действие:",
        reply_markup=get_crypto_main_menu()
    )

# Обработчики callback-запросов
@crypto_router.callback_query(F.data == "crypto_back")
async def process_crypto_back(callback: types.CallbackQuery):
    """Обработчик кнопки 'Назад'"""
    logger.info(f"Пользователь {callback.from_user.id} нажал кнопку 'Назад'")
    
    await callback.message.delete()

@crypto_router.callback_query(F.data == "crypto_analyze")
async def process_crypto_analyze(callback: types.CallbackQuery):
    """Обработчик кнопки 'Анализ рынка'"""
    logger.info(f"Пользователь {callback.from_user.id} запросил анализ рынка")
    
    # Проверяем, инициализированы ли необходимые компоненты
    global data_manager, analyzer
    
    if not data_manager:
        data_manager = DataSourceManager()
        await data_manager.initialize()
    
    if not analyzer:
        analyzer = SmartMoneyAnalyzer(data_manager)
    
    # Отправляем сообщение о начале анализа
    await callback.message.edit_text(
        "⏳ Выполняется анализ рынка...\n\n"
        "Это может занять некоторое время. Пожалуйста, подождите."
    )
    
    try:
        # Запускаем анализ
        results = await analyzer.run_analysis()
        
        # Формируем сообщение с результатами
        message_text = "📊 Результаты анализа рынка:\n\n"
        
        for pair, pair_results in results.items():
            signals = pair_results.get("signals", [])
            price = pair_results.get("price")
            
            if signals:
                # Группируем сигналы по типу
                signal_types = {}
                for signal in signals:
                    signal_type = signal.get("type")
                    if signal_type not in signal_types:
                        signal_types[signal_type] = []
                    signal_types[signal_type].append(signal)
                
                message_text += f"**{pair}** - ${price:.2f}\n"
                
                for signal_type, type_signals in signal_types.items():
                    # Определяем общее направление сигналов
                    long_count = sum(1 for s in type_signals if s.get("direction") == "long")
                    short_count = sum(1 for s in type_signals if s.get("direction") == "short")
                    
                    direction = "LONG" if long_count > short_count else "SHORT"
                    direction_emoji = "🟢" if direction == "LONG" else "🔴"
                    
                    message_text += f"{direction_emoji} {signal_type.replace('_', ' ').title()}: {direction}\n"
                
                message_text += "\n"
        
        if message_text == "📊 Результаты анализа рынка:\n\n":
            message_text += "Сигналов не обнаружено."
        
        # Отправляем результаты
        await callback.message.edit_text(
            message_text,
            reply_markup=get_crypto_keyboard()
        )
    except Exception as e:
        logger.error(f"Ошибка при анализе рынка: {e}")
        await callback.message.edit_text(
            f"❌ Произошла ошибка при анализе рынка: {e}",
            reply_markup=get_crypto_keyboard()
        )

@crypto_router.callback_query(F.data == "crypto_monitoring")
async def process_crypto_monitoring(callback: types.CallbackQuery):
    """Обработчик кнопки 'Мониторинг'"""
    logger.info(f"Пользователь {callback.from_user.id} запросил управление мониторингом")
    
    global monitoring_task
    
    # Проверяем, запущен ли мониторинг
    is_monitoring_active = monitoring_task is not None and not monitoring_task.done()
    
    # Формируем сообщение
    message_text = "🔍 Управление мониторингом\n\n"
    message_text += f"Статус: {'✅ Активен' if is_monitoring_active else '❌ Неактивен'}\n\n"
    
    # Получаем настройки мониторинга
    pairs = crypto_config.get('monitoring', {}).get('pairs', [])
    timeframes = crypto_config.get('monitoring', {}).get('timeframes', [])
    
    message_text += f"Отслеживаемые пары: {', '.join(pairs)}\n"
    message_text += f"Таймфреймы: {', '.join(timeframes)}\n\n"
    
    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="⏹ Остановить" if is_monitoring_active else "▶️ Запустить", 
                callback_data="crypto_toggle_monitoring_task"
            )
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="crypto_back_to_main")
        ]
    ])
    
    await callback.message.edit_text(message_text, reply_markup=keyboard)

@crypto_router.callback_query(F.data == "crypto_toggle_monitoring_task")
async def process_toggle_monitoring(callback: types.CallbackQuery):
    """Обработчик кнопки включения/выключения мониторинга"""
    logger.info(f"Пользователь {callback.from_user.id} переключает статус мониторинга")
    
    global monitoring_task, data_manager, analyzer, signal_dispatcher
    
    # Проверяем, запущен ли мониторинг
    is_monitoring_active = monitoring_task is not None and not monitoring_task.done()
    
    if is_monitoring_active:
        # Останавливаем мониторинг
        monitoring_task.cancel()
        await callback.message.edit_text("Мониторинг остановлен")
        logger.info("Мониторинг остановлен")
    else:
        # Инициализируем компоненты, если необходимо
        if not data_manager:
            data_manager = DataSourceManager()
            await data_manager.initialize()
        
        if not analyzer:
            analyzer = SmartMoneyAnalyzer(data_manager)
        
        if not signal_dispatcher:
            signal_dispatcher = SignalDispatcher()
            # Получаем экземпляр бота из глобальной переменной
            signal_dispatcher.set_bot(bot_instance)
        
        # Запускаем мониторинг
        monitoring_task = asyncio.create_task(run_monitoring(analyzer, signal_dispatcher))
        await callback.message.edit_text("Мониторинг запущен")
        logger.info("Мониторинг запущен")
    
    # Обновляем сообщение
    await process_crypto_monitoring(callback)

@crypto_router.callback_query(F.data == "crypto_settings")
async def process_crypto_settings(callback: types.CallbackQuery):
    """Обработчик кнопки 'Настройки'"""
    logger.info(f"Пользователь {callback.from_user.id} открыл настройки криптовалютного модуля")
    
    await callback.message.edit_text(
        "⚙️ Настройки криптовалютного модуля\n\n"
        "Здесь вы можете настроить параметры мониторинга и анализа.",
        reply_markup=get_crypto_settings_keyboard()
    )

@crypto_router.callback_query(F.data == "crypto_help")
async def process_crypto_help(callback: types.CallbackQuery):
    """Обработчик кнопки 'Помощь'"""
    logger.info(f"Пользователь {callback.from_user.id} запросил помощь по криптовалютному модулю")
    
    help_text = (
        "ℹ️ Помощь по криптовалютному модулю\n\n"
        "Этот модуль позволяет отслеживать активность крупных игроков (Smart Money) "
        "на криптовалютном рынке и получать сигналы о потенциальных движениях цены.\n\n"
        
        "📊 **Анализ рынка** - выполняет одноразовый анализ выбранных торговых пар "
        "и показывает результаты.\n\n"
        
        "🔍 **Мониторинг** - запускает постоянное отслеживание рынка и отправляет "
        "уведомления при обнаружении сигналов.\n\n"
        
        "⚙️ **Настройки** - позволяет настроить параметры мониторинга, выбрать "
        "торговые пары и указать API ключи.\n\n"
        
        "Отслеживаемые метрики:\n"
        "- Всплески объемов торгов\n"
        "- Изменения Open Interest\n"
        "- Funding Rate\n"
        "- Транзакции китов\n"
        "- Зоны ликвидности\n"
        "- Order Blocks\n\n"
        
        "Команды:\n"
        "/crypto - открыть меню криптовалютного модуля\n"
        "/crypto_analyze - выполнить анализ рынка\n"
        "/crypto_start - запустить мониторинг\n"
        "/crypto_stop - остановить мониторинг"
    )
    
    await callback.message.edit_text(
        help_text,
        reply_markup=get_crypto_keyboard()
    )

@crypto_router.callback_query(F.data == "crypto_back_to_main")
async def process_back_to_main(callback: types.CallbackQuery):
    """Обработчик кнопки 'Назад' в подменю"""
    logger.info(f"Пользователь {callback.from_user.id} вернулся в главное меню криптовалютного модуля")
    
    await callback.message.edit_text(
        "🚀 Криптовалютный анализатор Smart Money\n\n"
        "Этот модуль позволяет отслеживать активность крупных игроков (Smart Money) "
        "на криптовалютном рынке и получать сигналы о потенциальных движениях цены.\n\n"
        "Выберите действие:",
        reply_markup=get_crypto_keyboard()
    )

@crypto_router.callback_query(F.data == "crypto_back_to_settings")
async def process_back_to_settings(callback: types.CallbackQuery):
    """Обработчик кнопки 'Назад' в настройках"""
    logger.info(f"Пользователь {callback.from_user.id} вернулся в меню настроек")
    
    await process_crypto_settings(callback)

@crypto_router.callback_query(F.data == "crypto_pairs")
async def process_crypto_pairs(callback: types.CallbackQuery):
    """Обработчик кнопки 'Торговые пары'"""
    logger.info(f"Пользователь {callback.from_user.id} открыл настройки торговых пар")
    
    # Получаем текущие пары
    pairs = crypto_config.get('monitoring', {}).get('pairs', ['BTCUSDT', 'ETHUSDT'])
    
    await callback.message.edit_text(
        "🔢 Настройка торговых пар\n\n"
        f"Текущие пары: {', '.join(pairs)}\n\n"
        "Выберите пару для удаления или добавьте новую:",
        reply_markup=get_crypto_pairs_keyboard()
    )

# Функция для запуска мониторинга
async def run_monitoring(analyzer, signal_dispatcher, interval=300):
    """
    Запускает мониторинг рынка с периодическим анализом
    
    Args:
        analyzer (SmartMoneyAnalyzer): Анализатор Smart Money
        signal_dispatcher (SignalDispatcher): Диспетчер сигналов
        interval (int): Интервал между проверками в секундах
    """
    logger.info(f"Запущен мониторинг с интервалом {interval} секунд")
    
    try:
        while True:
            try:
                # Выполняем анализ
                results = await analyzer.run_analysis()
                
                # Отправляем сигналы
                sent_count = await signal_dispatcher.dispatch_signals(results)
                
                if sent_count > 0:
                    logger.info(f"Отправлено {sent_count} сигналов")
                else:
                    logger.info("Сигналов не обнаружено")
                
                # Ждем до следующей проверки
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger.info("Мониторинг отменен")
                break
            except Exception as e:
                logger.error(f"Ошибка при выполнении мониторинга: {e}")
                # Ждем перед повторной попыткой
                await asyncio.sleep(60)
    finally:
        logger.info("Мониторинг остановлен")

# Дополнительные обработчики команд
@crypto_router.message(Command("crypto_analyze"))
async def cmd_crypto_analyze(message: types.Message):
    """Обработчик команды /crypto_analyze"""
    logger.info(f"Пользователь {message.from_user.id} запустил команду /crypto_analyze")
    
    # Создаем сообщение
    msg = await message.answer("⏳ Запуск анализа рынка...")
    
    # Создаем callback-запрос для использования существующего обработчика
    callback = types.CallbackQuery(
        id="crypto_analyze",
        from_user=message.from_user,
        chat_instance=str(message.chat.id),
        message=msg,
        data="crypto_analyze"
    )
    
    # Устанавливаем бота для callback
    callback.bot = bot_instance
    
    # Вызываем обработчик
    await process_crypto_analyze(callback)

@crypto_router.message(Command("crypto_start"))
async def cmd_crypto_start(message: types.Message):
    """Обработчик команды /crypto_start"""
    logger.info(f"Пользователь {message.from_user.id} запустил команду /crypto_start")
    
    global monitoring_task, data_manager, analyzer, signal_dispatcher
    
    # Проверяем, запущен ли мониторинг
    is_monitoring_active = monitoring_task is not None and not monitoring_task.done()
    
    if is_monitoring_active:
        await message.answer("⚠️ Мониторинг уже запущен")
        return
    
    # Инициализируем компоненты, если необходимо
    if not data_manager:
        data_manager = DataSourceManager()
        await data_manager.initialize()
    
    if not analyzer:
        analyzer = SmartMoneyAnalyzer(data_manager)
    
    if not signal_dispatcher:
        signal_dispatcher = SignalDispatcher()
        signal_dispatcher.set_bot(bot_instance)
    
    # Запускаем мониторинг
    monitoring_task = asyncio.create_task(run_monitoring(analyzer, signal_dispatcher))
    
    await message.answer("✅ Мониторинг запущен")
    logger.info("Мониторинг запущен через команду /crypto_start")

@crypto_router.message(Command("crypto_stop"))
async def cmd_crypto_stop(message: types.Message):
    """Обработчик команды /crypto_stop"""
    logger.info(f"Пользователь {message.from_user.id} запустил команду /crypto_stop")
    
    global monitoring_task
    
    # Проверяем, запущен ли мониторинг
    is_monitoring_active = monitoring_task is not None and not monitoring_task.done()
    
    if not is_monitoring_active:
        await message.answer("⚠️ Мониторинг не запущен")
        return
    
    # Останавливаем мониторинг
    monitoring_task.cancel()
    
    await message.answer("✅ Мониторинг остановлен")
    logger.info("Мониторинг остановлен через команду /crypto_stop")

# Функция для регистрации обработчиков
def register_crypto_handlers(dp):
    """Регистрация обработчиков команд криптовалютного модуля"""
    logger.info("Регистрация обработчиков команд криптовалютного модуля")
    
    # Получаем экземпляр бота из глобальной переменной в handlers.py
    from handlers import bot_instance
    set_bot(bot_instance)
    
    dp.include_router(crypto_router)