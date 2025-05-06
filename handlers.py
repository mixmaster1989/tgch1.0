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
        return {"channel_id": None, "admin_id": None}

config = load_config()
CHANNEL_ID = config.get("channel_id")
ADMIN_ID = config.get("admin_id")

# Временное хранилище для сгенерированных постов
generated_posts = {}

# Создание клавиатур
def get_main_keyboard(is_admin=False):
    """Создает основную клавиатуру с кнопками команд"""
    keyboard = [
        [KeyboardButton(text="🔄 Сгенерировать пост")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ]
    
    if is_admin:
        keyboard.insert(1, [KeyboardButton(text="📢 Опубликовать в канал")])
        keyboard.append([KeyboardButton(text="⚙️ Настройки")])
    
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
    # Запускаем блокирующую функцию в пуле потоков
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        thread_pool,
        lambda: generate_post(post_type, category)
    )

# Словарь для хранения задач генерации
generation_tasks = {}

# Обработчики команд
@router.message(Command("start"))
async def cmd_start(message: types.Message):
    is_admin = message.from_user.id == ADMIN_ID
    
    welcome_text = (
        "👋 Привет! Я бот для генерации и публикации контента в Telegram-канал.\n\n"
        "Я могу помочь вам создавать разнообразные посты для вашего канала "
        "с использованием искусственного интеллекта.\n\n"
        "Используйте кнопки ниже или команды для взаимодействия со мной."
    )
    
    await message.answer(welcome_text, reply_markup=get_main_keyboard(is_admin))

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    is_admin = message.from_user.id == ADMIN_ID
    
    help_text = """
🤖 *TGE Bot* - помощник для раскрутки Telegram-канала

Доступные команды:
/start - Начать работу с ботом
/generate - Сгенерировать пост для канала
/help - Показать это сообщение

"""
    
    if is_admin:
        help_text += """
Команды администратора:
/publish - Сгенерировать и опубликовать пост в канал
/publish_type - Опубликовать пост определенного типа и категории
/settings - Настройки бота

"""
    
    help_text += """
Вы также можете использовать кнопки для удобного взаимодействия с ботом.
"""
    
    await message.answer(help_text, parse_mode="Markdown", reply_markup=get_main_keyboard(is_admin))

@router.message(Command("generate"))
async def cmd_generate(message: types.Message):
    await message.answer("Выберите тип поста:", reply_markup=get_post_type_keyboard())

@router.message(Command("publish"))
async def cmd_publish(message: types.Message):
    # Проверяем, что команду отправил администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта команда доступна только администратору.")
        return
    
    await message.answer("Выберите тип поста для публикации:", reply_markup=get_post_type_keyboard())

@router.message(Command("settings"))
async def cmd_settings(message: types.Message):
    # Проверяем, что команду отправил администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта команда доступна только администратору.")
        return
    
    await message.answer("Настройки бота:", reply_markup=get_settings_keyboard())

@router.message(Command("generate_type"))
async def cmd_generate_type(message: types.Message):
    # Извлекаем аргументы команды
    args = message.text.split()[1:]
    
    if len(args) >= 2:
        post_type = args[0].lower()
        category = args[1].lower()
        
        valid_types = ["informational", "promotional", "educational", "entertaining"]
        valid_categories = ["tech", "business", "lifestyle", "entertainment"]
        
        if post_type not in valid_types:
            await message.answer(f"Неизвестный тип поста. Доступные типы: {', '.join(valid_types)}")
            return
            
        if category not in valid_categories:
            await message.answer(f"Неизвестная категория. Доступные категории: {', '.join(valid_categories)}")
            return
        
        # Отправляем сообщение о начале генерации
        status_message = await message.answer("⏳ Генерация поста начата... Это может занять некоторое время.")
        
        # Создаем уникальный ID для задачи
        task_id = str(uuid.uuid4())
        
        # Запускаем асинхронную задачу генерации
        task = asyncio.create_task(generate_post_async(post_type, category))
        generation_tasks[task_id] = {
            "task": task,
            "user_id": message.from_user.id,
            "chat_id": message.chat.id,
            "message_id": status_message.message_id,
            "is_publish": False,
            "post_type": post_type,
            "category": category
        }
        
        # Обновляем сообщение с кнопкой проверки статуса
        await status_message.edit_text(
            "⏳ Генерация поста начата...\n\n"
            "Это может занять некоторое время. Вы можете проверить статус генерации "
            "или дождаться уведомления о завершении.",
            reply_markup=get_check_status_keyboard(task_id)
        )
        
        # Запускаем обработчик завершения задачи
        asyncio.create_task(handle_generation_completion(task_id))
    else:
        await message.answer("Использование: /generate_type [тип] [категория]\n\n"
                           "Типы: informational, promotional, educational, entertaining\n"
                           "Категории: tech, business, lifestyle, entertainment")

