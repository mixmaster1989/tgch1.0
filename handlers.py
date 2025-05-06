from aiogram import Dispatcher, types, Router, F
from aiogram.filters import Command
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

@router.message(Command("generate"))
async def cmd_generate(message: types.Message):
    post = generate_post_with_config()
    await message.answer(f"Сгенерировано: \n{post}")

@router.message(Command("publish"))
async def cmd_publish(message: types.Message):
    # Проверяем, что команду отправил администратор
    if message.from_user.id != ADMIN_ID:
        await message.answer("Эта команда доступна только администратору.")
        return
        
    post = generate_post_with_config()
    
    # Публикуем пост в канал
    if CHANNEL_ID:
        try:
            # Отправляем сообщение в канал
            await message.bot.send_message(chat_id=CHANNEL_ID, text=post)
            await message.answer(f"Пост опубликован в канале!")
        except Exception as e:
            await message.answer(f"Ошибка при публикации в канал: {e}")
    else:
        await message.answer("ID канала не настроен в конфигурации.")

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я помогу тебе раскрутить твой канал. Напиши /generate, чтобы начать.")

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = """
🤖 *TGE Bot* - помощник для раскрутки Telegram-канала

Доступные команды:
/start - Начать работу с ботом
/generate - Сгенерировать пост для канала
/publish - Сгенерировать и опубликовать пост в канал (только для админа)
/help - Показать это сообщение
/generate_type - Сгенерировать пост определенного типа и категории

Скоро будут доступны:
- Планирование постов
- Аналитика канала
- Система рефералов
    """
    await message.answer(help_text, parse_mode="Markdown")

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

def register_handlers(dp: Dispatcher):
    # Регистрируем роутер в диспетчере
    dp.include_router(router)