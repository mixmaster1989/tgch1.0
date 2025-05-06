from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging
import os
import yaml
import asyncio
from core.inviting import InvitingManager
from core.commenting import CommentingManager

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем роутер для обработчиков команд продвижения
promotion_router = Router()

# Загрузка конфигурации
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        return config
    except Exception as e:
        logger.error(f"Ошибка при загрузке конфигурации: {e}")
        return {}

# Получение ID администратора из конфигурации
config = load_config()
ADMIN_ID = config.get("admin_id")

# Словарь для хранения экземпляров менеджеров
managers = {
    "inviting": None,
    "commenting": None
}

# Словарь для хранения состояний авторизации
auth_states = {}

# Клавиатуры
def get_promotion_keyboard():
    """Создает клавиатуру для выбора метода продвижения"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Инвайтинг", callback_data="promotion_inviting"),
            InlineKeyboardButton(text="💬 Комментинг", callback_data="promotion_commenting")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки API", callback_data="promotion_settings")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="promotion_back")
        ]
    ])
    return keyboard

def get_inviting_keyboard():
    """Создает клавиатуру для управления инвайтингом"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Подключиться к API", callback_data="inviting_connect")
        ],
        [
            InlineKeyboardButton(text="👥 Пригласить пользователей", callback_data="inviting_invite")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки безопасности", callback_data="inviting_safety")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="inviting_back")
        ]
    ])
    return keyboard

def get_commenting_keyboard():
    """Создает клавиатуру для управления комментингом"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Подключиться к API", callback_data="commenting_connect")
        ],
        [
            InlineKeyboardButton(text="💬 Комментировать канал", callback_data="commenting_comment")
        ],
        [
            InlineKeyboardButton(text="✏️ Шаблоны комментариев", callback_data="commenting_templates")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки безопасности", callback_data="commenting_safety")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="commenting_back")
        ]
    ])
    return keyboard

def get_api_settings_keyboard():
    """Создает клавиатуру для настроек API"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔑 Установить API ID", callback_data="api_set_id")
        ],
        [
            InlineKeyboardButton(text="🔒 Установить API Hash", callback_data="api_set_hash")
        ],
        [
            InlineKeyboardButton(text="📱 Установить номер телефона", callback_data="api_set_phone")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="api_back")
        ]
    ])
    return keyboard

# Обработчики команд
@promotion_router.message(Command("promotion"))
async def cmd_promotion(message: types.Message):
    """Обработчик команды /promotion"""
    # Проверяем, что команду отправил администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта команда доступна только администратору.")
        return
    
    await message.answer(
        "🚀 Меню продвижения канала\n\n"
        "Выберите метод продвижения:",
        reply_markup=get_promotion_keyboard()
    )

# Обработчики callback-запросов для меню продвижения
@promotion_router.callback_query(F.data == "promotion_back")
async def process_promotion_back(callback: types.CallbackQuery):
    """Обработчик кнопки 'Назад' в меню продвижения"""
    await callback.message.delete()
    await callback.answer()

@promotion_router.callback_query(F.data == "promotion_inviting")
async def process_promotion_inviting(callback: types.CallbackQuery):
    """Обработчик кнопки 'Инвайтинг' в меню продвижения"""
    await callback.message.edit_text(
        "👥 Инвайтинг\n\n"
        "Инвайтинг позволяет приглашать пользователей из других групп в ваш канал.\n\n"
        "⚠️ Важно: Используйте эту функцию с осторожностью, чтобы избежать блокировки аккаунта.",
        reply_markup=get_inviting_keyboard()
    )
    await callback.answer()

@promotion_router.callback_query(F.data == "promotion_commenting")
async def process_promotion_commenting(callback: types.CallbackQuery):
    """Обработчик кнопки 'Комментинг' в меню продвижения"""
    await callback.message.edit_text(
        "💬 Комментинг\n\n"
        "Комментинг позволяет оставлять комментарии в других каналах с упоминанием вашего канала.\n\n"
        "⚠️ Важно: Используйте эту функцию с осторожностью, чтобы избежать блокировки аккаунта.",
        reply_markup=get_commenting_keyboard()
    )
    await callback.answer()