@router.message(Command("publish_type"))
async def cmd_publish_type(message: types.Message):
    # Проверяем, что команду отправил администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта команда доступна только администратору.")
        return
        
    # Извлекаем аргументы команды
    args = message.text.split()[1:]
    
    if len(args) >= 2:
        post_type = args[0].lower()
        category = args[1].lower()
        
        valid_types = ["informational", "promotional", "educational", "entertaining"]
        valid_categories = ["tech", "business", "lifestyle", "entertainment"]
        
        if post_type not in valid_types:
            await message.answer(f"Неизвестный тип поста. Доступные типы: {', '.join(valid_types)}")
            return
            
        if category not in valid_categories:
            await message.answer(f"Неизвестная категория. Доступные категории: {', '.join(valid_categories)}")
            return
        
        # Отправляем сообщение о начале генерации
        status_message = await message.answer("⏳ Генерация поста начата... Это может занять некоторое время.")
        
        # Создаем уникальный ID для задачи
        task_id = str(uuid.uuid4())
        
        # Запускаем асинхронную задачу генерации
        task = asyncio.create_task(generate_post_async(post_type, category))
        generation_tasks[task_id] = {
            "task": task,
            "user_id": message.from_user.id,
            "chat_id": message.chat.id,
            "message_id": status_message.message_id,
            "is_publish": True,
            "post_type": post_type,
            "category": category
        }
        
        # Обновляем сообщение с кнопкой проверки статуса
        await status_message.edit_text(
            "⏳ Генерация поста начата...\n\n"
            "Это может занять некоторое время. Вы можете проверить статус генерации "
            "или дождаться уведомления о завершении.",
            reply_markup=get_check_status_keyboard(task_id)
        )
        
        # Запускаем обработчик завершения задачи
        asyncio.create_task(handle_generation_completion(task_id))
    else:
        await message.answer("Использование: /publish_type [тип] [категория]\n\n"
                           "Типы: informational, promotional, educational, entertaining\n"
                           "Категории: tech, business, lifestyle, entertainment")

