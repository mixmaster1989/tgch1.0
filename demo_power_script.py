#!/usr/bin/env python3
"""
ДЕМОНСТРАЦИЯ МОЩИ ПРОЕКТА MEXCAITRADE
Скрипт для сбора полной информации по 3 монетам и отправки в Telegram
"""

import asyncio
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_data_manager import ComprehensiveDataManager
from perplexity_analyzer import PerplexityAnalyzer
from technical_indicators import TechnicalIndicators
from correlation_analyzer import CorrelationAnalyzer
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests

class PowerDemoScript:
    def __init__(self):
        self.data_manager = ComprehensiveDataManager()
        self.perplexity = PerplexityAnalyzer()
        self.technical_indicators = TechnicalIndicators()
        self.correlation_analyzer = CorrelationAnalyzer()
        
        # Выбираем 3 популярные монеты для демонстрации
        self.demo_symbols = ['BTCUSDT', 'ETHUSDT', 'ADAUSDT']
        
        # Telegram настройки
        self.telegram_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
    async def collect_comprehensive_data(self, symbol: str) -> Dict:
        """Сбор полных данных по символу"""
        print(f"🔍 Сбор данных для {symbol}...")
        
        data = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'market_data': None,
            'technical_indicators': None,
            'news_data': None,
            'correlations': None,
            'orderbook': None,
            'trade_history': None
        }
        
        try:
            # 1. Рыночные данные
            market_data = self.data_manager.get_market_data(symbol)
            if market_data:
                data['market_data'] = {
                    'price': market_data.price,
                    'change_24h': market_data.change_24h,
                    'volume_24h': market_data.volume_24h,
                    'high_24h': market_data.high_24h,
                    'low_24h': market_data.low_24h
                }
            
            # 2. Технические индикаторы
            indicators = self.data_manager.get_technical_indicators(symbol, '1m')
            if indicators:
                data['technical_indicators'] = indicators.to_dict()
            
            # 3. Новостные данные через Perplexity
            try:
                news_data = await self.perplexity.collect_coin_data(symbol)
                if news_data:
                    data['news_data'] = news_data
            except Exception as e:
                print(f"⚠️ Ошибка получения новостей для {symbol}: {e}")
            
            # 4. Корреляции
            correlations = self.data_manager.get_correlation_data(symbol)
            if correlations:
                data['correlations'] = correlations
            
            # 5. Order Book
            orderbook = self.data_manager.get_orderbook_data(symbol)
            if orderbook:
                data['orderbook'] = orderbook.to_dict()
            
            # 6. История сделок
            trade_history = self.data_manager.get_trade_history(symbol)
            if trade_history:
                data['trade_history'] = trade_history.to_dict()
                
        except Exception as e:
            print(f"❌ Ошибка сбора данных для {symbol}: {e}")
        
        return data
    
    def format_market_data(self, data: Dict) -> str:
        """Форматирование рыночных данных"""
        if not data.get('market_data'):
            return "❌ Данные недоступны"
        
        md = data['market_data']
        change_emoji = "📈" if md['change_24h'] > 0 else "📉" if md['change_24h'] < 0 else "➡️"
        
        return f"""
💰 **РЫНОЧНЫЕ ДАННЫЕ**
{change_emoji} Цена: ${md['price']:.6f}
📊 Изменение 24ч: {md['change_24h']:.2f}%
📈 Максимум 24ч: ${md['high_24h']:.6f}
📉 Минимум 24ч: ${md['low_24h']:.6f}
💎 Объем 24ч: ${md['volume_24h']:,.0f}"""
    
    def format_technical_indicators(self, data: Dict) -> str:
        """Форматирование технических индикаторов"""
        if not data.get('technical_indicators'):
            return "❌ Индикаторы недоступны"
        
        ti = data['technical_indicators']
        
        # Определяем сигналы
        rsi_signal = "🟢 Перепродан" if ti['rsi_14'] < 30 else "🔴 Перекуплен" if ti['rsi_14'] > 70 else "🟡 Нейтрально"
        
        macd_signal = "🟢 Бычий" if ti['macd']['histogram'] > 0 else "🔴 Медвежий"
        
        # Получаем текущую цену из рыночных данных
        current_price = data.get('market_data', {}).get('price', 0)
        
        # Проверяем структуру Bollinger Bands
        bollinger = ti.get('bollinger', {})
        if isinstance(bollinger, dict) and 'lower' in bollinger and 'upper' in bollinger:
            bb_position = "🟢 Нижняя полоса" if current_price <= bollinger['lower'] else "🔴 Верхняя полоса" if current_price >= bollinger['upper'] else "🟡 Центральная полоса"
        else:
            bb_position = "🟡 Центральная полоса"
        
        return f"""
📊 **ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ**
🔢 RSI (14): {ti['rsi_14']:.2f} {rsi_signal}
📈 SMA (20): ${ti['sma_20']:.6f}
📊 EMA (12): ${ti['ema_12']:.6f}
🎯 MACD: {macd_signal} (гистограмма: {ti['macd']['histogram']:.2f})
📏 Bollinger Bands: {bb_position}
📊 ATR (14): {ti['atr_14']:.6f}
📈 Volume SMA: {ti['volume_sma']:.2f}"""
    
    def format_news_data(self, data: Dict) -> str:
        """Форматирование новостных данных"""
        if not data.get('news_data'):
            return "❌ Новости недоступны"
        
        news = data['news_data']
        sentiment_emoji = {
            'positive': '🟢',
            'negative': '🔴', 
            'neutral': '🟡'
        }.get(news.get('social_sentiment', 'neutral'), '🟡')
        
        result = f"""
📰 **НОВОСТНОЙ АНАЛИЗ (Perplexity AI)**
{sentiment_emoji} Настроения: {news.get('social_sentiment', 'neutral').title()}
🎯 Влияние: {news.get('impact_score', 0):.2f}"""
        
        # Добавляем последние новости
        recent_news = news.get('recent_news', [])
        if recent_news:
            result += "\n\n📰 **ПОСЛЕДНИЕ НОВОСТИ:**"
            for i, news_item in enumerate(recent_news[:3], 1):
                impact_emoji = "🟢" if news_item.get('impact') == 'positive' else "🔴" if news_item.get('impact') == 'negative' else "🟡"
                result += f"\n{i}. {impact_emoji} {news_item.get('title', 'N/A')[:50]}..."
        
        return result
    
    def format_correlations(self, data: Dict) -> str:
        """Форматирование корреляций"""
        if not data.get('correlations'):
            return "❌ Корреляции недоступны"
        
        corr = data['correlations']
        
        # Определяем силу корреляции
        def get_correlation_strength(corr_value):
            if abs(corr_value) > 0.8:
                return "🔴 Сильная"
            elif abs(corr_value) > 0.5:
                return "🟡 Средняя"
            else:
                return "🟢 Слабая"
        
        return f"""
🔗 **КОРРЕЛЯЦИОННЫЙ АНАЛИЗ**
📊 BTC корреляция: {corr.get('correlation_btc', 0):.3f} {get_correlation_strength(corr.get('correlation_btc', 0))}
📈 ETH корреляция: {corr.get('correlation_eth', 0):.3f} {get_correlation_strength(corr.get('correlation_eth', 0))}
📊 Ранг волатильности: {corr.get('volatility_rank', 0)}
🎯 Сила корреляции: {corr.get('correlation_strength', 'neutral')}"""
    
    def format_orderbook(self, data: Dict) -> str:
        """Форматирование стакана заявок"""
        if not data.get('orderbook'):
            return "❌ Order Book недоступен"
        
        ob = data['orderbook']
        
        return f"""
📚 **СТАКАН ЗАЯВОК (Order Book)**
💰 Спред: ${ob['spread']:.6f} ({ob['spread_percent']:.2f}%)
📊 Bid объем: {ob['bid_volume']:.2f}
📈 Ask объем: {ob['ask_volume']:.2f}
⚖️ Соотношение: {ob['volume_ratio']:.2f}
💧 Ликвидность: {ob['liquidity_score']:.2f}"""
    
    def format_trade_history(self, data: Dict) -> str:
        """Форматирование истории сделок"""
        if not data.get('trade_history'):
            return "❌ История сделок недоступна"
        
        th = data['trade_history']
        
        return f"""
💱 **ИСТОРИЯ СДЕЛОК**
📊 Покупки: {th['buy_volume']:.2f}
📈 Продажи: {th['sell_volume']:.2f}
⚖️ Соотношение: {th['volume_ratio']:.2f}
📊 Средний размер: {th['avg_trade_size']:.2f}"""
    
    def create_comprehensive_report(self, symbol_data: Dict) -> str:
        """Создание комплексного отчета по символу"""
        symbol = symbol_data['symbol']
        
        report = f"""
🚀 **ПОЛНЫЙ АНАЛИЗ {symbol}** 🚀
{'='*50}

{self.format_market_data(symbol_data)}

{self.format_technical_indicators(symbol_data)}

{self.format_correlations(symbol_data)}

{self.format_orderbook(symbol_data)}

{self.format_trade_history(symbol_data)}

{self.format_news_data(symbol_data)}

⏰ Обновлено: {symbol_data['timestamp']}
{'='*50}"""
        
        return report
    
    async def send_telegram_message(self, message: str):
        """Отправка сообщения в Telegram"""
        try:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                print(f"✅ Сообщение отправлено в Telegram")
            else:
                print(f"❌ Ошибка отправки: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Ошибка Telegram: {e}")
    
    async def run_demo(self):
        """Запуск демонстрации"""
        print("🚀 ЗАПУСК ДЕМОНСТРАЦИИ МОЩИ ПРОЕКТА")
        print("=" * 60)
        
        # Запускаем менеджер данных
        print("🔌 Запуск менеджера данных...")
        await self.data_manager.start()
        
        # Подписываемся на символы
        print("📡 Подписка на символы...")
        await self.data_manager.subscribe_multiple_symbols(self.demo_symbols)
        
        # Ждем накопления данных
        print("⏳ Ожидание накопления данных (45 секунд)...")
        await asyncio.sleep(45)
        
        # Собираем данные по каждому символу
        all_reports = []
        
        for symbol in self.demo_symbols:
            print(f"🔍 Анализ {symbol}...")
            
            # Собираем данные
            symbol_data = await self.collect_comprehensive_data(symbol)
            
            # Создаем отчет
            report = self.create_comprehensive_report(symbol_data)
            all_reports.append(report)
            
            # Небольшая пауза между символами
            await asyncio.sleep(5)
        
        # Создаем общий заголовок
        header = f"""
🎯 **ДЕМОНСТРАЦИЯ МОЩИ MEXCAITRADE** 🎯
🤖 **ИИ + АЛГОРИТМИКА + REAL-TIME ДАННЫЕ**

📊 Проанализировано символов: {len(self.demo_symbols)}
🔍 Источники данных: MEX API + Perplexity AI + WebSocket
⏰ Время анализа: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*60}
"""
        
        # Отправляем в Telegram
        print("📤 Отправка отчетов в Telegram...")
        
        # Отправляем заголовок
        await self.send_telegram_message(header)
        await asyncio.sleep(2)
        
        # Отправляем отчеты по каждому символу
        for i, report in enumerate(all_reports, 1):
            print(f"📤 Отправка отчета {i}/{len(all_reports)}...")
            await self.send_telegram_message(report)
            await asyncio.sleep(3)  # Пауза между сообщениями
        
        # Отправляем итоговое сообщение
        footer = f"""
🏆 **ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА** 🏆

✅ Проанализировано: {len(self.demo_symbols)} символов
✅ Собраны данные: Рыночные + Технические + Новостные + Корреляции
✅ Источники: MEX API + Perplexity AI + WebSocket + PostgreSQL + Redis
✅ Время выполнения: {datetime.now().strftime('%H:%M:%S')}

🚀 **MEXCAITRADE - ПРОФЕССИОНАЛЬНАЯ ТОРГОВАЯ СИСТЕМА** 🚀

💡 Возможности системы:
• 📊 Real-time данные с MEX
• 🤖 ИИ анализ новостей через Perplexity
• 📈 Полный технический анализ
• 🔗 Корреляционный анализ
• 💾 Надежное хранение данных
• 📱 Telegram интеграция

🎯 Готово к торговле! 🎯
"""
        
        await self.send_telegram_message(footer)
        
        # Останавливаем менеджер
        await self.data_manager.stop()
        
        print("✅ Демонстрация завершена!")

async def main():
    """Главная функция"""
    demo = PowerDemoScript()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main()) 