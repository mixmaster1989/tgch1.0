import asyncio
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from openrouter_manager import OpenRouterManager
from market_analyzer import MarketAnalyzer
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class AIChatBot:
    def __init__(self):
        self.openrouter = OpenRouterManager()
        self.market_analyzer = MarketAnalyzer()
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
        
        user_message = update.message.text.strip().lower()
        user_name = update.effective_user.first_name or "Пользователь"
        
        # Проверяем команду симуляции
        if user_message == "симуляция":
            await self.run_simulation(update, context)
            return
        
        try:
            # Отправляем "печатает..." индикатор
            await context.bot.send_chat_action(chat_id=self.target_chat_id, action="typing")
            
            # Формируем промпт с контекстом
            prompt = f"""Ты умный помощник в торговой группе. Отвечай на русском языке кратко и по делу.
            
Пользователь {user_name} спрашивает: {update.message.text}

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
    
    async def run_simulation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Торговая симуляция"""
        try:
            await update.message.reply_text("🔍 Запуск анализа рынка...")
            
            # Получаем рыночные данные
            market_data = self.market_analyzer.get_market_data()
            await update.message.reply_text(f"📊 Получено {len(market_data)} торговых пар")
            
            if len(market_data) == 0:
                await update.message.reply_text("❌ Нет данных рынка")
                return
            
            # Фильтруем кандидатов
            await update.message.reply_text("🔍 Фильтрация кандидатов...")
            candidates = self.market_analyzer.filter_trading_candidates(market_data[:50])
            
            if len(candidates) == 0:
                await update.message.reply_text("❌ Нет подходящих кандидатов")
                return
            
            await update.message.reply_text(f"✅ Найдено {len(candidates)} кандидатов")
            
            # Анализируем топ-3
            recommendations = []
            for i, candidate in enumerate(candidates[:3]):
                await update.message.reply_text(f"🤖 Анализ {candidate['symbol']} ({i+1}/3)...")
                
                ai_analysis = self.market_analyzer.analyze_with_ai(candidate)
                quantity = self.market_analyzer.calculate_position_size(
                    candidate['symbol'], candidate['current_price'], candidate['score']
                )
                
                recommendation = {
                    'symbol': candidate['symbol'],
                    'action': ai_analysis['recommendation'],
                    'confidence': ai_analysis['confidence'],
                    'quantity': quantity,
                    'price': candidate['current_price'],
                    'score': candidate['score'],
                    'reasons': candidate['reasons'],
                    'ai_analysis': ai_analysis['analysis'],
                    'position_size_usdt': quantity * candidate['current_price']
                }
                recommendations.append(recommendation)
            
            # Выводим результаты
            await update.message.reply_text("🏆 РЕЗУЛЬТАТЫ АНАЛИЗА:")
            
            for i, rec in enumerate(recommendations, 1):
                action_emoji = "🟢" if rec['action'] == 'BUY' else "🔴" if rec['action'] == 'SELL' else "🟡"
                
                message = f"{action_emoji} {i}. {rec['symbol']}\n"
                message += f"⚙️ Действие: {rec['action']}\n"
                message += f"🎯 Уверенность: {rec['confidence']:.1%}\n"
                message += f"💰 Цена: ${rec['price']:.6f}\n"
                message += f"📈 Количество: {rec['quantity']}\n"
                message += f"💵 Размер: ${rec['position_size_usdt']:.2f}\n"
                message += f"⭐ Скор: {rec['score']}\n"
                message += f"📄 Причины: {', '.join(rec['reasons'])}\n\n"
                message += f"🤖 Анализ: {rec['ai_analysis']}"
                
                await update.message.reply_text(message)
            
            # Итого
            total_usdt = sum(rec['position_size_usdt'] for rec in recommendations)
            buy_count = sum(1 for rec in recommendations if rec['action'] == 'BUY')
            
            summary = f"📊 ИТОГО:\n"
            summary += f"📋 Проанализировано: {len(recommendations)} монет\n"
            summary += f"🟢 К покупке: {buy_count}\n"
            summary += f"💰 Общий объем: ${total_usdt:.2f}"
            
            await update.message.reply_text(summary)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка симуляции: {str(e)}")
    
    def run(self):
        """Запуск чат-бота"""
        print("Запуск AI Chat Bot...")
        self.app.run_polling()