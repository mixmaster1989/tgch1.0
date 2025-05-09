from aiogram import Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.exceptions import TelegramBadRequest
from core.generator import generate_post, generate_post_with_config
import yaml
import os
import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем роутер для обработчиков команд
router = Router()

# Пул потоков для выполнения блокирующих операций
thread_pool = ThreadPoolExecutor(max_workers=2)

# Загрузка конфигурации
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации: {e}")
        # Возвращаем минимальную конфигурацию без ограничений
        return {"channel_id": None, "admin_id": None, "allowed_users": [], "admins": []}

# Сохранение конфигурации
def save_config(config):
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
    try:
        with open(config_path, 'w', encoding='utf-8') as file:
            yaml.dump(config, file, default_flow_style=False)
        logger.info("Конфигурация успешно сохранена")
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении конфигурации: {e}")
        return False

# Загружаем конфигурацию
config = load_config()
# CHANNEL_ID = config.get("channel_id")  # Отключаем привязку к каналу
# ADMIN_ID = config.get("admin_id")      # Отключаем админские ограничения
# ALLOWED_USERS = config.get("allowed_users", [])  # Убираем список разрешенных пользователей
# ADMINS = config.get("admins", [])       # Убираем список админов

# Вместо этого разрешаем все функции для всех пользователей
CHANNEL_ID = None
ADMIN_ID = None
ALLOWED_USERS = []
ADMINS = []

# Временное хранилище для сгенерированных постов
generated_posts = {}

# Глобальная переменная для хранения экземпляра бота
bot_instance = None

# Словарь для хранения состояний пользователей
user_states = {}

def set_bot(bot):
    global bot_instance
    bot_instance = bot

# Создание клавиатур
def get_main_keyboard(is_admin=False, is_allowed=False, is_additional_admin=False):
    """Создает основную клавиатуру с кнопками команд"""
    keyboard = [
        [KeyboardButton(text="🔄 Сгенерировать пост")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ]
    
    if is_admin:
        keyboard.insert(1, [KeyboardButton(text="📢 Опубликовать в канал")])
        keyboard.append([KeyboardButton(text="🚀 Продвижение")])
        keyboard.append([KeyboardButton(text="📈 Крипто анализ")])
        keyboard.append([KeyboardButton(text="⚙️ Настройки")])
    elif is_additional_admin:
        keyboard.insert(1, [KeyboardButton(text="📢 Опубликовать в канал")])
        keyboard.append([KeyboardButton(text="🚀 Продвижение")])
        keyboard.append([KeyboardButton(text="📈 Крипто анализ")])
        keyboard.append([KeyboardButton(text="🔍 Smart Money")])  # Добавлена кнопка Smart Money для дополнительных администраторов
        keyboard.append([KeyboardButton(text="⚙️ Настройки")])
    elif is_allowed:
        keyboard.append([KeyboardButton(text="📈 Крипто анализ")])
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def get_post_type_keyboard():
    """Создает клавиатуру для выбора типа поста"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Информационный", callback_data="type_informational"),
            InlineKeyboardButton(text="🚀 Рекламный", callback_data="type_promotional")
        ],
        [
            InlineKeyboardButton(text="📚 Обучающий", callback_data="type_educational"),
            InlineKeyboardButton(text="🎭 Развлекательный", callback_data="type_entertaining")
        ],
        [
            InlineKeyboardButton(text="🔄 Случайный тип", callback_data="type_random")
        ]
    ])
    return keyboard

def get_category_keyboard(post_type):
    """Создает клавиатуру для выбора категории поста"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💻 Технологии", callback_data=f"category_{post_type}_tech"),
            InlineKeyboardButton(text="💼 Бизнес", callback_data=f"category_{post_type}_business")
        ],
        [
            InlineKeyboardButton(text="🧘 Лайфстайл", callback_data=f"category_{post_type}_lifestyle"),
            InlineKeyboardButton(text="🎮 Развлечения", callback_data=f"category_{post_type}_entertainment")
        ],
        [
            InlineKeyboardButton(text="🔄 Случайная категория", callback_data=f"category_{post_type}_random")
        ]
    ])
    return keyboard