@promotion_router.callback_query(F.data == "promotion_settings")
async def process_promotion_settings(callback: types.CallbackQuery):
    """Обработчик кнопки 'Настройки API' в меню продвижения"""
    # Загрузка текущих настроек API
    config = load_config()
    api_id = config.get('telegram_api', {}).get('api_id')
    api_hash = config.get('telegram_api', {}).get('api_hash')
    phone = config.get('telegram_api', {}).get('phone')
    
    # Формирование сообщения с текущими настройками
    settings_text = "⚙️ Настройки Telegram API\n\n"
    settings_text += f"API ID: {'✅ Установлен' if api_id else '❌ Не установлен'}\n"
    settings_text += f"API Hash: {'✅ Установлен' if api_hash else '❌ Не установлен'}\n"
    settings_text += f"Телефон: {'✅ Установлен' if phone else '❌ Не установлен'}\n\n"
    settings_text += "Для использования функций инвайтинга и комментинга необходимо установить все параметры API."
    
    await callback.message.edit_text(
        settings_text,
        reply_markup=get_api_settings_keyboard()
    )
    await callback.answer()

# Обработчики для инвайтинга
@promotion_router.callback_query(F.data == "inviting_back")
async def process_inviting_back(callback: types.CallbackQuery):
    """Обработчик кнопки 'Назад' в меню инвайтинга"""
    await process_promotion_inviting(callback)

@promotion_router.callback_query(F.data == "inviting_connect")
async def process_inviting_connect(callback: types.CallbackQuery):
    """Обработчик кнопки 'Подключиться к API' в меню инвайтинга"""
    # Загрузка настроек API
    config = load_config()
    api_id = config.get('telegram_api', {}).get('api_id')
    api_hash = config.get('telegram_api', {}).get('api_hash')
    phone = config.get('telegram_api', {}).get('phone')
    
    # Проверка наличия всех необходимых параметров
    if not api_id or not api_hash or not phone:
        await callback.message.edit_text(
            "❌ Ошибка: Не все параметры API установлены.\n\n"
            "Пожалуйста, установите API ID, API Hash и номер телефона в настройках API.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⚙️ Настройки API", callback_data="promotion_settings")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="inviting_back")]
            ])
        )
        await callback.answer()
        return
    
    # Создание менеджера инвайтинга
    managers["inviting"] = InvitingManager(
        api_id=api_id,
        api_hash=api_hash,
        phone=phone
    )
    
    # Подключение к API
    await callback.message.edit_text(
        "⏳ Подключение к Telegram API...\n\n"
        "Пожалуйста, подождите."
    )
    
    # Запуск подключения в отдельной задаче
    asyncio.create_task(connect_inviting_manager(callback.message))
    
    await callback.answer()

async def connect_inviting_manager(message):
    """Подключение менеджера инвайтинга к Telegram API"""
    try:
        # Подключение к API
        success = await managers["inviting"].connect()
        
        if success:
            # Если подключение успешно
            await message.edit_text(
                "✅ Успешное подключение к Telegram API!\n\n"
                "Теперь вы можете использовать функции инвайтинга.",
                reply_markup=get_inviting_keyboard()
            )
        else:
            # Если требуется код подтверждения
            auth_states["inviting"] = {
                "waiting_for_code": True,
                "message_id": message.message_id,
                "chat_id": message.chat.id
            }
            
            await message.edit_text(
                "📱 Требуется код подтверждения!\n\n"
                "На ваш номер телефона был отправлен код подтверждения. "
                "Пожалуйста, отправьте его в формате:\n\n"
                "/code XXXXX"
            )
    except Exception as e:
        logger.error(f"Ошибка при подключении к Telegram API: {e}")
        await message.edit_text(
            f"❌ Ошибка при подключении к Telegram API: {e}",
            reply_markup=get_inviting_keyboard()
        )

