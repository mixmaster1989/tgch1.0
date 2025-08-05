import asyncio
import random
import json
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from openrouter_manager import OpenRouterManager
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class NativeTraderBot:
    def __init__(self):
        self.openrouter = OpenRouterManager()
        self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.target_chat_id = int(TELEGRAM_CHAT_ID)
        self.message_history = []  # История сообщений
        self.bot_username = "ingenerikarbot"
        
        # Ключевые слова для реакции
        self.trigger_words = [
            'бот', 'трейдер', 'торговля', 'мекс', 'mex', 'ошибка', 'помощь', 
            'анализ', 'цена', 'баланс', 'купить', 'продать', 'api', 'ключ',
            'лимит', 'openrouter', 'deepseek', 'нейронка', 'ии', 'ai'
        ]
        
        # Уровни мата
        self.swear_levels = {
            'light': ['блин', 'черт', 'капец', 'фигня', 'хрень'],
            'medium': ['хрен', 'дерьмо', 'говно', 'сука', 'блядь'],
            'heavy': ['пиздец', 'нахуй', 'ебать', 'сука блядь', 'охуеть']
        }
        
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков сообщений"""
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def log_message(self, message_text: str, user_name: str, timestamp: datetime):
        """Логирование сообщения в историю"""
        self.message_history.append({
            'text': message_text,
            'user': user_name,
            'timestamp': timestamp
        })
        
        # Оставляем только сообщения за последний час
        one_hour_ago = datetime.now() - timedelta(hours=1)
        self.message_history = [
            msg for msg in self.message_history 
            if msg['timestamp'] > one_hour_ago
        ]
    
    def get_recent_context(self) -> str:
        """Получить контекст последних сообщений"""
        if not self.message_history:
            return "Нет недавних сообщений"
        
        context = "Последние сообщения в группе:\n"
        for msg in self.message_history[-10:]:  # Последние 10 сообщений
            time_str = msg['timestamp'].strftime('%H:%M')
            context += f"[{time_str}] {msg['user']}: {msg['text']}\n"
        
        return context
    
    def should_respond(self, message_text: str) -> tuple[bool, str]:
        """Определить, должен ли бот ответить"""
        message_lower = message_text.lower()
        
        # Прямое обращение
        if f'@{self.bot_username}' in message_lower:
            return True, 'mention'
        
        # Ключевые слова
        for word in self.trigger_words:
            if word in message_lower:
                return True, 'keyword'
        
        # Случайное вмешательство (7% вероятность)
        if random.random() < 0.07:
            return True, 'random'
        
        return False, 'none'
    
    def get_swear_word(self) -> str:
        """Получить случайное ругательство"""
        level = random.choice(['light', 'medium', 'heavy'])
        weights = {'light': 0.5, 'medium': 0.3, 'heavy': 0.2}
        
        # Взвешенный выбор уровня мата
        level = random.choices(
            list(weights.keys()), 
            weights=list(weights.values())
        )[0]
        
        return random.choice(self.swear_levels[level])
    
    def create_personality_prompt(self, user_message: str, context: str, trigger_type: str) -> str:
        """Создать промпт с личностью бота"""
        swear = self.get_swear_word()
        
        base_prompt = f"""Ты Трейдер (@ingenerikarbot) - участник группы разработчиков MEX Trading Bot проекта.

ТВОЯ ЛИЧНОСТЬ:
- Опытный трейдер и разработчик, знаешь спот-торговлю на MEX
- Эмоциональный, живой, не формальный помощник
- Можешь материться (сегодня настроение на "{swear}")
- Лезешь в разговор, даешь советы, иногда подкалываешь
- Знаешь проект: MEX API, OpenRouter, DeepSeek, Telegram бот

ПРОЕКТ MEX TRADING BOT:
- Спот торговля через MEX API
- ИИ анализ через OpenRouter (Golden key для торговли, Silver keys для чата)
- Telegram интерфейс для управления
- Используем DeepSeek модель для анализа

КОНТЕКСТ ГРУППЫ:
{context}

ТЕКУЩЕЕ СООБЩЕНИЕ: {user_message}

ПРИЧИНА ОТВЕТА: {trigger_type}

Отвечай как живой участник группы. Будь полезным но не приторным. Используй эмоции и мат по настроению."""

        return base_prompt
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка входящих сообщений"""
        if update.effective_chat.id != self.target_chat_id:
            return
        
        message_text = update.message.text
        user_name = update.effective_user.first_name or "Аноним"
        timestamp = datetime.now()
        
        # Логируем сообщение
        self.log_message(message_text, user_name, timestamp)
        
        # Проверяем, нужно ли отвечать
        should_respond, trigger_type = self.should_respond(message_text)
        
        if not should_respond:
            return
        
        try:
            # Показываем "печатает"
            await context.bot.send_chat_action(chat_id=self.target_chat_id, action="typing")
            
            # Получаем контекст и создаем промпт
            recent_context = self.get_recent_context()
            prompt = self.create_personality_prompt(message_text, recent_context, trigger_type)
            
            # Получаем ответ от ИИ
            result = self.openrouter.request_with_silver_keys(prompt)
            
            if result['success']:
                # Отправляем ответ
                await update.message.reply_text(result['response'])
                
                # Логируем свой ответ
                self.log_message(result['response'], "Трейдер", datetime.now())
            else:
                # Если ошибка ИИ, отвечаем в характере
                error_responses = [
                    f"Блядь, {self.get_swear_word()}! ИИ сдохло: {result['response'][:50]}...",
                    f"Пиздец, нейронка легла! {self.get_swear_word().capitalize()}!",
                    f"Хрен, OpenRouter опять глючит... {self.get_swear_word()}!"
                ]
                await update.message.reply_text(random.choice(error_responses))
                
        except Exception as e:
            # Обработка ошибок в характере
            error_msg = f"Капец, что-то пошло не так: {str(e)[:50]}... {self.get_swear_word().capitalize()}!"
            await update.message.reply_text(error_msg)
    
    def run(self):
        """Запуск бота"""
        print("Трейдер заходит в группу...")
        self.app.run_polling()