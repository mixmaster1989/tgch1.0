import logging
import traceback
import sys
import yaml
import os
from aiogram import Router, types, F, Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from .config import crypto_config, load_crypto_config # Предполагаем, что load_crypto_config есть в config.py
from .smart_money_analyzer import SmartMoneyAnalyzer # Импортируем анализатор
from .data_sources import DataSourceManager # Импортируем менеджер источников данных

# Настройка подробного логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Добавляем обработчик для вывода в консоль
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Функция для логирования с трассировкой стека
def log_exception(e, message="Произошла ошибка"):
    logger.error(f"{message}: {str(e)}")
    logger.error(traceback.format_exc())

# Создаем роутер для обработчиков команд криптовалютного интерфейса
crypto_router = Router()

# Глобальная переменная для хранения экземпляра бота
bot_instance: Bot = None

# Глобальный словарь для отслеживания состояний пользователей
user_states = {} # {user_id: {'state': 'waiting_api_key', 'api_type': 'binance'}}

# Функция для установки экземпляра бота
def set_bot(bot: Bot):
    global bot_instance
    bot_instance = bot
    logger.debug(f"Экземпляр бота установлен в telegram_interface: {bot_instance}")

# Функция для сохранения крипто конфигурации
def save_crypto_config():
    try:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'crypto_config.yaml')
        with open(config_path, 'w', encoding='utf-8') as file:
            yaml.dump(crypto_config, file, default_flow_style=False)
        logger.debug(f"Крипто конфигурация сохранена в {config_path}")
    except Exception as e:
        log_exception(e, "Ошибка при сохранении крипто конфигурации")

# Клавиатуры
def get_crypto_settings_keyboard():
    """Создает инлайн-клавиатуру для настроек крипто модуля"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔑 Настроить API ключи", callback_data="crypto_settings_api_keys")],
        [InlineKeyboardButton(text="📈 Настроить торговые пары", callback_data="crypto_settings_pairs")],
        [InlineKeyboardButton(text="🔔 Настроить сигналы", callback_data="crypto_settings_signals")],
        [InlineKeyboardButton(text="🔙 Назад к крипто настройкам", callback_data="crypto_settings_back")]
    ])
    return keyboard

def get_api_key_settings_keyboard():
    """Создает инлайн-клавиатуру для выбора типа API ключа"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Binance", callback_data="crypto_settings_api_binance")],
        # [InlineKeyboardButton(text="Bybit", callback_data="crypto_settings_api_bybit")], # Пример для других бирж
        [InlineKeyboardButton(text="🔙 Назад к настройкам крипто", callback_data="crypto_settings_back")]
    ])
    return keyboard

def get_signal_settings_keyboard():
    """Создает инлайн-клавиатуру для настроек сигналов"""
    signals_enabled = crypto_config.get('signals', {}).get('enabled', True)
    include_charts = crypto_config.get('signals', {}).get('include_charts', True)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Сигналы: {'✅ Вкл' if signals_enabled else '❌ Выкл'}", callback_data="crypto_settings_signals_toggle")],
        [InlineKeyboardButton(text="Канал для сигналов", callback_data="crypto_settings_signals_channel")],
        [InlineKeyboardButton(text=f"Графики в сигналах: {'✅ Вкл' if include_charts else '❌ Выкл'}", callback_data="crypto_settings_signals_charts_toggle")],
        [InlineKeyboardButton(text="Кулдаун уведомлений", callback_data="crypto_settings_signals_cooldown")],
        [InlineKeyboardButton(text="🔙 Назад к настройкам крипто", callback_data="crypto_settings_back")]
    ])
    return keyboard


# --- Обработчики команд и кнопок главного крипто меню (вызываются из main_menu.py) ---

