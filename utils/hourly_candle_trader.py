#!/usr/bin/env python3
"""
Торговля на основе часовых свечей
Покупает BTC и ETH по цене на 10% выше минимальной за прошедший час
"""

from mex_api import MexAPI
import time
import logging
import requests
from datetime import datetime, timedelta
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HourlyCandleTrader:
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
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
    
    def get_hourly_candle(self, symbol: str):
        """Получить часовую свечу для символа"""
        try:
            logger.info(f"📊 Получаю часовую свечу для {symbol}...")
            
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
            
            logger.info(f"📈 Свеча {symbol}:")
            logger.info(f"   Открытие: ${candle_data['open']:.4f}")
            logger.info(f"   Максимум: ${candle_data['high']:.4f}")
            logger.info(f"   Минимум: ${candle_data['low']:.4f}")
            logger.info(f"   Закрытие: ${candle_data['close']:.4f}")
            logger.info(f"   Объем: {candle_data['volume']:.2f}")
            
            return candle_data
            
        except Exception as e:
            logger.error(f"Ошибка получения свечи {symbol}: {e}")
            return None
    
    def calculate_limit_price(self, symbol: str, candle_data: dict):
        """Рассчитать лимитную цену на 10% выше минимальной"""
        try:
            min_price = candle_data['low']
            limit_price = min_price * 1.10  # 10% выше минимальной
            
            logger.info(f"🎯 Расчет лимитной цены для {symbol}:")
            logger.info(f"   Минимальная цена за час: ${min_price:.4f}")
            logger.info(f"   Лимитная цена (+10%): ${limit_price:.4f}")
            logger.info(f"   Разница: ${limit_price - min_price:.4f} ({((limit_price/min_price - 1) * 100):.2f}%)")
            
            return limit_price
            
        except Exception as e:
            logger.error(f"Ошибка расчета лимитной цены: {e}")
            return None
    
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
    
    def place_limit_order(self, symbol: str, usdc_amount: float, limit_price: float):
        """Разместить лимитный ордер"""
        try:
            # Рассчитываем количество монет
            quantity = usdc_amount / limit_price
            
            # Округляем количество до 4 знаков
            quantity = round(quantity, 4)
            
            logger.info(f"🚀 Размещаю лимитный ордер:")
            logger.info(f"   Символ: {symbol}")
            logger.info(f"   Сумма USDC: {usdc_amount}")
            logger.info(f"   Цена: ${limit_price:.4f}")
            logger.info(f"   Количество: {quantity}")
            
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
    
    def trade_based_on_hourly_candle(self, usdc_amount_per_coin: float = 25.0):
        """Торговля на основе часовых свечей"""
        try:
            logger.info(f"🔄 Начинаю торговлю на основе часовых свечей...")
            
            # Получаем баланс USDC
            usdc_balance = self.get_usdc_balance()
            logger.info(f"💰 Баланс USDC: {usdc_balance:.2f}")
            
            if usdc_balance < usdc_amount_per_coin * 2:
                logger.error(f"Недостаточно USDC. Нужно: {usdc_amount_per_coin * 2}, доступно: {usdc_balance}")
                return
            
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
                
                # Рассчитываем лимитную цену
                limit_price = self.calculate_limit_price(symbol, candle_data)
                if not limit_price:
                    continue
                
                # Размещаем лимитный ордер
                order = self.place_limit_order(symbol, usdc_amount_per_coin, limit_price)
                if order:
                    logger.info(f"✅ Ордер для {symbol} размещен успешно")
                else:
                    logger.error(f"❌ Не удалось разместить ордер для {symbol}")
                
                # Пауза между ордерами
                time.sleep(2)
            
            logger.info(f"\n🎉 Торговля на основе часовых свечей завершена!")
            
        except Exception as e:
            logger.error(f"❌ Ошибка торговли: {e}")

def main():
    trader = HourlyCandleTrader()
    
    # Запускаем торговлю на основе часовых свечей
    # 25 USDC на каждую монету (BTC и ETH)
    trader.trade_based_on_hourly_candle(usdc_amount_per_coin=25.0)

if __name__ == "__main__":
    main() 