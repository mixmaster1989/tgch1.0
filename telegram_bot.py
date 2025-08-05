import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from mex_api import MexAPI
from neural_analyzer import NeuralAnalyzer
from market_analyzer import MarketAnalyzer
from config import TELEGRAM_BOT_TOKEN, DEFAULT_TRADE_AMOUNT
import json

class TradingBot:
    def __init__(self):
        self.mex_api = MexAPI()
        self.analyzer = NeuralAnalyzer()
        self.market_analyzer = MarketAnalyzer()
        self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("balance", self.get_balance))
        self.app.add_handler(CommandHandler("price", self.get_price))
        self.app.add_handler(CommandHandler("analyze", self.analyze_symbol))
        self.app.add_handler(CommandHandler("orders", self.get_orders))
        self.app.add_handler(CommandHandler("симуляция", self.run_simulation))
        self.app.add_handler(CallbackQueryHandler(self.button_handler))
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Стартовое сообщение"""
        keyboard = [
            [InlineKeyboardButton("💰 Баланс", callback_data="balance")],
            [InlineKeyboardButton("📊 Анализ", callback_data="analyze_menu")],
            [InlineKeyboardButton("📋 Ордера", callback_data="orders")],
            [InlineKeyboardButton("🎯 Симуляция", callback_data="simulation")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 MEX Trading Bot запущен!\n\n"
            "Доступные команды:\n"
            "/balance - баланс аккаунта\n"
            "/price SYMBOL - цена символа\n"
            "/analyze SYMBOL - анализ символа\n"
            "/orders - открытые ордера\n"
            "/симуляция - полный анализ рынка",
            reply_markup=reply_markup
        )
    
    async def get_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получить баланс аккаунта"""
        try:
            account_info = self.mex_api.get_account_info()
            
            if 'balances' in account_info:
                balances = [b for b in account_info['balances'] if float(b['free']) > 0]
                
                message = "💰 Баланс аккаунта:\n\n"
                for balance in balances[:10]:  # Показываем только первые 10
                    free = float(balance['free'])
                    locked = float(balance['locked'])
                    if free > 0 or locked > 0:
                        message += f"{balance['asset']}: {free:.8f} (заблокировано: {locked:.8f})\n"
                
                await update.message.reply_text(message)
            else:
                await update.message.reply_text(f"❌ Ошибка: {account_info}")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения баланса: {str(e)}")
    
    async def get_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получить цену символа"""
        if not context.args:
            await update.message.reply_text("❌ Укажите символ: /price BTCUSDT")
            return
        
        symbol = context.args[0].upper()
        
        try:
            price_data = self.mex_api.get_ticker_price(symbol)
            
            if 'price' in price_data:
                price = float(price_data['price'])
                await update.message.reply_text(f"💹 {symbol}: ${price:.8f}")
            else:
                await update.message.reply_text(f"❌ Ошибка: {price_data}")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения цены: {str(e)}")
    
    async def analyze_symbol(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Анализ символа с помощью ИИ"""
        if not context.args:
            await update.message.reply_text("❌ Укажите символ: /analyze BTCUSDT")
            return
        
        symbol = context.args[0].upper()
        
        try:
            await update.message.reply_text("🔄 Анализирую данные...")
            
            # Получаем данные свечей
            klines = self.mex_api.get_klines(symbol, '1h', 100)
            
            if isinstance(klines, list) and len(klines) > 0:
                # Анализируем с помощью ИИ
                analysis = self.analyzer.analyze_market_data(klines, symbol)
                
                message = f"🤖 Анализ {symbol}:\n\n"
                message += f"📊 Рекомендация: {analysis['recommendation']}\n"
                message += f"🎯 Уверенность: {analysis['confidence']:.1%}\n"
                message += f"📉 Поддержка: ${analysis['support_level']:.8f}\n"
                message += f"📈 Сопротивление: ${analysis['resistance_level']:.8f}\n\n"
                message += f"💭 Анализ: {analysis['analysis']}"
                
                # Добавляем кнопки для торговли
                keyboard = []
                if analysis['recommendation'] == 'BUY':
                    keyboard.append([InlineKeyboardButton("🟢 Купить", callback_data=f"buy_{symbol}")])
                elif analysis['recommendation'] == 'SELL':
                    keyboard.append([InlineKeyboardButton("🔴 Продать", callback_data=f"sell_{symbol}")])
                
                reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None
                await update.message.reply_text(message, reply_markup=reply_markup)
            else:
                await update.message.reply_text(f"❌ Не удалось получить данные для {symbol}")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка анализа: {str(e)}")
    
    async def get_orders(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получить открытые ордера"""
        try:
            orders = self.mex_api.get_open_orders()
            
            if isinstance(orders, list):
                if len(orders) == 0:
                    await update.message.reply_text("📋 Открытых ордеров нет")
                else:
                    message = "📋 Открытые ордера:\n\n"
                    for order in orders:
                        message += f"🔸 {order['symbol']}: {order['side']} {order['origQty']} @ {order['price']}\n"
                    await update.message.reply_text(message)
            else:
                await update.message.reply_text(f"❌ Ошибка: {orders}")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка получения ордеров: {str(e)}")
    
    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатий кнопок"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "balance":
            await self.get_balance(update, context)
        elif data == "orders":
            await self.get_orders(update, context)
        elif data == "simulation":
            await self.run_simulation(update, context)
        elif data.startswith("buy_") or data.startswith("sell_"):
            action, symbol = data.split("_", 1)
            await query.edit_message_text(f"⚠️ Торговые операции будут добавлены в следующей версии\n{action.upper()} {symbol}")
    
    async def run_simulation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Полная симуляция торгового анализа"""
        try:
            await update.message.reply_text("🔍 Запуск анализа рынка...")
            
            # Получаем рыночные данные
            market_data = self.market_analyzer.get_market_data()
            await update.message.reply_text(f"📊 Получено {len(market_data)} торговых пар")
            
            if len(market_data) == 0:
                await update.message.reply_text("❌ Не удалось получить данные рынка")
                return
            
            # Фильтруем кандидатов
            await update.message.reply_text("🔍 Фильтрация кандидатов...")
            candidates = self.market_analyzer.filter_trading_candidates(market_data[:50])  # Ограничиваем для скорости
            
            if len(candidates) == 0:
                await update.message.reply_text("❌ Не найдено подходящих кандидатов")
                return
            
            await update.message.reply_text(f"✅ Найдено {len(candidates)} кандидатов")
            
            # Анализируем топ-3
            recommendations = []
            for i, candidate in enumerate(candidates[:3]):
                await update.message.reply_text(f"🤖 Анализ {candidate['symbol']} ({i+1}/3)...")
                
                # ИИ анализ
                ai_analysis = self.market_analyzer.analyze_with_ai(candidate)
                
                # Размер позиции
                quantity = self.market_analyzer.calculate_position_size(
                    candidate['symbol'], 
                    candidate['current_price'], 
                    candidate['score']
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
            
            # Вывод результатов
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
                message += f"🤖 Анализ: {rec['ai_analysis'][:200]}..."
                
                await update.message.reply_text(message)
            
            # Итоговая статистика
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
        """Запуск бота"""
        print("🤖 Запуск Telegram бота...")
        self.app.run_polling()