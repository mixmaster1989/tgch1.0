#!/usr/bin/env python3
"""
Автоматический торговый бот MEXCAITRADE
Анализ рынка + Perplexity + DeepSeek + Автоторговля
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from decimal import Decimal
import json

# Импорты компонентов
from comprehensive_data_manager import ComprehensiveDataManager
from perplexity_analyzer import PerplexityAnalyzer
from mex_api import MexAPI
from technical_indicators import TechnicalIndicators
from correlation_analyzer import CorrelationAnalyzer

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AutoTrader:
    """Автоматический торговый бот"""
    
    def __init__(self):
        self.data_manager = ComprehensiveDataManager()
        self.perplexity = PerplexityAnalyzer()
        self.rest_api = MexAPI()
        self.technical_indicators = TechnicalIndicators()
        self.correlation_analyzer = CorrelationAnalyzer()
        
        # Настройки торговли
        self.symbol = "ETHUSDT"
        self.min_profit_percent = 0.5  # Минимальный профит 0.5%
        self.commission = 0.001  # Комиссия 0.1%
        self.min_lot_size = 0.001  # Минимальный лот ETH
        self.max_investment = 0.001  # Только минимальный лот!
        
        # Состояние
        self.is_running = False
        self.active_orders = {}
        self.trade_history = []
        
    async def start(self):
        """Запуск бота"""
        try:
            logger.info("🚀 Запуск автоматического торгового бота...")
            
            # Запускаем менеджер данных
            await self.data_manager.start()
            
            # Подписываемся на символы
            await self.data_manager.subscribe_multiple_symbols([self.symbol])
            
            self.is_running = True
            
            # Запускаем основной цикл
            await self.trading_loop()
            
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            await self.send_telegram_message(f"❌ Ошибка запуска бота: {e}")
    
    async def stop(self):
        """Остановка бота"""
        try:
            logger.info("🛑 Остановка торгового бота...")
            self.is_running = False
            await self.data_manager.stop()
            await self.send_telegram_message("🛑 Торговый бот остановлен")
        except Exception as e:
            logger.error(f"❌ Ошибка остановки бота: {e}")
    
    async def trading_loop(self):
        """Основной торговый цикл"""
        while self.is_running:
            try:
                logger.info("🔍 Анализ рынка для торговли...")
                
                # Получаем анализ рынка
                market_analysis = await self.analyze_market()
                
                # Получаем новости
                news_analysis = await self.get_news_analysis()
                
                # Отправляем анализ в Telegram
                from telegram_trading_bot import telegram_bot
                await telegram_bot.send_market_analysis(market_analysis)
                await telegram_bot.send_news_analysis(news_analysis)
                
                # Принимаем торговое решение
                decision = await self.make_trading_decision(market_analysis, news_analysis)
                
                if decision['action'] == 'BUY':
                    await self.execute_buy_order(decision)
                elif decision['action'] == 'SELL':
                    await self.execute_sell_order(decision)
                elif decision['action'] == 'HOLD':
                    logger.info("⏸️ Удерживаем позицию")
                
                # Ждем 5 минут перед следующим анализом
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"❌ Ошибка в торговом цикле: {e}")
                await asyncio.sleep(60)
    
    async def analyze_market(self) -> Dict:
        """Анализ рынка"""
        try:
            # Получаем рыночные данные
            market_data = self.data_manager.get_market_data(self.symbol)
            
            # Получаем технические индикаторы
            indicators = self.data_manager.get_technical_indicators(self.symbol, '1h')
            
            # Получаем корреляции
            correlations = self.data_manager.get_correlation_data(self.symbol)
            
            # Получаем ордербук
            orderbook = self.data_manager.get_orderbook_data(self.symbol)
            
            analysis = {
                'symbol': self.symbol,
                'price': market_data.price if market_data else 0,
                'change_24h': market_data.change_24h if market_data else 0,
                'volume_24h': market_data.volume_24h if market_data else 0,
                'indicators': indicators.to_dict() if indicators else {},
                'correlations': correlations,
                'orderbook': orderbook.to_dict() if orderbook else {},
                'timestamp': datetime.now()
            }
            
            # Логируем полученные данные
            logger.info(f"📊 ДАННЫЕ АНАЛИЗА:")
            logger.info(f"   Цена: ${analysis['price']:.2f}")
            logger.info(f"   Изменение 24ч: {analysis['change_24h']:.2f}%")
            logger.info(f"   Индикаторы: {len(analysis['indicators'])} параметров")
            logger.info(f"   Корреляции: {len(analysis['correlations'])} параметров")
            logger.info(f"   OrderBook: {len(analysis['orderbook'])} параметров")
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа рынка: {e}")
            return {}
    
    async def get_news_analysis(self) -> Dict:
        """Анализ новостей через Perplexity"""
        try:
            news_data = await self.perplexity.collect_coin_data(self.symbol)
            
            analysis = {
                'sentiment': news_data.get('social_sentiment', 'neutral'),
                'impact_score': news_data.get('impact_score', 0),
                'recent_news': news_data.get('recent_news', []),
                'timestamp': datetime.now()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Ошибка анализа новостей: {e}")
            return {'sentiment': 'neutral', 'impact_score': 0}
    
    async def make_trading_decision(self, market_analysis: Dict, news_analysis: Dict) -> Dict:
        """Принятие торгового решения"""
        try:
            decision = {
                'action': 'HOLD',
                'reason': 'Нет четких сигналов',
                'confidence': 0.0,
                'price': 0.0,
                'quantity': 0.0
            }
            
            if not market_analysis:
                return decision
            
            price = market_analysis.get('price', 0)
            if price == 0:
                return decision
            
            # Анализируем технические индикаторы
            indicators = market_analysis.get('indicators', {})
            rsi = indicators.get('rsi_14', 50)
            macd_histogram = indicators.get('macd', {}).get('histogram', 0)
            
            # Анализируем новости
            sentiment = news_analysis.get('sentiment', 'neutral')
            impact_score = news_analysis.get('impact_score', 0)
            
            # Анализируем ордербук
            orderbook = market_analysis.get('orderbook', {})
            spread_percent = orderbook.get('spread_percent', 0)
            
            # Логика принятия решений
            buy_signals = 0
            sell_signals = 0
            
            # RSI сигналы
            if rsi < 30:
                buy_signals += 1
            elif rsi > 70:
                sell_signals += 1
            
            # MACD сигналы
            if macd_histogram > 0:
                buy_signals += 1
            elif macd_histogram < 0:
                sell_signals += 1
            
            # Новостные сигналы
            if sentiment == 'positive' and impact_score > 0.3:
                buy_signals += 1
            elif sentiment == 'negative' and impact_score > 0.3:
                sell_signals += 1
            
            # Спред сигналы
            if spread_percent < 0.1:  # Низкий спред - хорошая ликвидность
                buy_signals += 0.5
            
            # Логируем сигналы для отладки
            logger.info(f"📊 СИГНАЛЫ АНАЛИЗА:")
            logger.info(f"   RSI: {rsi:.1f} (покупка: {rsi < 30}, продажа: {rsi > 70})")
            logger.info(f"   MACD: {macd_histogram:.4f} (покупка: {macd_histogram > 0}, продажа: {macd_histogram < 0})")
            logger.info(f"   Новости: {sentiment} (влияние: {impact_score:.2f})")
            logger.info(f"   Спред: {spread_percent:.4f}% (покупка: {spread_percent < 0.1})")
            logger.info(f"   Покупка сигналов: {buy_signals}")
            logger.info(f"   Продажа сигналов: {sell_signals}")
            logger.info(f"   Активный ордер покупки: {self.has_active_buy_order()}")
            
            # Принимаем решение
            if buy_signals >= 1.5 and not self.has_active_buy_order():
                decision = {
                    'action': 'BUY',
                    'reason': f'Покупка: RSI={rsi:.1f}, MACD={macd_histogram:.4f}, Новости={sentiment}',
                    'confidence': min(buy_signals / 3, 1.0),
                    'price': price * 0.999,  # Покупаем чуть ниже рынка
                    'quantity': self.calculate_quantity(price)
                }
                logger.info(f"🚀 РЕШЕНИЕ: ПОКУПКА! Причина: {decision['reason']}")
            elif sell_signals >= 2 and self.has_active_buy_order():
                decision = {
                    'action': 'SELL',
                    'reason': f'Продажа: RSI={rsi:.1f}, MACD={macd_histogram:.4f}, Новости={sentiment}',
                    'confidence': min(sell_signals / 3, 1.0),
                    'price': price * 1.005,  # Продаем с профитом 0.5%
                    'quantity': self.get_bought_quantity()
                }
                logger.info(f"📉 РЕШЕНИЕ: ПРОДАЖА! Причина: {decision['reason']}")
            else:
                logger.info(f"⏸️ РЕШЕНИЕ: УДЕРЖАНИЕ (покупка: {buy_signals}/2, продажа: {sell_signals}/2)")
            
            return decision
            
        except Exception as e:
            logger.error(f"❌ Ошибка принятия решения: {e}")
            return {'action': 'HOLD', 'reason': f'Ошибка: {e}', 'confidence': 0.0}
    
    def calculate_quantity(self, price: float) -> float:
        """Расчет количества для покупки"""
        try:
            # Только минимальный лот!
            quantity = self.min_lot_size
            
            # Округляем до 3 знаков
            return round(quantity, 3)
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета количества: {e}")
            return self.min_lot_size
    
    def has_active_buy_order(self) -> bool:
        """Проверка активного ордера на покупку"""
        return any(order['side'] == 'BUY' and order['status'] == 'NEW' 
                  for order in self.active_orders.values())
    
    def get_bought_quantity(self) -> float:
        """Получение количества купленного ETH"""
        # Здесь должна быть логика получения реальных позиций
        # Пока возвращаем минимальный лот
        return self.min_lot_size
    
    async def execute_buy_order(self, decision: Dict):
        """Выполнение ордера на покупку"""
        try:
            logger.info(f"📈 Создание ордера на покупку: {decision['reason']}")
            
            # Создаем лимитный ордер
            order = await self.create_limit_order(
                symbol=self.symbol,
                side='BUY',
                quantity=decision['quantity'],
                price=decision['price']
            )
            
            if order:
                self.active_orders[order['orderId']] = {
                    'orderId': order['orderId'],
                    'symbol': self.symbol,
                    'side': 'BUY',
                    'quantity': decision['quantity'],
                    'price': decision['price'],
                    'status': 'NEW',
                    'timestamp': datetime.now()
                }
                
                # Отправляем решение в Telegram
                from telegram_trading_bot import telegram_bot
                await telegram_bot.send_trading_decision(decision)
                await telegram_bot.send_order_created(order)
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания ордера на покупку: {e}")
            await self.send_telegram_message(f"❌ Ошибка покупки: {e}")
    
    async def execute_sell_order(self, decision: Dict):
        """Выполнение ордера на продажу"""
        try:
            logger.info(f"📉 Создание ордера на продажу: {decision['reason']}")
            
            # Создаем лимитный ордер
            order = await self.create_limit_order(
                symbol=self.symbol,
                side='SELL',
                quantity=decision['quantity'],
                price=decision['price']
            )
            
            if order:
                self.active_orders[order['orderId']] = {
                    'orderId': order['orderId'],
                    'symbol': self.symbol,
                    'side': 'SELL',
                    'quantity': decision['quantity'],
                    'price': decision['price'],
                    'status': 'NEW',
                    'timestamp': datetime.now()
                }
                
                # Отправляем решение в Telegram
                from telegram_trading_bot import telegram_bot
                await telegram_bot.send_trading_decision(decision)
                await telegram_bot.send_order_created(order)
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания ордера на продажу: {e}")
            await self.send_telegram_message(f"❌ Ошибка продажи: {e}")
    
    async def create_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Optional[Dict]:
        """Создание лимитного ордера"""
        try:
            # РЕАЛЬНЫЙ ВЫЗОВ MEXC API
            order = self.rest_api.place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price
            )
            
            if order and 'orderId' in order:
                logger.info(f"✅ РЕАЛЬНЫЙ ордер создан: {order}")
                return order
            else:
                logger.error(f"❌ Ошибка API: {order}")
                return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка создания ордера: {e}")
            return None
    
    async def send_telegram_message(self, message: str):
        """Отправка сообщения в Telegram"""
        try:
            from telegram_trading_bot import telegram_bot
            await telegram_bot.send_message(message)
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки в Telegram: {e}")
            # Fallback - выводим в консоль
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"📱 [{timestamp}] {message}")

async def main():
    """Главная функция"""
    trader = AutoTrader()
    
    try:
        await trader.start()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
        await trader.stop()
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        await trader.stop()

if __name__ == "__main__":
    asyncio.run(main()) 