# Обработчик команды /crypto или кнопки "📈 Крипто анализ"
# Этот обработчик теперь просто вызывает меню из main_menu.py
@crypto_router.message(Command("crypto"))
@crypto_router.message(F.text == "📈 Крипто анализ")
async def cmd_crypto(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запросил крипто анализ")
    # Проверяем, что команду отправил администратор (если нужно)
    # from handlers import ADMIN_ID # Предполагаем, что ADMIN_ID определен в handlers.py
    # if message.from_user.id != ADMIN_ID:
    #     await message.answer("Эта функция доступна только администратору.")
    #     return

    # Импортируем функцию получения крипто меню из main_menu.py
    from .main_menu import get_crypto_main_menu

    await message.answer(
        "🚀 Криптовалютный анализатор Smart Money\n\nВыберите действие:",
        reply_markup=get_crypto_main_menu()
    )

# --- Обработчики для подменю анализа (вызываются из main_menu.py) ---

# Обработчик кнопки "🐋 Киты"
@crypto_router.message(F.text == "🐋 Киты")
async def crypto_whales(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} выбрал анализ китов")

    await message.answer(
        "⏳ Анализ транзакций китов...\n\n"
        "Это может занять некоторое время."
    )

    try:
        # Инициализируем источники данных
        data_manager = DataSourceManager()
        await data_manager.initialize()

        # Создаем анализатор
        analyzer = SmartMoneyAnalyzer(data_manager)

        # Анализируем транзакции китов для всех пар
        results = {}
        # Используем пары из конфигурации
        pairs_to_analyze = crypto_config.get('monitoring', {}).get('pairs', [])
        if not pairs_to_analyze:
             await message.answer("⚠️ Не настроены торговые пары для анализа.")
             await data_manager.close()
             return

        for pair in pairs_to_analyze:
            whale_signals = await analyzer.analyze_whale_transactions(pair)
            if whale_signals:
                results[pair] = whale_signals

        # Формируем сообщение с результатами
        if results:
            message_text = "🐋 Результаты анализа транзакций китов:\n\n"

            for pair, signals in results.items():
                message_text += f"**{pair}**\n"

                for signal in signals:
                    direction = "🟢 LONG" if signal.get("direction") == "long" else "🔴 SHORT"
                    amount_usd = signal.get("amount_usd", 0)

                    message_text += f"{direction}: транзакция на ${amount_usd:,.2f}\n"

                message_text += "\n"
        else:
            message_text = "🐋 Анализ транзакций китов:\n\nНе обнаружено значительных транзакций китов."

        # Закрываем соединения
        await data_manager.close()

        # Отправляем результаты
        from .main_menu import get_crypto_analysis_menu
        await message.answer(message_text, reply_markup=get_crypto_analysis_menu())

    except Exception as e:
        log_exception(e, "Ошибка при анализе китов")
        from .main_menu import get_crypto_analysis_menu
        await message.answer(
            f"❌ Произошла ошибка при анализе китов: {e}",
            reply_markup=get_crypto_analysis_menu()
        )

# Обработчик кнопки "📈 Ликвидность"
@crypto_router.message(F.text == "📈 Ликвидность")
async def crypto_liquidity(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} выбрал анализ ликвидности")

    await message.answer(
        "⏳ Анализ зон ликвидности...\n\n"
        "Это может занять некоторое время."
    )

    try:
        # Инициализируем источники данных
        data_manager = DataSourceManager()
        await data_manager.initialize()

        # Создаем анализатор
        analyzer = SmartMoneyAnalyzer(data_manager)

        # Анализируем зоны ликвидности для всех пар
        results = {}
        # Используем пары из конфигурации
        pairs_to_analyze = crypto_config.get('monitoring', {}).get('pairs', [])
        if not pairs_to_analyze:
             await message.answer("⚠️ Не настроены торговые пары для анализа.")
             await data_manager.close()
             return

        for pair in pairs_to_analyze:
            liquidity_signals = await analyzer.analyze_liquidity_zones(pair)
            if liquidity_signals:
                results[pair] = liquidity_signals

        # Формируем сообщение с результатами
        if results:
            message_text = "📈 Результаты анализа зон ликвидности:\n\n"

            for pair, signals in results.items():
                message_text += f"**{pair}**\n"

                for signal in signals:
                    direction = "🟢 LONG" if signal.get("direction") == "long" else "🔴 SHORT"
                    price_level = signal.get("price_level", 0)
                    volume = signal.get("volume", 0)
                    distance_percent = signal.get("distance_percent", 0)

                    message_text += (
                        f"{direction}: уровень ${price_level:.2f} с объемом ${volume:,.0f} "
                        f"({distance_percent:.2f}% от текущей цены)\n"
                    )

                message_text += "\n"
        else:
            message_text = "📈 Анализ зон ликвидности:\n\nНе обнаружено значительных зон ликвидности."

        # Закрываем соединения
        await data_manager.close()

        # Отправляем результаты
        from .main_menu import get_crypto_analysis_menu
        await message.answer(message_text, reply_markup=get_crypto_analysis_menu())

    except Exception as e:
        log_exception(e, "Ошибка при анализе ликвидности")
        from .main_menu import get_crypto_analysis_menu
        await message.answer(
            f"❌ Произошла ошибка при анализе ликвидности: {e}",
            reply_markup=get_crypto_analysis_menu()
        )


# --- Обработчики для меню торговых пар (вызываются из main_menu.py) ---

# Обработчик кнопки "➕ Добавить пару"
@crypto_router.message(F.text == "➕ Добавить пару")
async def add_crypto_pair(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} выбрал 'Добавить пару'")
    user_states[message.from_user.id] = {'state': 'waiting_pair_name'}
    await message.answer("Введите название торговой пары для добавления (например, BTCUSDT):")

# Обработчик кнопки "➖ Удалить пару"
@crypto_router.message(F.text == "➖ Удалить пару")
async def remove_crypto_pair(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} выбрал 'Удалить пару'")
    pairs = crypto_config.get('monitoring', {}).get('pairs', [])
    if not pairs:
        await message.answer("Список отслеживаемых пар пуст.")
        return

    user_states[message.from_user.id] = {'state': 'waiting_pair_to_remove'}
    await message.answer(
        f"Введите название торговой пары для удаления из списка:\n\nТекущие пары: {', '.join(pairs)}"
    )

# Обработчик выбора конкретной пары из меню торговых пар
@crypto_router.message(lambda message: message.text.endswith('USDT') and message.text in crypto_config.get('monitoring', {}).get('pairs', []))
async def view_crypto_pair_details(message: types.Message):
    pair = message.text.strip().upper()
    logger.info(f"Пользователь {message.from_user.id} выбрал пару для просмотра: {pair}")

    # Здесь можно добавить логику для отображения деталей по выбранной паре
    # Например, показать последние сигналы, текущую цену, графики и т.д.
    await message.answer(f"Информация по паре {pair} (в разработке).")


# --- Обработчики для меню настроек крипто (вызываются из main_menu.py) ---

# Обработчик callback-запроса для открытия меню настроек крипто
@crypto_router.callback_query(F.data == "crypto_settings")
async def process_crypto_settings(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} открыл настройки крипто")
    # Проверяем права администратора, если нужно
    # from handlers import ADMIN_ID
    # if callback.from_user.id != ADMIN_ID:
    #     await callback.answer("Эта функция доступна только администратору.")
    #     return

    await callback.message.edit_text(
        "⚙️ Настройки криптовалютного модуля\n\n"
        "Здесь вы можете настроить параметры мониторинга и анализа.",
        reply_markup=get_crypto_settings_keyboard()
    )
    await callback.answer()

# Обработчик callback-запроса для настройки API ключей
@crypto_router.callback_query(F.data == "crypto_settings_api_keys")
async def process_settings_api_keys(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} выбрал настройку API ключей")
    await callback.message.edit_text(
        "🔑 Настройка API ключей\n\n"
        "Выберите биржу, для которой хотите настроить API ключ:",
        reply_markup=get_api_key_settings_keyboard()
    )
    await callback.answer()

# Обработчик callback-запроса для выбора типа API ключа (например, Binance)
@crypto_router.callback_query(F.data.startswith("crypto_settings_api_"))
async def process_settings_select_api_type(callback: types.CallbackQuery):
    api_type = callback.data.split("_")[-1]
    logger.info(f"Пользователь {callback.from_user.id} выбрал настройку API ключа для {api_type}")

    user_states[callback.from_user.id] = {'state': 'waiting_api_key', 'api_type': api_type}

    await callback.message.edit_text(
        f"🔑 Введите ваш API ключ для {api_type.capitalize()}.\n\n"
        "⚠️ **Внимание:** Для вашей безопасности, сообщение с ключом будет удалено после ввода.\n"
        "Пожалуйста, убедитесь, что вы копируете ключ правильно."
    )
    await callback.answer()

# Обработчик callback-запроса для настройки торговых пар
@crypto_router.callback_query(F.data == "crypto_settings_pairs")
async def process_settings_pairs(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} выбрал настройку торговых пар")
    # Импортируем функцию получения меню пар из main_menu.py
    from .main_menu import get_crypto_pairs_menu

    pairs = crypto_config.get('monitoring', {}).get('pairs', ['BTCUSDT', 'ETHUSDT'])

    await callback.message.edit_text(
        "📈 Управление торговыми парами\n\n"
        f"Текущие пары: {', '.join(pairs)}\n\n"
        "Выберите пару для просмотра или действие:",
        reply_markup=get_crypto_pairs_menu() # Используем клавиатуру из main_menu.py
    )
    await callback.answer()

# Обработчик callback-запроса для настройки сигналов
@crypto_router.callback_query(F.data == "crypto_settings_signals")
async def process_settings_signals(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} выбрал настройку сигналов")
    await callback.message.edit_text(
        "🔔 Настройка сигналов\n\n"
        "Управляйте параметрами уведомлений о сигналах.",
        reply_markup=get_signal_settings_keyboard()
    )
    await callback.answer()

# Обработчик callback-запроса для переключения статуса сигналов
@crypto_router.callback_query(F.data == "crypto_settings_signals_toggle")
async def process_settings_signals_toggle(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} переключил статус сигналов")
    signals_config = crypto_config.get('signals', {})
    signals_enabled = signals_config.get('enabled', True)
    signals_config['enabled'] = not signals_enabled
    crypto_config['signals'] = signals_config
    save_crypto_config()

    await callback.message.edit_text(
        "🔔 Настройка сигналов\n\n"
        "Управляйте параметрами уведомлений о сигналах.",
        reply_markup=get_signal_settings_keyboard() # Обновляем клавиатуру
    )
    await callback.answer("Статус сигналов обновлен.")

# Обработчик callback-запроса для настройки канала сигналов
@crypto_router.callback_query(F.data == "crypto_settings_signals_channel")
async def process_settings_signals_channel(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} выбрал настройку канала сигналов")
    user_states[callback.from_user.id] = {'state': 'waiting_signal_channel'}
    await callback.message.edit_text(
        "🔔 Введите ID канала или @username для отправки сигналов.\n\n"
        "Убедитесь, что бот является администратором канала и имеет право отправлять сообщения."
    )
    await callback.answer()

# Обработчик callback-запроса для переключения графиков в сигналах
@crypto_router.callback_query(F.data == "crypto_settings_signals_charts_toggle")
async def process_settings_signals_charts_toggle(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} переключил графики в сигналах")
    signals_config = crypto_config.get('signals', {})
    include_charts = signals_config.get('include_charts', True)
    signals_config['include_charts'] = not include_charts
    crypto_config['signals'] = signals_config
    save_crypto_config()

    await callback.message.edit_text(
        "🔔 Настройка сигналов\n\n"
        "Управляйте параметрами уведомлений о сигналах.",
        reply_markup=get_signal_settings_keyboard() # Обновляем клавиатуру
    )
    await callback.answer("Настройка графиков обновлена.")

# Обработчик callback-запроса для настройки кулдауна сигналов
@crypto_router.callback_query(F.data == "crypto_settings_signals_cooldown")
async def process_settings_signals_cooldown(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} выбрал настройку кулдауна сигналов")
    user_states[callback.from_user.id] = {'state': 'waiting_signal_cooldown'}
    current_cooldown = crypto_config.get('signals', {}).get('notification_cooldown', 3600)
    await callback.message.edit_text(
        f"🔔 Введите время кулдауна между уведомлениями в секундах (текущее: {current_cooldown} сек).\n\n"
        "Например, 3600 для 1 часа."
    )
    await callback.answer()


# Обработчик callback-запроса для возврата из настроек крипто
@crypto_router.callback_query(F.data == "crypto_settings_back")
async def process_settings_back(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} вернулся из настроек крипто")
    # Импортируем функцию получения крипто меню из main_menu.py
    from .main_menu import get_crypto_main_menu

    await callback.message.edit_text(
        "🚀 Криптовалютный анализатор Smart Money\n\nВыберите действие:",
        reply_markup=get_crypto_main_menu()
    )
    await callback.answer()


# --- Обработчик ввода пользователя (для состояний) ---

# Этот обработчик будет ловить текстовые сообщения, когда пользователь находится в состоянии ожидания ввода
@crypto_router.message()
async def process_user_input(message: types.Message):
    """Обработчик ввода пользователя"""
    # Проверяем, находится ли пользователь в каком-либо состоянии ожидания
    global user_states

    user_state = user_states.get(message.from_user.id)
    if not user_state:
        # Если пользователь не в состоянии ожидания, игнорируем сообщение
        return

    state = user_state.get('state')

    if state == 'waiting_api_key':
        # Обработка ввода API ключа
        api_type = user_state.get('api_type')
        logger.info(f"Получен API ключ от пользователя {message.from_user.id} для {api_type}")

        try:
            # Удаляем сообщение с API ключом для безопасности
            await message.delete()

            # Получаем API ключ из сообщения
            api_key = message.text.strip()

            # Обновляем конфигурацию
            if 'api_keys' not in crypto_config:
                crypto_config['api_keys'] = {}

            crypto_config['api_keys'][api_type] = api_key

            # Сохраняем конфигурацию в файл
            save_crypto_config()

            logger.debug(f"API ключ для {api_type} сохранен в конфигурации")

            # Сбрасываем состояние пользователя
            del user_states[message.from_user.id]

            # Отправляем сообщение об успешном сохранении
            await message.answer(
                f"✅ API ключ для {api_type.capitalize()} успешно сохранен.\n\n"
                "Возвращаемся к настройкам API ключей."
            )

            # Создаем временное сообщение для использования в callback
            temp_msg = await message.answer("⏳ Загрузка настроек API ключей...")

            # Создаем callback-запрос для использования существующего обработчика
            # Возвращаемся в меню выбора типа API ключа
            callback = types.CallbackQuery(
                id="crypto_settings_api_keys", # Используем callback_data для возврата в меню выбора типа
                from_user=message.from_user,
                chat_instance=str(message.chat.id),
                message=temp_msg,
                data="crypto_settings_api_keys"
            )

            # Устанавливаем бота для callback
            callback.bot = bot_instance

            # Вызываем обработчик настроек API ключей
            await process_settings_api_keys(callback)

        except Exception as e:
            log_exception(e, f"Ошибка при сохранении API ключа для {api_type} пользователя {message.from_user.id}")
            try:
                await message.answer(
                    f"❌ Произошла ошибка при сохранении API ключа: {e}\n\n"
                    "Пожалуйста, попробуйте еще раз или вернитесь в настройки."
                )
            except Exception as e2:
                log_exception(e2, "Ошибка при отправке сообщения об ошибке")

    elif state == 'waiting_pair_name':
        # Обработка ввода названия торговой пары для добавления
        logger.info(f"Получено название торговой пары от пользователя {message.from_user.id}: {message.text}")

        try:
            # Получаем название пары из сообщения
            pair = message.text.strip().upper()

            # Проверяем формат пары (должна заканчиваться на USDT)
            if not pair.endswith('USDT'):
                await message.answer(
                    "⚠️ Название пары должно заканчиваться на USDT (например, BTCUSDT).\n"
                    "Пожалуйста, введите корректное название пары."
                )
                return

            # Получаем текущие пары
            monitoring_config = crypto_config.get('monitoring', {})
            pairs = monitoring_config.get('pairs', []) # Инициализируем пустым списком, если нет

            # Проверяем, не добавлена ли уже эта пара
            if pair in pairs:
                await message.answer(
                    f"⚠️ Пара {pair} уже добавлена в список отслеживаемых пар."
                )
                return

            # Добавляем новую пару
            pairs.append(pair)
            monitoring_config['pairs'] = pairs
            crypto_config['monitoring'] = monitoring_config

            # Сохраняем конфигурацию в файл
            save_crypto_config()

            logger.debug(f"Добавлена новая торговая пара {pair}, текущие пары: {pairs}")

            # Сбрасываем состояние пользователя
            del user_states[message.from_user.id]

            # Отправляем сообщение об успешном добавлении
            await message.answer(
                f"✅ Торговая пара {pair} успешно добавлена.\n\n"
                "Возвращаемся к настройкам торговых пар."
            )

            # Создаем временное сообщение для использования в callback
            temp_msg = await message.answer("⏳ Загрузка настроек торговых пар...")

            # Создаем callback-запрос для использования существующего обработчика
            # Возвращаемся в меню торговых пар
            callback = types.CallbackQuery(
                id="crypto_settings_pairs", # Используем callback_data для возврата в меню пар
                from_user=message.from_user,
                chat_instance=str(message.chat.id),
                message=temp_msg,
                data="crypto_settings_pairs"
            )

            # Устанавливаем бота для callback
            callback.bot = bot_instance

            # Вызываем обработчик настроек торговых пар
            await process_settings_pairs(callback)

        except Exception as e:
            log_exception(e, f"Ошибка при добавлении торговой пары для пользователя {message.from_user.id}")
            try:
                await message.answer(
                    f"❌ Произошла ошибка при добавлении торговой пары: {e}\n\n"
                    "Пожалуйста, попробуйте еще раз или вернитесь в настройки."
                )
            except Exception as e2:
                log_exception(e2, "Ошибка при отправке сообщения об ошибке")

    elif state == 'waiting_pair_to_remove':
        # Обработка ввода названия торговой пары для удаления
        logger.info(f"Получено название торговой пары для удаления от пользователя {message.from_user.id}: {message.text}")

        try:
            # Получаем название пары из сообщения
            pair_to_remove = message.text.strip().upper()

            # Получаем текущие пары
            monitoring_config = crypto_config.get('monitoring', {})
            pairs = monitoring_config.get('pairs', [])

            # Проверяем, существует ли такая пара в списке
            if pair_to_remove not in pairs:
                await message.answer(
                    f"⚠️ Пара {pair_to_remove} не найдена в списке отслеживаемых пар.\n"
                    "Пожалуйста, введите корректное название пары для удаления."
                )
                return

            # Удаляем пару
            pairs.remove(pair_to_remove)
            monitoring_config['pairs'] = pairs
            crypto_config['monitoring'] = monitoring_config

            # Сохраняем конфигурацию в файл
            save_crypto_config()

            logger.debug(f"Удалена торговая пара {pair_to_remove}, текущие пары: {pairs}")

            # Сбрасываем состояние пользователя
            del user_states[message.from_user.id]

            # Отправляем сообщение об успешном удалении
            await message.answer(
                f"✅ Торговая пара {pair_to_remove} успешно удалена.\n\n"
                "Возвращаемся к настройкам торговых пар."
            )

            # Создаем временное сообщение для использования в callback
            temp_msg = await message.answer("⏳ Загрузка настроек торговых пар...")

            # Создаем callback-запрос для использования существующего обработчика
            # Возвращаемся в меню торговых пар
            callback = types.CallbackQuery(
                id="crypto_settings_pairs", # Используем callback_data для возврата в меню пар
                from_user=message.from_user,
                chat_instance=str(message.chat.id),
                message=temp_msg,
                data="crypto_settings_pairs"
            )

            # Устанавливаем бота для callback
            callback.bot = bot_instance

            # Вызываем обработчик настроек торговых пар
            await process_settings_pairs(callback)

        except Exception as e:
            
            signals_config['channel_id'] = channel_id
            crypto_config['signals'] = signals_config
            save_crypto_config()

            logger.debug(f"ID канала для сигналов сохранен: {channel_id}")

            # Сбрасываем состояние пользователя
            del user_states[message.from_user.id]

            # Отправляем сообщение об успешном сохранении
            await message.answer(
                f"✅ ID канала для сигналов успешно сохранен: {channel_id}.\n\n"
                "Возвращаемся к настройкам сигналов."
            )

            # Создаем временное сообщение для использования в callback
            temp_msg = await message.answer("⏳ Загрузка настроек сигналов...")

            # Создаем callback-запрос для использования существующего обработчика
            # Возвращаемся в меню настроек сигналов
            callback = types.CallbackQuery(
                id="crypto_settings_signals", # Используем callback_data для возврата в меню сигналов
                from_user=message.from_user,
                chat_instance=str(message.chat.id),
                message=temp_msg,
                data="crypto_settings_signals"
            )

            # Устанавливаем бота для callback
            callback.bot = bot_instance

            # Вызываем обработчик настроек сигналов
            await process_settings_signals(callback)

        except Exception as e:
            log_exception(e, f"Ошибка при сохранении ID канала для сигналов пользователя {message.from_user.id}")
            try:
                await message.answer(
                    f"❌ Произошла ошибка при сохранении ID канала: {e}\n\n"
                    "Пожалуйста, попробуйте еще раз или вернитесь в настройки."
                )
            except Exception as e2:
                log_exception(e2, "Ошибка при отправке сообщения об ошибке")

    elif state == 'waiting_signal_cooldown':
        # Обработка ввода кулдауна сигналов
        logger.info(f"Получен кулдаун сигналов от пользователя {message.from_user.id}: {message.text}")

        try:
            cooldown_seconds = int(message.text.strip())

            if cooldown_seconds < 0:
                 await message.answer(
                    "⚠️ Кулдаун не может быть отрицательным числом. Введите корректное значение в секундах."
                )
                 return

            signals_config = crypto_config.get('signals', {})
            signals_config['notification_cooldown'] = cooldown_seconds
            crypto_config['signals'] = signals_config
            save_crypto_config()

            logger.debug(f"Кулдаун сигналов сохранен: {cooldown_seconds} сек")

            # Сбрасываем состояние пользователя
            del user_states[message.from_user.id]

            # Отправляем сообщение об успешном сохранении
            await message.answer(
                f"✅ Кулдаун уведомлений успешно сохранен: {cooldown_seconds} сек.\n\n"
                "Возвращаемся к настройкам сигналов."
            )

            # Создаем временное сообщение для использования в callback
            temp_msg = await message.answer("⏳ Загрузка настроек сигналов...")

            # Создаем callback-запрос для использования существующего обработчика
            # Возвращаемся в меню настроек сигналов
            callback = types.CallbackQuery(
                id="crypto_settings_signals", # Используем callback_data для возврата в меню сигналов
                from_user=message.from_user,
                chat_instance=str(message.chat.id),
                message=temp_msg,
                data="crypto_settings_signals"
            )

            # Устанавливаем бота для callback
            callback.bot = bot_instance

            # Вызываем обработчик настроек сигналов
            await process_settings_signals(callback)

        except ValueError:
            # Обработка ошибки, если введенное значение не является числом
            await message.answer(
                "⚠️ Некорректный формат. Введите кулдаун в секундах (целое число)."
            )
        except Exception as e:
            log_exception(e, f"Ошибка при сохранении кулдауна сигналов пользователя {message.from_user.id}")
            try:
                await message.answer(
                    f"❌ Произошла ошибка при сохранении кулдауна: {e}\n\n"
                    "Пожалуйста, попробуйте еще раз или вернитесь в настройки."
                )
            except Exception as e2:
                log_exception(e2, "Ошибка при отправке сообщения об ошибке")

    # Если состояние пользователя не соответствует ни одному из ожидаемых, игнорируем сообщение
    # (Это уже обрабатывается в начале функции, но можно добавить лог для отладки)
    # else:
    #     logger.debug(f"Получено сообщение от пользователя {message.from_user.id} в неизвестном состоянии: {state}")


# Функция для регистрации роутера в диспетчере
def register_crypto_handlers(dp: Dispatcher):
    """Регистрация обработчиков команд криптовалютного интерфейса"""
    logger.info("Регистрация обработчиков крипто анализа")
    dp.include_router(crypto_router)

# Возможно, потребуется отдельная функция для регистрации меню, как в main.py
# def register_crypto_menu_handlers(dp: Dispatcher):
#     logger.info("Регистрация обработчиков крипто меню")
#     # Здесь можно зарегистрировать обработчики для кнопок крипто меню, если они будут в другом роутере
#     pass

# Функция для обработки кнопки "🔍 Мониторинг" из main_menu.py (базовая реализация)
async def process_crypto_monitoring(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} выбрал 'Мониторинг'")
    # Здесь можно добавить логику для отображения текущего статуса мониторинга
    # или последних сигналов. Пока просто заглушка.
    await callback.message.edit_text(
        "🔍 Мониторинг (в разработке)\n\n"
        "Здесь будет отображаться статус мониторинга и последние сигналы.",
        reply_markup=get_crypto_settings_keyboard() # Можно вернуться в настройки или другое меню
    )
    await callback.answer()