# Обработчик завершения задачи генерации
async def handle_generation_completion(task_id):
    """
    Обрабатывает завершение задачи генерации
    
    Args:
        task_id (str): ID задачи
    """
    if task_id not in generation_tasks:
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
        
        # Отправляем уведомление о завершении
        bot = task_info["task"]._loop._running_task.get_name().split('_')[0]
        
        if is_publish:
            # Если это запрос на публикацию, показываем предварительный просмотр
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"✅ Генерация завершена!\n\nПредварительный просмотр поста:\n\n{post}",
                reply_markup=get_publish_confirmation_keyboard(task_id)
            )
        else:
            # Иначе просто показываем сгенерированный пост
            type_category = f"({post_type}, {category})" if post_type and category else ""
            await bot.edit_message_text(
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
            bot = task_info["task"]._loop._running_task.get_name().split('_')[0]
            
            # Отправляем уведомление об ошибке
            await bot.edit_message_text(
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

# Обработчики текстовых сообщений
@router.message(F.text == "🔄 Сгенерировать пост")
async def text_generate(message: types.Message):
    await cmd_generate(message)

@router.message(F.text == "📢 Опубликовать в канал")
async def text_publish(message: types.Message):
    await cmd_publish(message)

@router.message(F.text == "ℹ️ Помощь")
async def text_help(message: types.Message):
    await cmd_help(message)

@router.message(F.text == "⚙️ Настройки")
async def text_settings(message: types.Message):
    await cmd_settings(message)

# Обработчики callback-запросов
@router.callback_query(F.data.startswith("type_"))
async def process_post_type(callback: types.CallbackQuery):
    post_type = callback.data.split("_")[1]
    
    # Проверяем, является ли это запросом на публикацию
    is_publish = "публикации" in callback.message.text
    
    # Если выбран случайный тип, начинаем асинхронную генерацию
    if post_type == "random":
        # Обновляем сообщение
        await callback.message.edit_text("⏳ Генерация поста начата... Это может занять некоторое время.")
        
        # Создаем уникальный ID для задачи
        task_id = str(uuid.uuid4())
        
        # Запускаем асинхронную задачу генерации
        task = asyncio.create_task(generate_post_async())
        generation_tasks[task_id] = {
            "task": task,
            "user_id": callback.from_user.id,
            "chat_id": callback.message.chat.id,
            "message_id": callback.message.message_id,
            "is_publish": is_publish,
            "post_type": None,
            "category": None
        }
        
        # Обновляем сообщение с кнопкой проверки статуса
        await callback.message.edit_text(
            "⏳ Генерация поста начата...\n\n"
            "Это может занять некоторое время. Вы можете проверить статус генерации "
            "или дождаться уведомления о завершении.",
            reply_markup=get_check_status_keyboard(task_id)
        )
        
        # Запускаем обработчик завершения задачи
        asyncio.create_task(handle_generation_completion(task_id))
        
        await callback.answer()
        return
    
    # Иначе предлагаем выбрать категорию
    await callback.message.edit_text(
        f"Выбран тип: {post_type}\nТеперь выберите категорию:",
        reply_markup=get_category_keyboard(post_type)
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("category_"))
async def process_category(callback: types.CallbackQuery):
    # Формат: category_[post_type]_[category]
    parts = callback.data.split("_")
    post_type = parts[1]
    category = parts[2]
    
    # Проверяем, является ли это запросом на публикацию
    is_publish = "публикации" in callback.message.text
    
    # Обновляем сообщение
    await callback.message.edit_text("⏳ Генерация поста начата... Это может занять некоторое время.")
    
    # Создаем уникальный ID для задачи
    task_id = str(uuid.uuid4())
    
    # Определяем параметры генерации
    gen_post_type = None if post_type == "random" else post_type
    gen_category = None if category == "random" else category
    
    # Запускаем асинхронную задачу генерации
    task = asyncio.create_task(generate_post_async(gen_post_type, gen_category))
    generation_tasks[task_id] = {
        "task": task,
        "user_id": callback.from_user.id,
        "chat_id": callback.message.chat.id,
        "message_id": callback.message.message_id,
        "is_publish": is_publish,
        "post_type": gen_post_type,
        "category": gen_category
    }
    
    # Обновляем сообщение с кнопкой проверки статуса
    await callback.message.edit_text(
        "⏳ Генерация поста начата...\n\n"
        "Это может занять некоторое время. Вы можете проверить статус генерации "
        "или дождаться уведомления о завершении.",
        reply_markup=get_check_status_keyboard(task_id)
    )
    
    # Запускаем обработчик завершения задачи
    asyncio.create_task(handle_generation_completion(task_id))
    
    await callback.answer()

@router.callback_query(F.data.startswith("check_status_"))
async def process_check_status(callback: types.CallbackQuery):
    # Получаем ID задачи
    task_id = callback.data.replace("check_status_", "")
    
    if task_id in generation_tasks:
        # Задача еще выполняется
        await callback.answer("Генерация поста еще не завершена. Пожалуйста, подождите.")
    else:
        # Задача завершена или не найдена
        if task_id in generated_posts:
            # Задача завершена успешно
            post = generated_posts[task_id]
            
            # Проверяем, является ли это запросом на публикацию
            is_publish = "публикации" in callback.message.text
            
            if is_publish and callback.from_user.id == ADMIN_ID:
                # Показываем предварительный просмотр и запрашиваем подтверждение
                await callback.message.edit_text(
                    f"✅ Генерация завершена!\n\nПредварительный просмотр поста:\n\n{post}",
                    reply_markup=get_publish_confirmation_keyboard(task_id)
                )
            else:
                # Просто показываем сгенерированный пост
                await callback.message.edit_text(f"✅ Генерация завершена!\n\n{post}")
        else:
            # Задача не найдена
            await callback.answer("Задача не найдена или произошла ошибка.")
    
    await callback.answer()

@router.callback_query(F.data == "cancel_generation")
async def process_cancel_generation(callback: types.CallbackQuery):
    # Находим задачу по сообщению
    task_id = None
    for tid, task_info in list(generation_tasks.items()):
        if (task_info["chat_id"] == callback.message.chat.id and 
            task_info["message_id"] == callback.message.message_id):
            task_id = tid
            break
    
    if task_id:
        # Отменяем задачу
        task_info = generation_tasks[task_id]
        task_info["task"].cancel()
        
        # Удаляем задачу из словаря
        del generation_tasks[task_id]
        
        # Обновляем сообщение
        await callback.message.edit_text("❌ Генерация поста отменена.")
    else:
        await callback.answer("Задача не найдена или уже завершена.")
    
    await callback.answer()

@router.callback_query(F.data.startswith("publish_confirm_"))
async def process_publish_confirmation(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Эта функция доступна только администратору.")
        return
    
    # Получаем ID поста из callback_data
    post_id = callback.data.replace("publish_confirm_", "")
    
    # Получаем текст поста из временного хранилища
    post_text = generated_posts.get(post_id)
    
    if not post_text:
        # Если пост не найден, используем текст из сообщения
        post_text = callback.message.text
        if "Предварительный просмотр поста:" in post_text:
            post_text = post_text.split("Предварительный просмотр поста:", 1)[1].strip()
        elif "Генерация завершена!" in post_text:
            post_text = post_text.split("Генерация завершена!", 1)[1].strip()
    
    # Публикуем пост в канал
    if CHANNEL_ID:
        try:
            # Отправляем сообщение в канал
            await callback.bot.send_message(chat_id=CHANNEL_ID, text=post_text)
            await callback.message.edit_text("✅ Пост успешно опубликован в канале!")
        except Exception as e:
            await callback.message.edit_text(f"❌ Ошибка при публикации в канал: {e}")
    else:
        await callback.message.edit_text("❌ ID канала не настроен в конфигурации.")
    
    await callback.answer()

@router.callback_query(F.data == "publish_regenerate")
async def process_publish_regenerate(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Эта функция доступна только администратору.")
        return
    
    await callback.message.edit_text("Выберите тип поста для публикации:", reply_markup=get_post_type_keyboard())
    
    await callback.answer()

@router.callback_query(F.data == "publish_cancel")
async def process_publish_cancel(callback: types.CallbackQuery):
    await callback.message.edit_text("❌ Публикация отменена.")
    
    await callback.answer()

@router.callback_query(F.data.startswith("settings_"))
async def process_settings(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Эта функция доступна только администратору.")
        return
    
    action = callback.data.split("_")[1]
    
    if action == "stats":
        await callback.message.edit_text(
            "📊 Статистика:\n\n"
            "Функция статистики находится в разработке.\n\n"
            "Скоро здесь появится информация о количестве сгенерированных и опубликованных постов, "
            "активности подписчиков и другие полезные метрики.",
            reply_markup=get_settings_keyboard()
        )
    elif action == "schedule":
        schedule_text = "⏱ Расписание постов:\n\n"
        
        if 'post_schedule' in config:
            schedule_times = config['post_schedule']
            for i, time in enumerate(schedule_times, 1):
                schedule_text += f"{i}. {time}\n"
        else:
            schedule_text += "Расписание не настроено.\n"
        
        schedule_text += "\nФункция автоматической публикации по расписанию находится в разработке."
        
        await callback.message.edit_text(schedule_text, reply_markup=get_settings_keyboard())
    elif action == "back":
        await callback.message.edit_text("Настройки закрыты.")
        await callback.message.delete()
    
    await callback.answer()

def register_handlers(dp: Dispatcher):
    # Регистрируем роутер в диспетчере
    dp.include_router(router)