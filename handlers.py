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

# Глобальная переменная для хранения экземпляра бота
bot_instance = None

def set_bot(bot):
    global bot_instance
    bot_instance = bot

# Создание клавиатур
def get_main_keyboard(is_admin=False):
    """Создает основную клавиатуру с кнопками команд"""
    keyboard = [
        [KeyboardButton(text="🔄 Сгенерировать пост")],
        [KeyboardButton(text="ℹ️ Помощь")]
    ]
    
    if is_admin:
        keyboard.insert(1, [KeyboardButton(text="📢 Опубликовать в канал")])
        keyboard.append([KeyboardButton(text="🚀 Продвижение")])
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
/promotion - Меню продвижения канала

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

@router.message(Command("promotion"))
async def cmd_promotion_handler(message: types.Message):
    # Проверяем, что команду отправил администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта команда доступна только администратору.")
        return
    
    # Вызываем команду /promotion
    from handlers_promotion import cmd_promotion
    await cmd_promotion(message)

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

@router.message(F.text == "🚀 Продвижение")
async def text_promotion(message: types.Message):
    # Проверяем, что команду отправил администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта функция доступна только администратору.")
        return
    
    # Вызываем команду /promotion
    from handlers_promotion import cmd_promotion
    await cmd_promotion(message)

def register_handlers(dp: Dispatcher):
    # Регистрируем роутер в диспетчере
    dp.include_router(router)
