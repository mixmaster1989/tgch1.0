from aiogram import Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from core.generator import generate_post, generate_post_with_config
import yaml
import os

# Создаем роутер для обработчиков команд
router = Router()

# Загрузка конфигурации
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        print(f"Ошибка при загрузке конфигурации: {e}")
        return {"channel_id": None, "admin_id": None}

config = load_config()
CHANNEL_ID = config.get("channel_id")
ADMIN_ID = config.get("admin_id")

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

def get_publish_confirmation_keyboard(post_type=None, category=None):
    """Создает клавиатуру для подтверждения публикации"""
    callback_data = f"publish_confirm_{post_type}_{category}" if post_type and category else "publish_confirm"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опубликовать", callback_data=callback_data),
            InlineKeyboardButton(text="🔄 Сгенерировать заново", callback_data="publish_regenerate")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="publish_cancel")
        ]
    ])
    return keyboard

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
            
        post = generate_post(post_type, category)
        await message.answer(f"Сгенерировано ({post_type}, {category}): \n{post}")
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
            
        post = generate_post(post_type, category)
        
        # Публикуем пост в канал
        if CHANNEL_ID:
            try:
                # Отправляем сообщение в канал
                await message.bot.send_message(chat_id=CHANNEL_ID, text=post)
                await message.answer(f"Пост типа {post_type} категории {category} опубликован в канале!")
            except Exception as e:
                await message.answer(f"Ошибка при публикации в канал: {e}")
        else:
            await message.answer("ID канала не настроен в конфигурации.")
    else:
        await message.answer("Использование: /publish_type [тип] [категория]\n\n"
                           "Типы: informational, promotional, educational, entertaining\n"
                           "Категории: tech, business, lifestyle, entertainment")

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
    
    # Если выбран случайный тип, генерируем пост сразу
    if post_type == "random":
        post = generate_post()
        await callback.message.edit_text(f"Сгенерировано: \n\n{post}")
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
    is_publish = callback.message.text.startswith("Выбран тип") and "публикации" in callback.message.text
    
    # Если выбрана случайная категория
    if category == "random":
        if post_type == "random":
            post = generate_post()
        else:
            post = generate_post(post_type)
    else:
        post = generate_post(post_type, category)
    
    if is_publish and callback.from_user.id == ADMIN_ID:
        # Показываем предварительный просмотр и запрашиваем подтверждение
        await callback.message.edit_text(
            f"Предварительный просмотр поста:\n\n{post}",
            reply_markup=get_publish_confirmation_keyboard(post_type, category)
        )
    else:
        # Просто показываем сгенерированный пост
        await callback.message.edit_text(f"Сгенерировано: \n\n{post}")
    
    await callback.answer()

@router.callback_query(F.data.startswith("publish_confirm"))
async def process_publish_confirmation(callback: types.CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Эта функция доступна только администратору.")
        return
    
    # Получаем текст поста из сообщения
    post_text = callback.message.text.replace("Предварительный просмотр поста:\n\n", "")
    
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