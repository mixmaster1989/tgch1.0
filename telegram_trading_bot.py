#!/usr/bin/env python3
"""
Telegram бот для торговых уведомлений
Показывает инвесторам что делает бот в реальном времени
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# Импорты для Telegram
import aiohttp
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

class TelegramTradingBot:
    """Telegram бот для торговых уведомлений"""
    
    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        
        # Статистика торговли
        self.trading_stats = {
            'total_trades': 0,
            'profitable_trades': 0,
            'total_profit': 0.0,
            'total_volume': 0.0,
            'start_time': datetime.now()
        }
        
        # Активные ордера
        self.active_orders = {}
        
    async def send_message(self, message: str, parse_mode: str = "Markdown"):
        """Отправка сообщения в Telegram"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        logger.info("✅ Сообщение отправлено в Telegram")
                    else:
                        logger.error(f"❌ Ошибка отправки в Telegram: {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Ошибка отправки в Telegram: {e}")
    
    async def send_market_analysis(self, analysis: Dict):
        """Отправка анализа рынка"""
        try:
            symbol = analysis.get('symbol', 'N/A')
            price = analysis.get('price', 0)
            change_24h = analysis.get('change_24h', 0)
            indicators = analysis.get('indicators', {})
            
            message = f"""
🔍 **АНАЛИЗ РЫНКА {symbol}**

💰 **ЦЕНА:** ${price:,.2f}
📊 **ИЗМЕНЕНИЕ 24Ч:** {change_24h:+.2f}%

📈 **ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ:**
• RSI (14): {indicators.get('rsi_14', 0):.1f}
• MACD: {indicators.get('macd', {}).get('histogram', 0):.4f}
• SMA (20): ${indicators.get('sma_20', 0):.2f}

⏰ **ВРЕМЯ:** {datetime.now().strftime('%H:%M:%S')}
"""
            
            await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки анализа: {e}")
    
    async def send_news_analysis(self, news: Dict):
        """Отправка анализа новостей"""
        try:
            sentiment = news.get('sentiment', 'neutral')
            impact_score = news.get('impact_score', 0)
            recent_news = news.get('recent_news', [])
            
            sentiment_emoji = {
                'positive': '🟢',
                'negative': '🔴',
                'neutral': '🟡'
            }.get(sentiment, '🟡')
            
            message = f"""
📰 **НОВОСТНОЙ АНАЛИЗ**

{sentiment_emoji} **НАСТРОЕНИЯ:** {sentiment.title()}
🎯 **ВЛИЯНИЕ:** {impact_score:.2f}

📰 **ПОСЛЕДНИЕ НОВОСТИ:**
"""
            
            for i, news_item in enumerate(recent_news[:3], 1):
                title = news_item.get('title', 'N/A')[:50]
                impact = news_item.get('impact', 'neutral')
                impact_emoji = "🟢" if impact == 'positive' else "🔴" if impact == 'negative' else "🟡"
                message += f"{i}. {impact_emoji} {title}...\n"
            
            message += f"\n⏰ **ВРЕМЯ:** {datetime.now().strftime('%H:%M:%S')}"
            
            await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки новостей: {e}")
    
    async def send_trading_decision(self, decision: Dict):
        """Отправка торгового решения"""
        try:
            action = decision.get('action', 'HOLD')
            reason = decision.get('reason', 'Нет сигналов')
            confidence = decision.get('confidence', 0)
            price = decision.get('price', 0)
            quantity = decision.get('quantity', 0)
            
            action_emoji = {
                'BUY': '📈',
                'SELL': '📉',
                'HOLD': '⏸️'
            }.get(action, '❓')
            
            message = f"""
{action_emoji} **ТОРГОВОЕ РЕШЕНИЕ**

🎯 **ДЕЙСТВИЕ:** {action}
💡 **ПРИЧИНА:** {reason}
🎯 **УВЕРЕННОСТЬ:** {confidence:.1%}

"""
            
            if action in ['BUY', 'SELL']:
                message += f"""
💰 **ЦЕНА:** ${price:,.2f}
📊 **КОЛИЧЕСТВО:** {quantity:.3f} ETH
💵 **СУММА:** ${price * quantity:.2f}
"""
            
            message += f"\n⏰ **ВРЕМЯ:** {datetime.now().strftime('%H:%M:%S')}"
            
            await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки решения: {e}")
    
    async def send_order_created(self, order: Dict):
        """Отправка уведомления о создании ордера"""
        try:
            symbol = order.get('symbol', 'N/A')
            side = order.get('side', 'N/A')
            quantity = order.get('quantity', 0)
            price = order.get('price', 0)
            order_id = order.get('orderId', 'N/A')
            
            side_emoji = "📈" if side == 'BUY' else "📉"
            
            message = f"""
{side_emoji} **ОРДЕР СОЗДАН**

🆔 **ID:** {order_id}
💰 **СИМВОЛ:** {symbol}
📊 **ТИП:** {side}
💵 **ЦЕНА:** ${price:,.2f}
📈 **КОЛИЧЕСТВО:** {quantity:.3f} ETH
💸 **СУММА:** ${price * quantity:.2f}

⏰ **ВРЕМЯ:** {datetime.now().strftime('%H:%M:%S')}
"""
            
            await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки ордера: {e}")
    
    async def send_order_filled(self, order: Dict, fill_price: float):
        """Отправка уведомления об исполнении ордера"""
        try:
            symbol = order.get('symbol', 'N/A')
            side = order.get('side', 'N/A')
            quantity = order.get('quantity', 0)
            order_price = order.get('price', 0)
            order_id = order.get('orderId', 'N/A')
            
            side_emoji = "📈" if side == 'BUY' else "📉"
            
            # Вычисляем разницу
            price_diff = fill_price - order_price
            price_diff_percent = (price_diff / order_price) * 100
            
            message = f"""
✅ **ОРДЕР ИСПОЛНЕН**

{side_emoji} **ID:** {order_id}
💰 **СИМВОЛ:** {symbol}
📊 **ТИП:** {side}
💵 **ЦЕНА ОРДЕРА:** ${order_price:,.2f}
💵 **ЦЕНА ИСПОЛНЕНИЯ:** ${fill_price:,.2f}
📈 **КОЛИЧЕСТВО:** {quantity:.3f} ETH

📊 **РАЗНИЦА:** {price_diff:+.2f} ({price_diff_percent:+.2f}%)

⏰ **ВРЕМЯ:** {datetime.now().strftime('%H:%M:%S')}
"""
            
            await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки исполнения: {e}")
    
    async def send_profit_report(self, buy_order: Dict, sell_order: Dict, profit: float):
        """Отправка отчета о прибыли"""
        try:
            symbol = buy_order.get('symbol', 'N/A')
            quantity = buy_order.get('quantity', 0)
            buy_price = buy_order.get('price', 0)
            sell_price = sell_order.get('price', 0)
            
            profit_percent = (profit / (buy_price * quantity)) * 100
            
            profit_emoji = "🟢" if profit > 0 else "🔴"
            
            message = f"""
{profit_emoji} **ОТЧЕТ О ПРИБЫЛИ**

💰 **СИМВОЛ:** {symbol}
📈 **КОЛИЧЕСТВО:** {quantity:.3f} ETH

📉 **ПОКУПКА:** ${buy_price:,.2f}
📈 **ПРОДАЖА:** ${sell_price:,.2f}

💵 **ПРИБЫЛЬ:** ${profit:.4f} ({profit_percent:+.2f}%)

📊 **ОБНОВЛЕННАЯ СТАТИСТИКА:**
• Всего сделок: {self.trading_stats['total_trades']}
• Прибыльных: {self.trading_stats['profitable_trades']}
• Общая прибыль: ${self.trading_stats['total_profit']:.4f}

⏰ **ВРЕМЯ:** {datetime.now().strftime('%H:%M:%S')}
"""
            
            await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки отчета: {e}")
    
    async def send_daily_summary(self):
        """Отправка дневного отчета"""
        try:
            runtime = datetime.now() - self.trading_stats['start_time']
            win_rate = (self.trading_stats['profitable_trades'] / self.trading_stats['total_trades'] * 100) if self.trading_stats['total_trades'] > 0 else 0
            
            message = f"""
📊 **ДНЕВНОЙ ОТЧЕТ ТОРГОВОГО БОТА**

⏱️ **ВРЕМЯ РАБОТЫ:** {runtime.days}д {runtime.seconds // 3600}ч {(runtime.seconds % 3600) // 60}м

📈 **СТАТИСТИКА:**
• Всего сделок: {self.trading_stats['total_trades']}
• Прибыльных: {self.trading_stats['profitable_trades']}
• Процент успеха: {win_rate:.1f}%

💰 **ФИНАНСЫ:**
• Общая прибыль: ${self.trading_stats['total_profit']:.4f}
• Общий объем: ${self.trading_stats['total_volume']:.2f}

🎯 **АКТИВНЫЕ ОРДЕРА:** {len(self.active_orders)}

⏰ **ВРЕМЯ:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            await self.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки отчета: {e}")
    
    def update_stats(self, trade_result: Dict):
        """Обновление статистики"""
        try:
            self.trading_stats['total_trades'] += 1
            
            if trade_result.get('profit', 0) > 0:
                self.trading_stats['profitable_trades'] += 1
            
            self.trading_stats['total_profit'] += trade_result.get('profit', 0)
            self.trading_stats['total_volume'] += trade_result.get('volume', 0)
            
        except Exception as e:
            logger.error(f"❌ Ошибка обновления статистики: {e}")

# Глобальный экземпляр для использования в других модулях
telegram_bot = TelegramTradingBot() 