# Обработчик для ввода кода подтверждения
@promotion_router.message(Command("code"))
async def cmd_code(message: types.Message):
    """Обработчик команды /code для ввода кода подтверждения"""
    # Проверяем, что команду отправил администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта команда доступна только администратору.")
        return
    
    # Получаем код из сообщения
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Пожалуйста, укажите код подтверждения: /code XXXXX")
        return
    
    code = args[1]
    
    # Проверяем, ожидается ли код для инвайтинга или комментинга
    if "inviting" in auth_states and auth_states["inviting"].get("waiting_for_code"):
        # Авторизация с помощью кода
        success = await managers["inviting"].sign_in_with_code(code)
        
        if success:
            # Если авторизация успешна
            await message.answer(
                "✅ Успешная авторизация!\n\n"
                "Теперь вы можете использовать функции инвайтинга.",
                reply_markup=get_inviting_keyboard()
            )
            
            # Обновляем состояние авторизации
            auth_states["inviting"]["waiting_for_code"] = False
        else:
            # Если требуется пароль двухфакторной аутентификации
            auth_states["inviting"]["waiting_for_password"] = True
            
            await message.answer(
                "🔐 Требуется пароль двухфакторной аутентификации!\n\n"
                "Пожалуйста, отправьте его в формате:\n\n"
                "/password XXXXX"
            )
    elif "commenting" in auth_states and auth_states["commenting"].get("waiting_for_code"):
        # Авторизация с помощью кода для комментинга
        success = await managers["commenting"].sign_in_with_code(code)
        
        if success:
            # Если авторизация успешна
            await message.answer(
                "✅ Успешная авторизация!\n\n"
                "Теперь вы можете использовать функции комментинга.",
                reply_markup=get_commenting_keyboard()
            )
            
            # Обновляем состояние авторизации
            auth_states["commenting"]["waiting_for_code"] = False
        else:
            # Если требуется пароль двухфакторной аутентификации
            auth_states["commenting"]["waiting_for_password"] = True
            
            await message.answer(
                "🔐 Требуется пароль двухфакторной аутентификации!\n\n"
                "Пожалуйста, отправьте его в формате:\n\n"
                "/password XXXXX"
            )
    else:
        await message.answer("Код подтверждения не требуется.")

# Обработчик для ввода пароля двухфакторной аутентификации
@promotion_router.message(Command("password"))
async def cmd_password(message: types.Message):
    """Обработчик команды /password для ввода пароля двухфакторной аутентификации"""
    # Проверяем, что команду отправил администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта команда доступна только администратору.")
        return
    
    # Получаем пароль из сообщения
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Пожалуйста, укажите пароль: /password XXXXX")
        return
    
    password = args[1]
    
    # Проверяем, ожидается ли пароль для инвайтинга или комментинга
    if "inviting" in auth_states and auth_states["inviting"].get("waiting_for_password"):
        # Авторизация с помощью пароля
        success = await managers["inviting"].sign_in_with_password(password)
        
        if success:
            # Если авторизация успешна
            await message.answer(
                "✅ Успешная авторизация с двухфакторной аутентификацией!\n\n"
                "Теперь вы можете использовать функции инвайтинга.",
                reply_markup=get_inviting_keyboard()
            )
            
            # Обновляем состояние авторизации
            auth_states["inviting"]["waiting_for_password"] = False
        else:
            await message.answer(
                "❌ Ошибка авторизации!\n\n"
                "Пожалуйста, проверьте пароль и попробуйте снова.",
                reply_markup=get_inviting_keyboard()
            )
    elif "commenting" in auth_states and auth_states["commenting"].get("waiting_for_password"):
        # Авторизация с помощью пароля для комментинга
        success = await managers["commenting"].sign_in_with_password(password)
        
        if success:
            # Если авторизация успешна
            await message.answer(
                "✅ Успешная авторизация с двухфакторной аутентификацией!\n\n"
                "Теперь вы можете использовать функции комментинга.",
                reply_markup=get_commenting_keyboard()
            )
            
            # Обновляем состояние авторизации
            auth_states["commenting"]["waiting_for_password"] = False
        else:
            await message.answer(
                "❌ Ошибка авторизации!\n\n"
                "Пожалуйста, проверьте пароль и попробуйте снова.",
                reply_markup=get_commenting_keyboard()
            )
    else:
        await message.answer("Пароль двухфакторной аутентификации не требуется.")

# Функция для регистрации обработчиков
def register_promotion_handlers(dp):
    """Регистрация обработчиков команд продвижения"""
    dp.include_router(promotion_router)