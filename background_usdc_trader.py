#!/usr/bin/env python3
"""
Фоновая торговля BTC и ETH за USDC
Лимитные ордера на 10% выше минимальной цены за час
"""

from mex_api import MexAPI
import time
import logging
import requests
import asyncio
import threading
from datetime import datetime, timedelta
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundUSDCTrader:
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.is_running = False
        self.last_trade_time = None
        self.trade_interval = 3600  # 1 час между торговыми сессиями
        
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
    
    def cancel_all_usdt_orders(self):
        """Отменить все USDT ордера"""
        try:
            logger.info("🔄 Отменяю все USDT ордера...")
            
            # Отменяем ордера для USDT пар
            usdt_pairs = ['BTCUSDT', 'ETHUSDT', 'USDCUSDT']
            
            for pair in usdt_pairs:
                try:
                    open_orders = self.mex_api.get_open_orders(pair)
                    if open_orders:
                        for order in open_orders:
                            order_id = order.get('orderId')
                            if order_id:
                                result = self.mex_api.cancel_order(pair, order_id)
                                logger.info(f"Отменен ордер {order_id} для {pair}: {result}")
                except Exception as e:
                    logger.error(f"Ошибка отмены ордеров для {pair}: {e}")
            
            logger.info("✅ Все USDT ордера отменены")
            
        except Exception as e:
            logger.error(f"Ошибка отмены USDT ордеров: {e}")
    
    def get_hourly_candle(self, symbol: str):
        """Получить часовую свечу для символа"""
        try:
            # Получаем часовые свечи за последний час
            klines = self.mex_api.get_klines(symbol, '60m', 1)
            
            if not klines or len(klines) == 0:
                logger.error(f"Не удалось получить свечи для {symbol}")
                return None
            
            # Структура свечи: [timestamp, open, high, low, close, volume, ...]
            candle = klines[0]
            
            candle_data = {
                'timestamp': int(candle[0]),
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4]),
                'volume': float(candle[5])
            }
            
            return candle_data
            
        except Exception as e:
            logger.error(f"Ошибка получения свечи {symbol}: {e}")
            return None
    
    def calculate_limit_price(self, symbol: str, candle_data: dict):
        """Рассчитать лимитную цену на 10% выше минимальной"""
        try:
            min_price = candle_data['low']
            limit_price = min_price * 1.10  # 10% выше минимальной
            
            return limit_price, min_price
            
        except Exception as e:
            logger.error(f"Ошибка расчета лимитной цены: {e}")
            return None, None
    
    def get_usdc_balance(self):
        """Получить баланс USDC"""
        try:
            account_info = self.mex_api.get_account_info()
            for balance in account_info.get('balances', []):
                if balance['asset'] == 'USDC':
                    return float(balance['free'])
            return 0.0
        except Exception as e:
            logger.error(f"Ошибка получения баланса USDC: {e}")
            return 0.0
    
    def place_limit_order(self, symbol: str, usdc_amount: float, limit_price: float, candle_data: dict):
        """Разместить лимитный ордер"""
        try:
            # Рассчитываем количество монет
            quantity = usdc_amount / limit_price
            
            # Округляем количество до 4 знаков
            quantity = round(quantity, 4)
            
            # Размещаем ордер
            order = self.mex_api.place_order(
                symbol=symbol,
                side='BUY',
                quantity=quantity,
                price=limit_price
            )
            
            if 'orderId' in order:
                logger.info(f"✅ Лимитный ордер создан: {order['orderId']}")
                
                # Отправляем уведомление в Telegram
                message = (
                    f"🎯 <b>ЛИМИТНЫЙ ОРДЕР РАЗМЕЩЕН</b>\n\n"
                    f"📋 <b>Детали:</b>\n"
                    f"🆔 ID: <code>{order['orderId']}</code>\n"
                    f"💱 Пара: {symbol}\n"
                    f"💰 Сумма: {usdc_amount} USDC\n"
                    f"📈 Цена: ${limit_price:.4f}\n"
                    f"📊 Количество: {quantity}\n\n"
                    f"📊 <b>Анализ свечи:</b>\n"
                    f"📉 Минимум за час: ${candle_data['low']:.4f}\n"
                    f"📈 Максимум за час: ${candle_data['high']:.4f}\n"
                    f"📊 Закрытие: ${candle_data['close']:.4f}\n"
                    f"📏 Премия: +10%\n\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_telegram_message(message)
                
                return order
            else:
                logger.error(f"❌ Ошибка создания ордера: {order}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка размещения ордера: {e}")
            return None
    
    def execute_trading_session(self):
        """Выполнить торговую сессию"""
        try:
            logger.info(f"🔄 Начинаю торговую сессию...")
            
            # Получаем баланс USDC
            usdc_balance = self.get_usdc_balance()
            logger.info(f"💰 Баланс USDC: {usdc_balance:.2f}")
            
            if usdc_balance < 10:
                logger.warning(f"Недостаточно USDC: {usdc_balance}")
                return
            
            # Распределяем средства: 50% на BTC, 50% на ETH
            usdc_per_coin = usdc_balance * 0.45  # 45% на каждую монету, 10% резерв
            
            # Торговые пары
            symbols = ['BTCUSDC', 'ETHUSDC']
            
            for symbol in symbols:
                logger.info(f"\n{'='*50}")
                logger.info(f"📊 Анализ {symbol}")
                logger.info(f"{'='*50}")
                
                # Получаем часовую свечу
                candle_data = self.get_hourly_candle(symbol)
                if not candle_data:
                    continue
                
                logger.info(f"📈 Свеча {symbol}:")
                logger.info(f"   Открытие: ${candle_data['open']:.4f}")
                logger.info(f"   Максимум: ${candle_data['high']:.4f}")
                logger.info(f"   Минимум: ${candle_data['low']:.4f}")
                logger.info(f"   Закрытие: ${candle_data['close']:.4f}")
                
                # Рассчитываем лимитную цену
                limit_price, min_price = self.calculate_limit_price(symbol, candle_data)
                if not limit_price:
                    continue
                
                logger.info(f"🎯 Расчет лимитной цены для {symbol}:")
                logger.info(f"   Минимальная цена за час: ${min_price:.4f}")
                logger.info(f"   Лимитная цена (+10%): ${limit_price:.4f}")
                logger.info(f"   Разница: ${limit_price - min_price:.4f} ({((limit_price/min_price - 1) * 100):.2f}%)")
                
                # Размещаем лимитный ордер
                order = self.place_limit_order(symbol, usdc_per_coin, limit_price, candle_data)
                if order:
                    logger.info(f"✅ Ордер для {symbol} размещен успешно")
                else:
                    logger.error(f"❌ Не удалось разместить ордер для {symbol}")
                
                # Пауза между ордерами
                time.sleep(2)
            
            self.last_trade_time = time.time()
            logger.info(f"\n🎉 Торговая сессия завершена!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка торговой сессии: {e}")
    
    def start_background_trading(self):
        """Запустить фоновую торговлю"""
        try:
            logger.info("🚀 Запуск фоновой торговли BTC/ETH за USDC...")
            
            # Отправляем уведомление о запуске
            start_message = (
                f"🤖 <b>ФОНОВАЯ ТОРГОВЛЯ ЗАПУЩЕНА</b>\n\n"
                f"📊 <b>Стратегия:</b>\n"
                f"💱 Пара: BTCUSDC / ETHUSDC\n"
                f"💰 Валюта: USDC\n"
                f"📈 Тип ордера: Лимитный\n"
                f"📏 Цена: +10% от минимальной за час\n"
                f"⏰ Интервал: Каждый час\n\n"
                f"🔄 Отменяю старые USDT ордера...\n"
                f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
            )
            self.send_telegram_message(start_message)
            
            # Отменяем все USDT ордера
            self.cancel_all_usdt_orders()
            
            self.is_running = True
            
            while self.is_running:
                try:
                    current_time = time.time()
                    
                    # Проверяем, прошло ли достаточно времени с последней торговли
                    if (self.last_trade_time is None or 
                        current_time - self.last_trade_time >= self.trade_interval):
                        
                        logger.info(f"⏰ Выполняю торговую сессию...")
                        self.execute_trading_session()
                    
                    # Ждем 5 минут перед следующей проверкой
                    time.sleep(300)
                    
                except KeyboardInterrupt:
                    logger.info("🛑 Торговля остановлена пользователем")
                    break
                except Exception as e:
                    logger.error(f"❌ Ошибка в цикле торговли: {e}")
                    time.sleep(60)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            # Отправляем уведомление об остановке
            stop_message = (
                f"🛑 <b>ФОНОВАЯ ТОРГОВЛЯ ОСТАНОВЛЕНА</b>\n\n"
                f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
            )
            self.send_telegram_message(stop_message)
    
    def stop_trading(self):
        """Остановить торговлю"""
        self.is_running = False
        logger.info("🛑 Остановка торговли...")

def main():
    trader = BackgroundUSDCTrader()
    
    try:
        # Запускаем фоновую торговлю
        trader.start_background_trading()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
        trader.stop_trading()

if __name__ == "__main__":
    main() 