def get_settings_keyboard():
    """Создает клавиатуру настроек для администратора"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="settings_stats")
        ],
        [
            InlineKeyboardButton(text="⏱ Расписание постов", callback_data="settings_schedule")
        ],
        [
            InlineKeyboardButton(text="👥 Управление администраторами", callback_data="settings_admins")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="settings_back")
        ]
    ])
    return keyboard

def get_publish_confirmation_keyboard(post_id):
    """Создает клавиатуру для подтверждения публикации"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опубликовать", callback_data=f"publish_confirm_{post_id}"),
            InlineKeyboardButton(text="🔄 Сгенерировать заново", callback_data="publish_regenerate")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="publish_cancel")
        ]
    ])
    return keyboard

def get_check_status_keyboard(task_id):
    """Создает клавиатуру для проверки статуса генерации"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Проверить статус", callback_data=f"check_status_{task_id}")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_generation")
        ]
    ])
    return keyboard

# Асинхронная генерация контента
async def generate_post_async(post_type=None, category=None):
    """
    Асинхронно генерирует пост в отдельном потоке
    
    Args:
        post_type (str, optional): Тип поста
        category (str, optional): Категория поста
        
    Returns:
        str: Сгенерированный пост
    """
    logger.info(f"Начало генерации поста: тип={post_type}, категория={category}")
    # Запускаем блокирующую функцию в пуле потоков
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            thread_pool,
            lambda: generate_post(post_type, category)
        )
        logger.info(f"Пост успешно сгенерирован: тип={post_type}, категория={category}")
        return result
    except Exception as e:
        logger.error(f"Ошибка при генерации поста: {e}")
        raise

# Словарь для хранения задач генерации
generation_tasks = {}

# Обработчик завершения задачи генерации
async def handle_generation_completion(task_id):
    """
    Обрабатывает завершение задачи генерации
    
    Args:
        task_id (str): ID задачи
    """
    if task_id not in generation_tasks:
        logger.warning(f"Задача {task_id} не найдена в списке задач")
        return
    
    task_info = generation_tasks[task_id]
    task = task_info["task"]
    
    try:
        # Ждем завершения задачи
        post = await task
        
        # Сохраняем результат
        generated_posts[task_id] = post
        
        # Получаем информацию о задаче
        chat_id = task_info["chat_id"]
        message_id = task_info["message_id"]
        is_publish = task_info["is_publish"]
        post_type = task_info.get("post_type", "")
        category = task_info.get("category", "")
        
        logger.info(f"Задача {task_id} завершена успешно: is_publish={is_publish}, post_type={post_type}, category={category}")
        
        # Используем глобальный экземпляр бота
        if bot_instance:
            if is_publish:
                # Если это запрос на публикацию, показываем предварительный просмотр
                await bot_instance.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"✅ Генерация завершена!\n\nПредварительный просмотр поста:\n\n{post}",
                    reply_markup=get_publish_confirmation_keyboard(task_id)
                )
            else:
                # Иначе просто показываем сгенерированный пост
                type_category = f"({post_type}, {category})" if post_type and category else ""
                await bot_instance.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"✅ Генерация завершена! {type_category}\n\n{post}"
                )
    except asyncio.CancelledError:
        # Задача была отменена
        logger.info(f"Задача {task_id} была отменена")
    except Exception as e:
        # Произошла ошибка при генерации
        logger.error(f"Ошибка при генерации поста: {e}")
        
        try:
            # Получаем информацию о задаче
            chat_id = task_info["chat_id"]
            message_id = task_info["message_id"]
            
            # Используем глобальный экземпляр бота
            if bot_instance:
                # Отправляем уведомление об ошибке
                await bot_instance.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=f"❌ Произошла ошибка при генерации поста: {e}"
                )
        except Exception as e2:
            logger.error(f"Ошибка при отправке уведомления об ошибке: {e2}")
    finally:
        # Удаляем задачу из словаря
        if task_id in generation_tasks:
            del generation_tasks[task_id]
            logger.info(f"Задача {task_id} удалена из списка задач")

# Обработчики команд
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил команду /start")
    
    # Проверяем, является ли пользователь главным администратором
    is_admin = message.from_user.id == ADMIN_ID
    
    # Проверяем, является ли пользователь дополнительным администратором
    is_additional_admin = message.from_user.id in ADMINS
    
    # Проверяем, является ли пользователь разрешенным
    is_allowed = message.from_user.id in ALLOWED_USERS
    
    # Отправляем приветственное сообщение
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я бот для генерации и публикации постов. "
        "Используйте кнопки ниже для управления.",
        reply_markup=get_main_keyboard(is_admin, is_allowed, is_additional_admin)
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил команду /help")
    
    # Отправляем справочное сообщение
    await message.answer(
        "📚 *Справка по командам*\n\n"
        "/start - Начать работу с ботом\n"
        "/generate - Сгенерировать новый пост\n"
        "/help - Показать эту справку\n\n"
        "Для администраторов:\n"
        "/publish - Опубликовать пост в канал\n"
        "/settings - Настройки бота\n"
        "/promotion - Инструменты продвижения\n",
        parse_mode="Markdown"
    )

@router.message(Command("generate"))
async def cmd_generate(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил команду /generate")
    
    # Отправляем клавиатуру для выбора типа поста
    await message.answer("Выберите тип поста:", reply_markup=get_post_type_keyboard())

@router.message(Command("publish"))
async def cmd_publish(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил команду /publish")
    
    # Проверяем, что команду отправил администратор или дополнительный администратор
    if message.from_user.id != ADMIN_ID and message.from_user.id not in ADMINS:
        logger.warning(f"Пользователь {message.from_user.id} попытался использовать команду /publish без прав администратора")
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    await message.answer("Выберите тип поста для публикации:", reply_markup=get_post_type_keyboard())

@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил команду /settings")
    # Проверяем, что команду отправил администратор или дополнительный администратор
    if message.from_user.id != ADMIN_ID and message.from_user.id not in ADMINS:
        logger.warning(f"Пользователь {message.from_user.id} попытался использовать команду /settings без прав администратора")
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    await message.answer("Настройки бота:", reply_markup=get_settings_keyboard())

@router.message(Command("promotion"))
async def cmd_promotion_handler(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} запустил команду /promotion")
    # Проверяем, что команду отправил администратор или дополнительный администратор
    if message.from_user.id != ADMIN_ID and message.from_user.id not in ADMINS:
        logger.warning(f"Пользователь {message.from_user.id} попытался использовать команду /promotion без прав администратора")
        await message.answer("Эта команда доступна только администраторам.")
        return
    
    # Вызываем команду /promotion
    from handlers_promotion import cmd_promotion
    await cmd_promotion(message)

# Обработчики текстовых сообщений
@router.message(F.text == "🔄 Сгенерировать пост")
async def text_generate(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} нажал кнопку 'Сгенерировать пост'")
    await cmd_generate(message)

@router.message(F.text == "📢 Опубликовать в канал")
async def text_publish(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} нажал кнопку 'Опубликовать в канал'")
    await cmd_publish(message)

@router.message(F.text == "ℹ️ Помощь")
async def text_help(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} нажал кнопку 'Помощь'")
    await cmd_help(message)

@router.message(F.text == "⚙️ Настройки")
async def text_settings(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} нажал кнопку 'Настройки'")
    await cmd_settings(message)

@router.message(F.contact)
async def handle_contact(message: types.Message):
    """
    Обработчик для полученного контакта
    """
    global ADMINS
    logger.info(f"Пользователь {message.from_user.id} отправил контакт")
    
    # Проверяем, что пользователь находится в состоянии ожидания контакта
    if message.from_user.id in user_states and user_states[message.from_user.id] == "waiting_for_admin_contact":
        # Получаем ID пользователя из контакта
        contact = message.contact
        user_id = contact.user_id
        
        # Загружаем текущую конфигурацию
        config = load_config()
        admins = config.get("admins", [])
        
        # Проверяем, не является ли пользователь уже администратором
        if user_id == ADMIN_ID:
            await message.answer("Этот пользователь уже является главным администратором.")
            return
        
        if user_id in admins:
            await message.answer("Этот пользователь уже является администратором.")
            return
        
        # Добавляем пользователя в список администраторов
        admins.append(user_id)
        config["admins"] = admins
        
        # Сохраняем обновленную конфигурацию
        if save_config(config):
            await message.answer(f"Пользователь с ID {user_id} успешно добавлен в список администраторов.")
            
            # Обновляем глобальную переменную
            ADMINS = admins
        else:
            await message.answer("Произошла ошибка при сохранении конфигурации.")
        
        # Очищаем состояние пользователя
        del user_states[message.from_user.id]
        
        # Возвращаем основную клавиатуру
        is_admin = message.from_user.id == ADMIN_ID
        is_additional_admin = message.from_user.id in ADMINS
        is_allowed = message.from_user.id in ALLOWED_USERS
        
        await message.answer(
            "Возвращаемся в главное меню.",
            reply_markup=get_main_keyboard(is_admin, is_allowed, is_additional_admin)
        )
    else:
        await message.answer("Я не запрашивал контакт. Пожалуйста, используйте команды бота.")

@router.message(F.forward_from)
async def handle_forwarded_message(message: types.Message):
    """
    Обработчик для пересланного сообщения
    """
    global ADMINS
    logger.info(f"Пользователь {message.from_user.id} переслал сообщение")
    
    # Проверяем, что пользователь находится в состоянии ожидания контакта
    if message.from_user.id in user_states and user_states[message.from_user.id] == "waiting_for_admin_contact":
        # Получаем ID пользователя из пересланного сообщения
        forwarded_from = message.forward_from
        if forwarded_from:
            user_id = forwarded_from.id
            
            # Загружаем текущую конфигурацию
            config = load_config()
            admins = config.get("admins", [])
            
            # Проверяем, не является ли пользователь уже администратором
            if user_id == ADMIN_ID:
                await message.answer("Этот пользователь уже является главным администратором.")
                return
            
            if user_id in admins:
                await message.answer("Этот пользователь уже является администратором.")
                return
            
            # Добавляем пользователя в список администраторов
            admins.append(user_id)
            config["admins"] = admins
            
            # Сохраняем обновленную конфигурацию
            if save_config(config):
                await message.answer(f"Пользователь с ID {user_id} успешно добавлен в список администраторов.")
                
                # Обновляем глобальную переменную
                ADMINS = admins
            else:
                await message.answer("Произошла ошибка при сохранении конфигурации.")
            
            # Очищаем состояние пользователя
            del user_states[message.from_user.id]
            
            # Возвращаем основную клавиатуру
            is_admin = message.from_user.id == ADMIN_ID
            is_additional_admin = message.from_user.id in ADMINS
            is_allowed = message.from_user.id in ALLOWED_USERS
            
            await message.answer(
                "Возвращаемся в главное меню.",
                reply_markup=get_main_keyboard(is_admin, is_allowed, is_additional_admin)
            )
        else:
            await message.answer("Не удалось получить информацию о пользователе из пересланного сообщения. Попробуйте другой способ.")
    else:
        # Обычная обработка пересланных сообщений
        pass

@router.message(lambda message: message.from_user.id in user_states and user_states[message.from_user.id] == "waiting_for_admin_contact")
async def handle_admin_id_input(message: types.Message):
    """
    Обработчик для ввода ID администратора вручную
    """
    global ADMINS
    logger.info(f"Пользователь {message.from_user.id} ввел ID администратора")
    
    # Проверяем, является ли введенный текст числом
    if message.text == "❌ Отмена":
        # Очищаем состояние пользователя
        del user_states[message.from_user.id]
        
        # Возвращаем основную клавиатуру
        is_admin = message.from_user.id == ADMIN_ID
        is_additional_admin = message.from_user.id in ADMINS
        is_allowed = message.from_user.id in ALLOWED_USERS
        
        await message.answer(
            "Операция отменена. Возвращаемся в главное меню.",
            reply_markup=get_main_keyboard(is_admin, is_allowed, is_additional_admin)
        )
        return
    
    try:
        user_id = int(message.text)
        
        # Загружаем текущую конфигурацию
        config = load_config()
        admins = config.get("admins", [])
        
        # Проверяем, не является ли пользователь уже администратором
        if user_id == ADMIN_ID:
            await message.answer("Этот пользователь уже является главным администратором.")
            return
        
        if user_id in admins:
            await message.answer("Этот пользователь уже является администратором.")
            return
        
        # Добавляем пользователя в список администраторов
        admins.append(user_id)
        config["admins"] = admins
        
        # Сохраняем обновленную конфигурацию
        if save_config(config):
            await message.answer(f"Пользователь с ID {user_id} успешно добавлен в список администраторов.")
            
            # Обновляем глобальную переменную
            ADMINS = admins
        else:
            await message.answer("Произошла ошибка при сохранении конфигурации.")
        
        # Очищаем состояние пользователя
        del user_states[message.from_user.id]
        
        # Возвращаем основную клавиатуру
        is_admin = message.from_user.id == ADMIN_ID
        is_additional_admin = message.from_user.id in ADMINS
        is_allowed = message.from_user.id in ALLOWED_USERS
        
        await message.answer(
            "Возвращаемся в главное меню.",
            reply_markup=get_main_keyboard(is_admin, is_allowed, is_additional_admin)
        )
    except ValueError:
        await message.answer("Пожалуйста, введите корректный ID пользователя (только цифры).")

@router.message(F.text == "🚀 Продвижение")
async def text_promotion(message: types.Message):
    logger.info(f"Пользователь {message.from_user.id} нажал кнопку 'Продвижение'")
    await cmd_promotion_handler(message)

@router.message(F.text == "📈 Крипто анализ")
async def text_crypto(message: types.Message):
    """
    Обработчик кнопки "Крипто анализ"
    """
    logger.info(f"Пользователь {message.from_user.id} нажал кнопку 'Крипто анализ'")
    
    # Проверяем, имеет ли пользователь доступ к криптомодулю
    if message.from_user.id == ADMIN_ID or message.from_user.id in ADMINS or message.from_user.id in ALLOWED_USERS:
        # Импортируем функцию из криптомодуля
        from crypto.handlers import cmd_crypto_mode
        
        # Вызываем обработчик команды
        await cmd_crypto_mode(message)
    else:
        await message.answer("У вас нет доступа к этой функции. Обратитесь к администратору бота.")

# Обработчики callback-запросов
@router.callback_query(F.data.startswith("type_"))
async def callback_post_type(callback: types.CallbackQuery):
    post_type = callback.data.split("_")[1]
    logger.info(f"Пользователь {callback.from_user.id} выбрал тип поста: {post_type}")
    
    # Проверяем, является ли это запросом на публикацию
    is_publish = False
    message_text = callback.message.text
    if "публикации" in message_text.lower():
        is_publish = True
    
    # Показываем клавиатуру для выбора категории
    await callback.message.edit_text(
        f"Выбран тип: {post_type}\n\nТеперь выберите категорию поста:",
        reply_markup=get_category_keyboard(post_type)
    )
    
    # Отвечаем на callback, чтобы убрать часы загрузки
    await callback.answer()

@router.callback_query(F.data.startswith("category_"))
async def callback_post_category(callback: types.CallbackQuery):
    # Разбираем данные из callback
    parts = callback.data.split("_")
    post_type = parts[1]
    category = parts[2]
    
    logger.info(f"Пользователь {callback.from_user.id} выбрал категорию поста: {category} для типа {post_type}")
    
    # Проверяем, является ли это запросом на публикацию
    is_publish = False
    message_text = callback.message.text
    if "публикации" in message_text.lower():
        is_publish = True
    
    # Отправляем сообщение о начале генерации
    await callback.message.edit_text(
        f"🔄 Генерация {'поста для публикации' if is_publish else 'поста'}...\n\n"
        f"Тип: {post_type}\n"
        f"Категория: {category}\n\n"
        "Это может занять некоторое время. Пожалуйста, подождите."
    )
    
    # Создаем задачу для генерации поста
    task_id = str(uuid.uuid4())
    task = asyncio.create_task(generate_post_async(post_type, category))
    
    # Сохраняем информацию о задаче
    generation_tasks[task_id] = {
        "task": task,
        "chat_id": callback.message.chat.id,
        "message_id": callback.message.message_id,
        "is_publish": is_publish,
        "post_type": post_type,
        "category": category
    }
    
    # Добавляем обработчик завершения задачи
    task.add_done_callback(
        lambda _: asyncio.create_task(handle_generation_completion(task_id))
    )
    
    # Отвечаем на callback, чтобы убрать часы загрузки
    await callback.answer()

@router.callback_query(F.data.startswith("publish_confirm_"))
async def callback_publish_confirm(callback: types.CallbackQuery):
    # Получаем ID поста из callback
    post_id = callback.data.split("_")[2]
    
    logger.info(f"Пользователь {callback.from_user.id} подтвердил публикацию поста {post_id}")
    
    # Проверяем, что пользователь имеет права администратора
    if callback.from_user.id != ADMIN_ID and callback.from_user.id not in ADMINS:
        await callback.answer("У вас нет прав для публикации постов")
        return
    
    # Проверяем, что пост существует
    if post_id not in generated_posts:
        await callback.answer("Ошибка: пост не найден")
        return
    
    # Получаем текст поста
    post_text = generated_posts[post_id]
    
    try:
        # Публикуем пост в канал
        if CHANNEL_ID:
            await bot_instance.send_message(
                chat_id=CHANNEL_ID,
                text=post_text
            )
            
            await callback.message.edit_text(
                "✅ Пост успешно опубликован в канал!"
            )
            
            logger.info(f"Пост {post_id} опубликован в канал {CHANNEL_ID}")
        else:
            await callback.message.edit_text(
                "❌ Ошибка: ID канала не настроен"
            )
            
            logger.error("Ошибка публикации: ID канала не настроен")
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Ошибка при публикации поста: {e}"
        )
        
        logger.error(f"Ошибка при публикации поста {post_id}: {e}")
    
    # Отвечаем на callback, чтобы убрать часы загрузки
    await callback.answer()

@router.callback_query(F.data == "publish_regenerate")
async def callback_publish_regenerate(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} запросил повторную генерацию поста")
    
    # Отправляем клавиатуру для выбора типа поста
    await callback.message.edit_text(
        "Выберите тип поста для публикации:",
        reply_markup=get_post_type_keyboard()
    )
    
    # Отвечаем на callback, чтобы убрать часы загрузки
    await callback.answer()

@router.callback_query(F.data == "publish_cancel")
async def callback_publish_cancel(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} отменил публикацию поста")
    
    await callback.message.edit_text(
        "❌ Публикация отменена"
    )
    
    # Отвечаем на callback, чтобы убрать часы загрузки
    await callback.answer()

@router.callback_query(F.data.startswith("check_status_"))
async def callback_check_status(callback: types.CallbackQuery):
    # Получаем ID задачи из callback
    task_id = callback.data.split("_")[2]
    
    logger.info(f"Пользователь {callback.from_user.id} проверяет статус задачи {task_id}")
    
    # Проверяем, существует ли задача
    if task_id in generation_tasks:
        await callback.answer("Генерация все еще выполняется. Пожалуйста, подождите.")
    else:
        # Если задачи нет в списке, возможно, она уже завершена
        if task_id in generated_posts:
            await callback.answer("Генерация завершена!")
        else:
            await callback.answer("Задача не найдена или была отменена")
    
@router.callback_query(F.data == "cancel_generation")
async def callback_cancel_generation(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} отменил генерацию")
    
    # Находим задачу для этого чата и сообщения
    chat_id = callback.message.chat.id
    message_id = callback.message.message_id
    
    task_id_to_cancel = None
    for task_id, task_info in generation_tasks.items():
        if task_info["chat_id"] == chat_id and task_info["message_id"] == message_id:
            task_id_to_cancel = task_id
            break
    
    if task_id_to_cancel:
        # Отменяем задачу
        task_info = generation_tasks[task_id_to_cancel]
        task = task_info["task"]
        task.cancel()
        
        # Удаляем задачу из словаря
        del generation_tasks[task_id_to_cancel]
        
        await callback.message.edit_text(
            "❌ Генерация отменена"
        )
        
        logger.info(f"Задача {task_id_to_cancel} отменена")
    else:
        await callback.answer("Задача не найдена или уже завершена")

@router.callback_query(F.data == "settings_stats")
async def callback_settings_stats(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} запросил статистику")
    
    # Здесь будет код для получения статистики
    # Пока просто заглушка
    await callback.message.edit_text(
        "📊 *Статистика*\n\n"
        "Функция статистики будет доступна в следующем обновлении.",
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data == "settings_schedule")
async def callback_settings_schedule(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} запросил настройки расписания")
    
    # Здесь будет код для настройки расписания
    # Пока просто заглушка
    await callback.message.edit_text(
        "⏱ *Расписание постов*\n\n"
        "Функция настройки расписания будет доступна в следующем обновлении.",
        reply_markup=get_settings_keyboard(),
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data == "settings_admins")
async def callback_settings_admins(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} запросил управление администраторами")
    
    # Проверяем, что пользователь имеет права главного администратора
    # Только главный администратор может управлять другими администраторами
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Только главный администратор может управлять списком администраторов")
        return
    
    # Загружаем текущий список администраторов
    config = load_config()
    admin_id = config.get("admin_id")
    admins = config.get("admins", [])
    
    # Формируем список администраторов для отображения
    admins_text = f"Главный администратор: {admin_id}\n\nДополнительные администраторы:\n"
    
    if admins:
        for i, admin in enumerate(admins, 1):
            admins_text += f"{i}. ID: {admin}\n"
    else:
        admins_text += "Список пуст\n"
    
    # Создаем клавиатуру для управления администраторами
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить администратора", callback_data="admin_add")
        ],
        [
            InlineKeyboardButton(text="❌ Удалить администратора", callback_data="admin_remove")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="settings_back")
        ]
    ])
    
    await callback.message.edit_text(
        f"👥 *Управление администраторами*\n\n{admins_text}\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    await callback.answer()

@router.callback_query(F.data == "admin_add")
async def callback_admin_add(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} запросил добавление администратора")
    
    # Создаем клавиатуру для запроса контакта
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📲 Поделиться контактом", request_contact=True)],
            [KeyboardButton(text="❌ Отмена")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    # Сохраняем состояние пользователя
    user_states[callback.from_user.id] = "waiting_for_admin_contact"
    
    await callback.message.answer(
        "Для добавления администратора, пожалуйста:\n\n"
        "1. Перешлите сообщение от пользователя, которого хотите добавить\n"
        "ИЛИ\n"
        "2. Введите ID пользователя вручную\n\n"
        "Вы также можете поделиться контактом, нажав на кнопку ниже.",
        reply_markup=keyboard
    )
    
    await callback.answer()

@router.callback_query(F.data == "admin_remove")
async def callback_admin_remove(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} запросил удаление администратора")
    
    # Загружаем текущий список администраторов
    config = load_config()
    admins = config.get("admins", [])
    
    if not admins:
        await callback.answer("Список администраторов пуст")
        return
    
    # Создаем клавиатуру для выбора администратора для удаления
    keyboard = InlineKeyboardBuilder()
    
    for i, admin in enumerate(admins):
        keyboard.button(text=f"❌ {admin}", callback_data=f"remove_admin_{admin}")
    
    keyboard.button(text="🔙 Назад", callback_data="settings_admins")
    keyboard.adjust(1)
    
    await callback.message.edit_text(
        "Выберите администратора для удаления:",
        reply_markup=keyboard.as_markup()
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("remove_admin_"))
async def callback_remove_admin(callback: types.CallbackQuery):
    global ADMINS
    admin_id = int(callback.data.split("_")[2])
    logger.info(f"Пользователь {callback.from_user.id} удаляет администратора {admin_id}")
    
    # Загружаем текущий список администраторов
    config = load_config()
    admins = config.get("admins", [])
    
    # Удаляем администратора из списка
    if admin_id in admins:
        admins.remove(admin_id)
        
        # Сохраняем обновленный список администраторов
        config["admins"] = admins
        save_config(config)
        
        # Обновляем глобальную переменную
        ADMINS = admins
        
        await callback.answer(f"Администратор {admin_id} удален")
    else:
        await callback.answer("Администратор не найден")
    
    # Возвращаемся к списку администраторов
    await callback_settings_admins(callback)

@router.callback_query(F.data == "settings_back")
async def callback_settings_back(callback: types.CallbackQuery):
    logger.info(f"Пользователь {callback.from_user.id} вернулся из настроек")
    
    await callback.message.edit_text(
        "Настройки бота:",
        reply_markup=get_settings_keyboard()
    )
    
    await callback.answer()

# Регистрация обработчиков
def register_handlers(dp: Dispatcher):
    """
    Регистрирует обработчики команд
    
    Args:
        dp: Диспетчер aiogram
    """
    dp.include_router(router)
    logger.info("Регистрация обработчиков команд")