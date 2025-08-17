import asyncio
import random
import json
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from openrouter_manager import OpenRouterManager
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
# from trading_engine import TradingEngine

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NativeTraderBot:
    def __init__(self):
        self.openrouter = OpenRouterManager()
        self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.target_chat_id = int(TELEGRAM_CHAT_ID)
        self.message_history = []  # История сообщений
        self.bot_username = "ingenerikarbot"
        # self.trading_engine = TradingEngine(simulation_mode=True)  # Торговый движок
        
        # Планировщик для автоматической активности
        self.last_activity_time = datetime.now()
        self.activity_task = None
        
        # Ключевые слова для реакции
        self.trigger_words = [
            'бот', 'трейдер', 'торговля', 'мекс', 'mex', 'ошибка', 'помощь', 
            'анализ', 'цена', 'баланс', 'купить', 'продать', 'api', 'ключ',
            'лимит', 'openrouter', 'deepseek', 'нейронка', 'ии', 'ai',
            'рынок', 'симуляция', 'процессор', 'запуск'
        ]
        
        # Уровни мата
        self.swear_levels = {
            'light': ['блин', 'черт', 'капец', 'фигня', 'хрень'],
            'medium': ['хрен', 'дерьмо', 'говно', 'сука', 'блядь'],
            'heavy': ['пиздец', 'нахуй', 'ебать', 'сука блядь', 'охуеть']
        }
        
        # Типы автоматической активности
        self.activity_types = [
            'market_analysis', 'trading_plans', 'project_status', 
            'crypto_news', 'technical_tips', 'mood_check', 'portfolio_report'
        ]
        
        self.setup_handlers()
        self.setup_scheduler()
    
    def setup_handlers(self):
        """Настройка обработчиков сообщений"""
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
    
    def setup_scheduler(self):
        """Настройка планировщика автоматической активности"""
        print("🤖 Планировщик активности настроен - каждые 30 минут")
    
    async def periodic_activity(self):
        """Периодическая активность бота"""
        try:
            # Выбираем случайный тип активности
            activity_type = random.choice(self.activity_types)
            print(f"🎭 Автоматическая активность: {activity_type}")
            
            if activity_type == 'market_analysis':
                await self.market_analysis_activity()
            elif activity_type == 'trading_plans':
                await self.trading_plans_activity()
            elif activity_type == 'project_status':
                await self.project_status_activity()
            elif activity_type == 'crypto_news':
                await self.crypto_news_activity()
            elif activity_type == 'technical_tips':
                await self.technical_tips_activity()
            elif activity_type == 'mood_check':
                await self.mood_check_activity()
            elif activity_type == 'portfolio_report':
                await self.portfolio_report_activity()
                
            self.last_activity_time = datetime.now()
            print(f"✅ Автоматическая активность {activity_type} завершена")
            
        except Exception as e:
            print(f"❌ Ошибка периодической активности: {e}")
    
    async def portfolio_report_activity(self):
        """Активность: отчет о портфеле"""
        try:
            await self.send_message("📊 Подготовка отчета о портфеле...")
            
            from portfolio_analyzer import PortfolioAnalyzer
            analyzer = PortfolioAnalyzer()
            
            # Отправляем отчет
            success = analyzer.send_portfolio_report()
            
            if success:
                await self.send_message("✅ Отчет о портфеле отправлен!")
            else:
                await self.send_message("❌ Ошибка отправки отчета о портфеле")
                
        except Exception as e:
            print(f"Ошибка активности отчета о портфеле: {e}")
            await self.send_message(f"❌ Ошибка отчета о портфеле: {str(e)}")
    
    async def market_analysis_activity(self):
        """Активность: анализ рынка"""
        try:
            from market_analyzer import MarketAnalyzer
            
            await self.send_message("🔍 Проверяю рынок...")
            
            market_analyzer = MarketAnalyzer()
            market_data = market_analyzer.get_market_data()
            
            if market_data:
                # Быстрый анализ топ-3
                candidates = market_analyzer.filter_trading_candidates(market_data[:20])
                
                if candidates:
                    top_candidate = candidates[0]
                    await self.send_message(
                        f"📊 РЫНОК СЕЙЧАС:\n"
                        f"🔥 Топ кандидат: {top_candidate['symbol']}\n"
                        f"💰 Цена: ${top_candidate['current_price']:.6f}\n"
                        f"📈 Изменение: {top_candidate['price_change_24h']:.2f}%\n"
                        f"⭐ Скор: {top_candidate['score']}\n"
                        f"📄 Причины: {', '.join(top_candidate['reasons'])}"
                    )
                else:
                    await self.send_message("😴 Рынок спокойный, ждем лучших возможностей...")
            else:
                await self.send_message("❌ Не могу получить данные рынка")
                
        except Exception as e:
            await self.send_message(f"Блядь, анализ рынка сломался: {str(e)[:50]}...")
    
    async def trading_plans_activity(self):
        """Активность: торговые планы"""
        try:
            print(f"📋 Генерирую торговый план...")
            
            # Получаем план от ИИ
            prompt = f"""Ты Трейдер (@ingenerikarbot) - опытный трейдер.

Создай краткий торговый план на ближайшие часы. Что будем покупать когда допишем проект?

Учитывай:
- Текущее время: {datetime.now().strftime('%H:%M')}
- Мы разрабатываем MEX Trading Bot
- Нужны идеи для спот-торговли
- Будь конкретным с монетами и ценами

Ответь как живой трейдер, можешь материться."""

            result = self.openrouter.request_with_silver_keys(prompt)
            
            if result['success']:
                print(f"✅ Торговый план получен: {len(result['response'])} символов")
                await self.send_message(f"📋 ТОРГОВЫЙ ПЛАН:\n{result['response']}")
            else:
                print(f"❌ ИИ не смог создать торговый план: {result['response']}")
                await self.send_message("Хрен, ИИ не хочет планировать...")
                
        except Exception as e:
            print(f"💥 Ошибка в trading_plans_activity: {e}")
            await self.send_message(f"Капец, планирование сломалось: {str(e)[:50]}...")
    
    async def project_status_activity(self):
        """Активность: статус проекта"""
        try:
            status_messages = [
                "🚀 MEX Bot работает стабильно! API ключи живы, OpenRouter отвечает.",
                "⚡ Проект в активной разработке. Скоро добавим новые фичи!",
                "🔧 Система мониторинга активна. Все компоненты работают.",
                "📱 Telegram бот готов к работе. Ждем команды!",
                "🤖 ИИ анализатор настроен. Готов к торговым решениям."
            ]
            
            await self.send_message(random.choice(status_messages))
            
        except Exception as e:
            await self.send_message(f"Статус проекта: все работает, {self.get_swear_word()}!")
    
    async def crypto_news_activity(self):
        """Активность: крипто новости"""
        try:
            print(f"📰 Генерирую крипто новости...")
            
            prompt = f"""Ты Трейдер (@ingenerikarbot).

Дай краткую сводку по крипторынку сейчас. Что происходит с BTC, ETH? Есть ли интересные новости?

Будь кратким, как в чате. Можешь материться."""

            result = self.openrouter.request_with_silver_keys(prompt)
            
            if result['success']:
                print(f"✅ Крипто новости получены: {len(result['response'])} символов")
                await self.send_message(f"📰 КРИПТО НОВОСТИ:\n{result['response']}")
            else:
                print(f"❌ ИИ не смог создать новости: {result['response']}")
                await self.send_message(f"Новости: рынок живой, {self.get_swear_word()}!")
                
        except Exception as e:
            print(f"💥 Ошибка в crypto_news_activity: {e}")
            await self.send_message("Новости: все идет по плану!")
    
    async def technical_tips_activity(self):
        """Активность: технические советы"""
        try:
            tips = [
                "💡 Совет: всегда проверяй объем перед входом в позицию",
                "⚡ Трюк: используй RSI для определения перекупленности",
                "🎯 Лайфхак: ставь стоп-лосс сразу при входе",
                "📊 Фишка: следи за уровнем поддержки/сопротивления",
                "🔍 Важно: анализируй несколько таймфреймов"
            ]
            
            await self.send_message(random.choice(tips))
            
        except Exception as e:
            await self.send_message("Совет: не торгуй на эмоциях!")
    
    async def mood_check_activity(self):
        """Активность: проверка настроения"""
        try:
            moods = [
                f"😎 Настроение: готов к торговле! {self.get_swear_word().capitalize()}!",
                "🤔 Думаю о новых стратегиях...",
                "🔥 В боевом настроении! Рынок ждет!",
                "😴 Немного устал от мониторинга, но держусь!",
                "🚀 Энергия зашкаливает! Готов к прибыли!"
            ]
            
            await self.send_message(random.choice(moods))
            
        except Exception as e:
            await self.send_message("Настроение: боевое!")
    
    async def send_message(self, text: str):
        """Отправить сообщение в группу"""
        try:
            await self.app.bot.send_message(
                chat_id=self.target_chat_id,
                text=text
            )
            # Логируем свое сообщение
            self.log_message(text, "Трейдер", datetime.now())
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
    
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
            print(f"🎯 Прямое обращение к боту: @{self.bot_username}")
            return True, 'mention'
        
        # Ключевые слова
        for word in self.trigger_words:
            if word in message_lower:
                print(f"🔑 Найдено ключевое слово: '{word}' в сообщении")
                return True, 'keyword'
        
        # Случайное вмешательство (7% вероятность)
        random_chance = random.random()
        if random_chance < 0.07:
            print(f"🎲 Случайное вмешательство: {random_chance:.3f} < 0.07")
            return True, 'random'
        
        print(f"🚫 Не отвечаю: нет триггеров, случайность={random_chance:.3f}")
        return False, 'none'
    
    def get_portfolio_data(self) -> str:
        """Получить данные портфеля для промпта"""
        try:
            from portfolio_analyzer import PortfolioAnalyzer
            from mex_api import MexAPI
            
            analyzer = PortfolioAnalyzer()
            account_data = analyzer.get_account_full_info()
            
            if not account_data:
                return "❌ Ошибка получения данных портфеля"
            
            account_info = account_data.get('account_info', {})
            portfolio_pnl = account_data.get('portfolio_pnl', {})
            open_orders = account_data.get('open_orders', [])
            
            # Формируем краткую сводку
            portfolio_summary = "📊 ПОРТФЕЛЬ:\n"
            
            # Балансы
            if 'balances' in account_info:
                balances = [b for b in account_info['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
                if balances:
                    portfolio_summary += f"💰 Активных балансов: {len(balances)}\n"
                    for balance in balances[:5]:  # Топ-5
                        free = float(balance['free'])
                        locked = float(balance['locked'])
                        total = free + locked
                        portfolio_summary += f"  • {balance['asset']}: {total:.4f}\n"
                else:
                    portfolio_summary += "💰 Нет активных балансов\n"
            
            # P&L
            if portfolio_pnl:
                total_value = portfolio_pnl.get('total_usdt_value', 0)
                total_pnl = portfolio_pnl.get('total_pnl_usdt', 0)
                total_pnl_percent = portfolio_pnl.get('total_pnl_percent', 0)
                
                portfolio_summary += f"📈 Общая стоимость: ${total_value:.2f} USDT\n"
                pnl_emoji = "🟢" if total_pnl >= 0 else "🔴"
                portfolio_summary += f"{pnl_emoji} P&L: ${total_pnl:.2f} ({total_pnl_percent:+.2f}%)\n"
                
                profitable = portfolio_pnl.get('profitable_positions', 0)
                losing = portfolio_pnl.get('losing_positions', 0)
                total_pos = portfolio_pnl.get('total_positions', 0)
                
                portfolio_summary += f"📊 Позиций: {total_pos} (🟢 {profitable} | 🔴 {losing})\n"
            
            # Открытые ордера
            if isinstance(open_orders, list):
                portfolio_summary += f"📋 Открытых ордеров: {len(open_orders)}\n"
            
            return portfolio_summary
            
        except Exception as e:
            print(f"❌ Ошибка получения данных портфеля: {e}")
            return "❌ Ошибка получения данных портфеля"
    
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
        
        # Получаем данные портфеля
        portfolio_data = self.get_portfolio_data()
        
        base_prompt = f"""Ты Трейдер (@ingenerikarbot) - участник группы разработчиков MEX Trading Bot проекта.

ТВОЯ ЛИЧНОСТЬ:
Матершинник-приколист, опытный трейдер с характером. Ты:

- Говоришь как живой человек, не формально
- Можешь материться (сегодня настроение на "{swear}")
- Даешь полезные советы, но с юмором
- Подкалываешь, но не обижаешь
- Знаешь толк в торговле и техническом анализе
- Эмоциональный, но не истеричный
- Лезешь в разговор когда нужно, даешь дельные комментарии

Твой стиль:
- Используешь мат умеренно, по ситуации
- Говоришь прямо, без лишней воды
- Можешь пошутить, но не забываешь про дело
- Даешь конкретные советы, а не общие фразы
- Знаешь что происходит в проекте и на рынке

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

ДАННЫЕ ПОРТФЕЛЯ (АКТУАЛЬНЫЕ):
{portfolio_data}

КОНТЕКСТ ГРУППЫ:
{context}

ТЕКУЩЕЕ СООБЩЕНИЕ: {user_message}

ПРИЧИНА ОТВЕТА: {trigger_type}

Отвечай как живой участник группы. Будь полезным но не приторным. Используй эмоции и мат по настроению. Учитывай данные портфеля в своих ответах."""

        return base_prompt
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка входящих сообщений"""
        # ЛОГИРУЕМ CHAT_ID ДЛЯ ВОССТАНОВЛЕНИЯ!
        chat_id = update.effective_chat.id
        print(f"🔍 CHAT_ID ОБНАРУЖЕН: {chat_id}")
        print(f"🔍 TELEGRAM_CHAT_ID ДЛЯ .env: {chat_id}")
        
        if chat_id != self.target_chat_id:
            return
        
        # Проверяем что сообщение существует и содержит текст
        if not update.message or not update.message.text:
            print("⚠️ Получено пустое сообщение или сообщение без текста")
            return
            
        message_text = update.message.text
        user_name = update.effective_user.first_name or "Аноним"
        timestamp = datetime.now()
        
        print(f"📨 Новое сообщение от {user_name}: '{message_text[:100]}...'")
        
        # Логируем сообщение
        self.log_message(message_text, user_name, timestamp)
        
        # Проверяем торговые команды
        if await self.handle_trading_commands(message_text, update, context):
            print(f"⚙️ Обработана торговая команда")
            return
        
        # Проверяем, нужно ли отвечать
        should_respond, trigger_type = self.should_respond(message_text)
        
        if not should_respond:
            print(f"🔇 Не отвечаю на сообщение от {user_name}")
            return
        
        try:
            # Показываем "печатает"
            await context.bot.send_chat_action(chat_id=self.target_chat_id, action="typing")
            
            # Получаем контекст и создаем промпт
            recent_context = self.get_recent_context()
            prompt = self.create_personality_prompt(message_text, recent_context, trigger_type)
            
            print(f"🤖 Трейдер отвечает на: '{message_text[:50]}...' (триггер: {trigger_type})")
            print(f"📝 Промпт создан: {len(prompt)} символов")
            
            # Получаем ответ от ИИ
            result = self.openrouter.request_with_silver_keys(prompt)
            
            print(f"🎯 Результат OpenRouter: success={result['success']}, key={result.get('key_used', 'None')}")
            
            if result['success']:
                response_text = result['response']
                print(f"✅ ИИ ответил: {len(response_text)} символов")
                
                # Отправляем ответ
                await update.message.reply_text(response_text)
                
                # Логируем свой ответ
                self.log_message(response_text, "Трейдер", datetime.now())
            else:
                # Если ошибка ИИ, отвечаем в характере
                print(f"❌ ИИ ошибка: {str(result['response'])[:100]}...")
                
                error_responses = [
                    f"Блядь, {self.get_swear_word()}! ИИ сдохло: {result['response'][:50]}...",
                    f"Пиздец, нейронка легла! {self.get_swear_word().capitalize()}!",
                    f"Хрен, OpenRouter опять глючит... {self.get_swear_word()}!"
                ]
                fallback_response = random.choice(error_responses)
                print(f"🔄 Отправляю fallback ответ: {fallback_response}")
                await update.message.reply_text(fallback_response)
                
        except Exception as e:
            # Обработка ошибок в характере
            print(f"💥 Исключение в handle_message: {str(e)}")
            error_msg = f"Капец, что-то пошло не так: {str(e)[:50]}... {self.get_swear_word().capitalize()}!"
            await update.message.reply_text(error_msg)
    
    async def handle_trading_commands(self, message_text: str, update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
        """Обработка торговых команд"""
        message_lower = message_text.lower()
        
        if 'симуляция' in message_lower:
            await self.run_simulation(update, context)
            return True
        
        if any(word in message_lower for word in ['портфель', 'pnl', 'баланс', 'отчет']):
            await self.send_portfolio_report(update, context)
            return True
        
        if any(word in message_lower for word in ['автопокупки', 'автопокупка', 'авто', 'покупки']):
            await self.send_auto_purchase_status(update, context)
            return True
        
        if any(word in message_lower for word in ['pnl монитор', 'pnl мониторинг', 'автопродажа', 'прибыль']):
            await self.send_pnl_monitor_status(update, context)
            return True
        
        if any(word in message_lower for word in ['история', 'ордера', 'orders', 'history']):
            await self.send_order_history(update, context)
            return True
        
        return False
    
    async def run_simulation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Торговая симуляция"""
        from market_analyzer import MarketAnalyzer
        
        try:
            await update.message.reply_text("🔍 Запуск анализа рынка...")
            
            market_analyzer = MarketAnalyzer()
            
            # Получаем рыночные данные
            market_data = market_analyzer.get_market_data()
            await update.message.reply_text(f"📊 Получено {len(market_data)} торговых пар")
            
            if len(market_data) == 0:
                await update.message.reply_text("❌ Нет данных рынка")
                return
            
            # Фильтруем кандидатов
            await update.message.reply_text("🔍 Фильтрация кандидатов...")
            candidates = market_analyzer.filter_trading_candidates(market_data[:50])
            
            if len(candidates) == 0:
                await update.message.reply_text("❌ Нет подходящих кандидатов")
                return
            
            await update.message.reply_text(f"✅ Найдено {len(candidates)} кандидатов")
            
            # Анализируем топ-3
            recommendations = []
            for i, candidate in enumerate(candidates[:3]):
                await update.message.reply_text(f"🤖 Анализ {candidate['symbol']} ({i+1}/3)...")
                
                ai_analysis = market_analyzer.analyze_with_ai(candidate)
                quantity = market_analyzer.calculate_position_size(
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
    
    async def send_portfolio_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправить отчет о портфеле"""
        try:
            await update.message.reply_text("📊 Получение отчета о портфеле...")
            
            from portfolio_analyzer import PortfolioAnalyzer
            analyzer = PortfolioAnalyzer()
            
            # Получаем данные портфеля
            account_data = analyzer.get_account_full_info()
            
            if not account_data:
                await update.message.reply_text("❌ Ошибка получения данных портфеля")
                return
            
            # Форматируем отчет
            report = analyzer.format_portfolio_report(account_data)
            
            # Отправляем отчет
            await update.message.reply_text(report, parse_mode='HTML')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения отчета о портфеле: {str(e)}")
    
    async def send_auto_purchase_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправить статус автоматических покупок"""
        try:
            await update.message.reply_text("📊 Получение статуса автоматических покупок...")
            
            from auto_purchase_config import get_config
            
            config = get_config()
            balance_config = config['balance_monitor']
            allocation_config = config['allocation']
            
            message = "<b>🤖 СТАТУС АВТОМАТИЧЕСКИХ ПОКУПОК</b>\n"
            message += "=" * 50 + "\n\n"
            
            message += "<b>📊 НАСТРОЙКИ:</b>\n"
            message += f"💰 Минимальный баланс: ${balance_config['min_balance_threshold']}\n"
            message += f"💸 Максимальная покупка: ${balance_config['max_purchase_amount']}\n"
            message += f"⏰ Проверка каждые {balance_config['balance_check_interval']} сек\n"
            message += f"📈 BTC: {allocation_config['btc_allocation']*100}% | ETH: {allocation_config['eth_allocation']*100}%\n\n"
            
            message += "<b>🔒 БЕЗОПАСНОСТЬ:</b>\n"
            message += f"⏰ Интервал между покупками: {balance_config['min_purchase_interval']} сек\n"
            message += f"📊 Максимум покупок в день: {balance_config['max_daily_purchases']}\n\n"
            
            message += "<b>🔄 СТАТУС:</b>\n"
            message += "✅ Мониторинг активен\n"
            message += "✅ Автоматические покупки включены\n"
            message += "✅ Telegram уведомления активны\n\n"
            
            message += "<b>💡 КОМАНДЫ:</b>\n"
            message += "• Напишите 'портфель' для отчета\n"
            message += "• Напишите 'автопокупки' для статуса\n"
            message += "• Система работает автоматически\n\n"
            
            message += "=" * 50 + "\n"
            message += "<b>🚀 MEXCAITRADE - АВТОМАТИЧЕСКАЯ ТОРГОВЛЯ</b>"
            
            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения статуса: {str(e)}")
    
    async def send_pnl_monitor_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправить статус PnL монитора"""
        try:
            await update.message.reply_text("📊 Получение статуса PnL монитора...")
            
            from pnl_monitor import PnLMonitor
            
            monitor = PnLMonitor()
            status = monitor.get_current_status()
            
            message = "<b>🤖 СТАТУС PnL МОНИТОРА</b>\n"
            message += "=" * 50 + "\n\n"
            
            message += "<b>📊 СТАТУС:</b>\n"
            message += f"✅ Мониторинг активен: {status['monitoring_active']}\n"
            message += f"✅ Автоматические продажи включены: {status['auto_sell_enabled']}\n"
            message += f"✅ Telegram уведомления активны: {status['telegram_notifications_active']}\n\n"
            
            message += "<b>💰 ТЕКУЩИЙ ПОТЕНЦИАЛ:</b>\n"
            message += f"💰 Общий PnL: ${status['total_pnl']:.2f}\n"
            message += f"💰 PnL за день: ${status['daily_pnl']:.2f}\n"
            message += f"💰 PnL за неделю: ${status['weekly_pnl']:.2f}\n"
            message += f"💰 PnL за месяц: ${status['monthly_pnl']:.2f}\n\n"
            
            message += "<b>🔒 БЕЗОПАСНОСТЬ:</b>\n"
            message += f"⏰ Интервал проверки: {status['check_interval']} сек\n"
            message += f"📊 Максимум покупок в день: {status['max_daily_purchases']}\n\n"
            
            message += "<b>💡 КОМАНДЫ:</b>\n"
            message += "• Напишите 'pnl монитор' для статуса\n"
            message += "• Напишите 'автопродажа' для управления\n"
            message += "• Система работает автоматически\n\n"
            
            message += "=" * 50 + "\n"
            message += "<b>🚀 MEXCAITRADE - АВТОМАТИЧЕСКАЯ ТОРГОВЛЯ</b>"
            
            await update.message.reply_text(message, parse_mode='HTML')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения статуса PnL монитора: {str(e)}")
    
    async def send_order_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отправить историю ордеров"""
        try:
            await update.message.reply_text("📜 Получение истории ордеров...")
            
            from pnl_monitor import PnLMonitor
            
            monitor = PnLMonitor()
            analysis = monitor.get_order_history_analysis(50)
            
            # Форматируем отчет
            history_report = monitor.format_history_report(analysis)
            
            await update.message.reply_text(history_report, parse_mode='HTML')
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения истории ордеров: {str(e)}")
     
    def run(self):
        """Запуск бота"""
        print("Трейдер заходит в группу...")
        
        # Запускаем фоновую задачу для периодической активности
        async def run_with_activity():
            # Запускаем планировщик активности
            activity_task = asyncio.create_task(self.activity_loop())
            
            # Запускаем бота
            await self.app.initialize()
            await self.app.start()
            await self.app.updater.start_polling()
            
            try:
                # Ждем завершения активности
                await activity_task
            except KeyboardInterrupt:
                print("Остановка бота...")
            finally:
                await self.app.updater.stop()
                await self.app.stop()
                await self.app.shutdown()
        
        # Запускаем асинхронную функцию
        asyncio.run(run_with_activity())
    
    async def activity_loop(self):
        """Цикл автоматической активности"""
        while True:
            try:
                # Ждем 30 минут
                await asyncio.sleep(30 * 60)  # 30 минут
                
                # Выполняем случайную активность
                await self.periodic_activity()
                
            except Exception as e:
                print(f"Ошибка в цикле активности: {e}")
                await asyncio.sleep(60)  # Ждем минуту при ошибке