import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from openrouter_manager import OpenRouterManager
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class AIChatBot:
    def __init__(self):
        self.openrouter = OpenRouterManager()
        self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.target_chat_id = int(TELEGRAM_CHAT_ID)
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков сообщений"""
        # Обработчик всех текстовых сообщений
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка входящих сообщений"""
        # Проверяем, что сообщение из нужной группы
        if update.effective_chat.id != self.target_chat_id:
            return
        
        user_message = update.message.text
        user_name = update.effective_user.first_name or "Пользователь"
        
        try:
            # Отправляем "печатает..." индикатор
            await context.bot.send_chat_action(chat_id=self.target_chat_id, action="typing")
            
            # Формируем промпт с контекстом
            prompt = f"""Ты умный помощник в торговой группе. Отвечай на русском языке кратко и по делу.
            
Пользователь {user_name} спрашивает: {user_message}

Дай полезный ответ."""
            
            # Получаем ответ от ИИ через silver ключи
            result = self.openrouter.request_with_silver_keys(prompt, "deepseek/deepseek-r1-0528:free")
            
            if result['success']:
                # Отправляем ответ в группу
                await update.message.reply_text(result['response'])
            else:
                # Если ошибка, отправляем уведомление
                await update.message.reply_text(f"Ошибка ИИ: {result['response']}")
                
        except Exception as e:
            await update.message.reply_text(f"Ошибка обработки: {str(e)}")
    
    def run(self):
        """Запуск чат-бота"""
        print("Запуск AI Chat Bot...")
        self.app.run_polling()