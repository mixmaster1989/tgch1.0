#!/usr/bin/env python3
"""
Упрощенный автоматический покупатель
Анализирует рынок и находит перспективные монеты для покупки при наличии свободных USDT
Без использования OpenRouter API
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from mex_api import MexAPI
from technical_indicators import TechnicalIndicators
from anti_hype_filter import AntiHypeFilter
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAutoPurchaser:
    """Упрощенный автоматический покупатель"""
    
    def __init__(self):
        self.mex_api = MexAPI()
        self.tech_indicators = TechnicalIndicators()
        self.anti_hype_filter = AntiHypeFilter()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Настройки
        self.min_usdt_balance = 10.0  # Минимальный баланс для покупки
        self.max_purchase_amount = 50.0  # Максимальная сумма одной покупки
        self.check_interval = 300  # Проверка каждые 5 минут
        self.min_purchase_interval = 600  # Минимум 10 минут между покупками
        
        # Статистика
        self.last_purchase_time = None
        self.total_purchases = 0
        self.total_spent = 0.0
        
        # Торговые пары для анализа
        self.trading_pairs = [
            'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
            'DOTUSDT', 'LINKUSDT', 'MATICUSDT', 'AVAXUSDT', 'UNIUSDT'
        ]
        
    def send_telegram_message(self, message: str):
        """Отправить сообщение в Telegram"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        try:
            response = requests.post(url, data=data)
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
            return None
    
    def get_usdt_balance(self) -> float:
        """Получить баланс USDT"""
        try:
            account_info = self.mex_api.get_account_info()
            for balance in account_info.get('balances', []):
                if balance['asset'] == 'USDT':
                    return float(balance['free'])
            return 0.0
        except Exception as e:
            logger.error(f"Ошибка получения баланса USDT: {e}")
            return 0.0
    
    def analyze_trading_pair(self, symbol: str) -> Optional[Dict]:
        """Анализ торговой пары"""
        try:
            logger.info(f"🔍 Анализ {symbol}...")
            
            # Получаем свечи (используем правильный интервал)
            klines = self.mex_api.get_klines(symbol, '1h', 24)
            if not klines or len(klines) < 20:
                logger.warning(f"Недостаточно данных для {symbol}")
                return None
            
            # Получаем текущую цену
            ticker = self.mex_api.get_ticker_price(symbol)
            if not ticker or 'price' not in ticker:
                return None
            
            current_price = float(ticker['price'])
            
            # Рассчитываем технические индикаторы
            indicators = self.tech_indicators.calculate_all_indicators(klines, symbol)
            if not indicators:
                return None
            
            # Проверяем анти-хайп фильтр
            filter_result = self.anti_hype_filter.check_buy_permission(symbol)
            
            # Рассчитываем скор
            score = 0
            reasons = []
            
            # RSI анализ
            rsi = indicators.get('rsi', 50)
            if rsi < 30:
                score += 3
                reasons.append("перепродано")
            elif rsi < 45:
                score += 2
                reasons.append("низкий_rsi")
            elif rsi > 70:
                score -= 2
                reasons.append("перекуплено")
            
            # Объем анализ
            volume_ratio = indicators.get('volume_ratio', 1.0)
            if volume_ratio > 1.5:
                score += 2
                reasons.append("высокий_объем")
            elif volume_ratio > 1.2:
                score += 1
                reasons.append("нормальный_объем")
            
            # MACD анализ
            macd_signal = indicators.get('macd_signal', 'NEUTRAL')
            if macd_signal == 'BUY':
                score += 2
                reasons.append("macd_buy")
            elif macd_signal == 'SELL':
                score -= 1
                reasons.append("macd_sell")
            
            # Bollinger Bands анализ
            bb_position = indicators.get('bb_position', 0.5)
            if bb_position < 0.2:
                score += 2
                reasons.append("bb_нижняя")
            elif bb_position > 0.8:
                score -= 1
                reasons.append("bb_верхняя")
            
            # Анти-хайп фильтр
            if not filter_result['allowed']:
                score = -10  # Блокируем покупку
                reasons.append(f"блокирован_{filter_result['reason']}")
            
            # Рассчитываем уверенность
            confidence = max(0.1, min(0.9, (score + 5) / 10))
            
            return {
                'symbol': symbol,
                'price': current_price,
                'score': score,
                'confidence': confidence,
                'reasons': reasons,
                'indicators': indicators,
                'filter_result': filter_result
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа {symbol}: {e}")
            return None
    
    def find_best_opportunities(self) -> List[Dict]:
        """Найти лучшие возможности для покупки"""
        try:
            logger.info("🔍 Поиск лучших возможностей...")
            
            opportunities = []
            
            for symbol in self.trading_pairs:
                analysis = self.analyze_trading_pair(symbol)
                if analysis and analysis['score'] > 0:  # Только положительные скоры
                    opportunities.append(analysis)
            
            # Сортируем по скору
            opportunities.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"✅ Найдено {len(opportunities)} перспективных монет")
            return opportunities[:3]  # Топ-3
            
        except Exception as e:
            logger.error(f"Ошибка поиска возможностей: {e}")
            return []
    
    def calculate_purchase_amount(self, available_usdt: float, opportunity: Dict) -> float:
        """Рассчитать сумму покупки"""
        try:
            # Адаптивная логика: при малом балансе используем больше средств
            if available_usdt < 20.0:
                # При балансе меньше $20 используем 60% средств
                base_amount = available_usdt * 0.6
            else:
                # При большем балансе используем 30% от баланса
                base_amount = min(available_usdt * 0.3, self.max_purchase_amount)
            
            # Корректируем на основе уверенности
            confidence_multiplier = opportunity['confidence']
            adjusted_amount = base_amount * confidence_multiplier
            
            # Применяем фильтр множитель
            filter_multiplier = opportunity['filter_result']['multiplier']
            final_amount = adjusted_amount * filter_multiplier
            
            # Ограничиваем максимальной суммой
            final_amount = min(final_amount, self.max_purchase_amount)
            
            # Обеспечиваем минимальную сумму $5
            if final_amount < 5.0 and available_usdt >= 5.0:
                final_amount = 5.0
            
            # Если все еще меньше $5, возвращаем 0
            if final_amount < 5.0:
                return 0.0
            
            return final_amount
            
        except Exception as e:
            logger.error(f"Ошибка расчета суммы покупки: {e}")
            return 0.0
    
    def execute_purchase(self, symbol: str, usdt_amount: float, opportunity: Dict) -> Dict:
        """Выполнить покупку"""
        try:
            logger.info(f"🛒 Покупка {symbol} на ${usdt_amount:.2f} USDT...")
            
            # Получаем текущую цену
            ticker = self.mex_api.get_ticker_price(symbol)
            if not ticker or 'price' not in ticker:
                return {'success': False, 'error': 'Не удалось получить цену'}
            
            current_price = float(ticker['price'])
            
            # Рассчитываем количество
            quantity = usdt_amount / current_price
            
            # Округляем количество (зависит от символа)
            if 'BTC' in symbol:
                quantity = round(quantity, 6)  # 6 знаков для BTC
            elif 'ETH' in symbol:
                quantity = round(quantity, 5)  # 5 знаков для ETH
            else:
                quantity = round(quantity, 4)  # 4 знака для остальных
            
            if quantity <= 0:
                return {'success': False, 'error': 'Количество слишком мало'}
            
            # Размещаем рыночный ордер
            order = self.mex_api.place_order(
                symbol=symbol,
                side='BUY',
                quantity=quantity,
                price=None  # Рыночный ордер
            )
            
            if 'orderId' in order:
                logger.info(f"✅ Ордер размещен: {order['orderId']}")
                
                # Отправляем уведомление
                message = (
                    f"🎯 <b>УМНАЯ ПОКУПКА ВЫПОЛНЕНА</b>\n\n"
                    f"📈 <b>{symbol}</b>\n"
                    f"💰 Сумма: ${usdt_amount:.2f} USDT\n"
                    f"📊 Количество: {quantity:.6f}\n"
                    f"💵 Цена: ${current_price:.6f}\n\n"
                    f"🎯 <b>АНАЛИЗ:</b>\n"
                    f"⭐ Уверенность: {opportunity['confidence']:.1%}\n"
                    f"📊 Скор: {opportunity['score']}\n"
                    f"🔍 Причины: {', '.join(opportunity['reasons'])}\n"
                    f"🛡️ Фильтр: {opportunity['filter_result']['reason']}\n\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_telegram_message(message)
                
                return {
                    'success': True,
                    'order_id': order['orderId'],
                    'symbol': symbol,
                    'quantity': quantity,
                    'price': current_price,
                    'amount': usdt_amount
                }
            else:
                error_msg = f"Ошибка создания ордера: {order}"
                logger.error(error_msg)
                return {'success': False, 'error': error_msg}
                
        except Exception as e:
            error_msg = f"Ошибка покупки {symbol}: {e}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    async def smart_purchase_cycle(self):
        """Цикл умных покупок"""
        try:
            # Проверяем баланс USDT
            usdt_balance = self.get_usdt_balance()
            logger.info(f"💰 Баланс USDT: ${usdt_balance:.2f}")
            
            if usdt_balance < self.min_usdt_balance:
                logger.info(f"❌ Недостаточно USDT: ${usdt_balance:.2f} < ${self.min_usdt_balance}")
                return
            
            # Проверяем время последней покупки
            if self.last_purchase_time:
                time_since_last = time.time() - self.last_purchase_time
                if time_since_last < self.min_purchase_interval:
                    remaining = self.min_purchase_interval - time_since_last
                    logger.info(f"⏰ Ждем {remaining:.0f} сек до следующей покупки")
                    return
            
            # Ищем лучшие возможности
            opportunities = self.find_best_opportunities()
            
            if not opportunities:
                logger.info("❌ Нет подходящих возможностей для покупки")
                return
            
            # Выбираем лучшую возможность
            best_opportunity = opportunities[0]
            symbol = best_opportunity['symbol']
            
            # Рассчитываем сумму покупки
            purchase_amount = self.calculate_purchase_amount(usdt_balance, best_opportunity)
            
            if purchase_amount <= 0:
                logger.info("❌ Сумма покупки слишком мала")
                return
            
            # Выполняем покупку
            result = self.execute_purchase(symbol, purchase_amount, best_opportunity)
            
            if result['success']:
                self.last_purchase_time = time.time()
                self.total_purchases += 1
                self.total_spent += purchase_amount
                
                logger.info(f"✅ Покупка выполнена: {symbol} на ${purchase_amount:.2f}")
                logger.info(f"📊 Статистика: {self.total_purchases} покупок, ${self.total_spent:.2f} потрачено")
            else:
                logger.error(f"❌ Ошибка покупки: {result['error']}")
                
        except Exception as e:
            logger.error(f"Ошибка цикла умных покупок: {e}")
    
    async def start_monitoring(self):
        """Запуск мониторинга"""
        logger.info("🚀 Запуск упрощенного автоматического покупателя...")
        logger.info(f"💰 Минимальный баланс: ${self.min_usdt_balance}")
        logger.info(f"💸 Максимальная покупка: ${self.max_purchase_amount}")
        logger.info(f"⏰ Проверка каждые {self.check_interval} сек")
        logger.info(f"📊 Анализируем пары: {', '.join(self.trading_pairs)}")
        
        # Отправляем уведомление о запуске
        startup_message = (
            f"🤖 <b>УПРОЩЕННЫЙ АВТОПОКУПАТЕЛЬ ЗАПУЩЕН</b>\n\n"
            f"💰 Минимальный баланс: ${self.min_usdt_balance}\n"
            f"💸 Максимальная покупка: ${self.max_purchase_amount}\n"
            f"⏰ Проверка каждые {self.check_interval} сек\n"
            f"🎯 Технический анализ + Анти-хайп фильтр\n"
            f"📊 Пары: {', '.join(self.trading_pairs)}\n\n"
            f"🔄 Мониторинг активен..."
        )
        self.send_telegram_message(startup_message)
        
        while True:
            try:
                await self.smart_purchase_cycle()
                await asyncio.sleep(self.check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Упрощенный покупатель остановлен")
                break
            except Exception as e:
                logger.error(f"❌ Критическая ошибка: {e}")
                await asyncio.sleep(60)  # Ждем минуту при ошибке

async def main():
    """Главная функция"""
    purchaser = SimpleAutoPurchaser()
    await purchaser.start_monitoring()

if __name__ == "__main__":
    asyncio.run(main()) 