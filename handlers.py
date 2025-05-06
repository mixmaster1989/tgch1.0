from aiogram import Dispatcher, types, Router, F
from aiogram.filters import Command
from core.generator import generate_post, generate_post_with_config

# Создаем роутер для обработчиков команд
router = Router()

@router.message(Command("generate"))
async def cmd_generate(message: types.Message):
    post = generate_post_with_config()
    await message.answer(f"Сгенерировано: \n{post}")

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

def register_handlers(dp: Dispatcher):
    # Регистрируем роутер в диспетчере
    dp.include_router(router)