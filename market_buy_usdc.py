#!/usr/bin/env python3
"""
Рыночная покупка USDC за 50 USDT
"""

from mex_api import MexAPI
import time
import logging
import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketUSDCBuyer:
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
    
    def cancel_order(self, order_id: str, symbol: str = 'USDCUSDT'):
        """Отменить ордер"""
        try:
            logger.info(f"🔄 Отменяю лимитный ордер {order_id}...")
            result = self.mex_api.cancel_order(symbol, order_id)
            logger.info(f"Результат отмены: {result}")
            return result
        except Exception as e:
            logger.error(f"Ошибка отмены ордера: {e}")
            return None
    
    def get_current_price(self, symbol: str = 'USDCUSDT'):
        """Получить текущую рыночную цену"""
        try:
            price_info = self.mex_api.get_ticker_price(symbol)
            if 'price' in price_info:
                return float(price_info['price'])
            return None
        except Exception as e:
            logger.error(f"Ошибка получения цены: {e}")
            return None
    
    def market_buy_usdc(self, usdt_amount: float, symbol: str = 'USDCUSDT'):
        """Рыночная покупка USDC за USDT"""
        try:
            logger.info(f"🚀 Рыночная покупка USDC на {usdt_amount} USDT...")
            
            # Получаем текущую цену для расчета количества
            current_price = self.get_current_price(symbol)
            if not current_price:
                logger.error("Не удалось получить текущую цену")
                return None
            
            # Рассчитываем примерное количество USDC и округляем до 2 знаков
            estimated_usdc = usdt_amount / current_price
            rounded_usdc = round(estimated_usdc, 2)  # Округляем до 2 знаков после запятой
            
            logger.info(f"💰 Детали рыночной покупки:")
            logger.info(f"   Сумма USDT: {usdt_amount}")
            logger.info(f"   Текущая цена: {current_price:.4f} USDT")
            logger.info(f"   Примерное количество USDC: {estimated_usdc:.4f}")
            logger.info(f"   Округленное количество USDC: {rounded_usdc:.2f}")
            
            # Размещаем рыночный ордер
            order = self.mex_api.place_order(
                symbol=symbol,
                side='BUY',
                quantity=rounded_usdc,
                price=None  # None = рыночный ордер
            )
            
            if 'orderId' in order:
                logger.info(f"✅ Рыночный ордер создан: {order['orderId']}")
                
                # Отправляем уведомление в Telegram
                message = (
                    f"🚀 <b>РЫНОЧНЫЙ ОРДЕР РАЗМЕЩЕН</b>\n\n"
                    f"📋 <b>Детали:</b>\n"
                    f"🆔 ID: <code>{order['orderId']}</code>\n"
                    f"💱 Пара: {symbol}\n"
                    f"💰 Сумма: {usdt_amount} USDT\n"
                    f"📈 Тип: РЫНОЧНЫЙ\n"
                    f"📊 Количество: {rounded_usdc:.2f} USDC\n"
                    f"💵 Текущая цена: {current_price:.4f} USDT\n\n"
                    f"⚡ Исполнение: МГНОВЕННОЕ\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_telegram_message(message)
                
                return order
            else:
                logger.error(f"❌ Ошибка создания рыночного ордера: {order}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка рыночной покупки: {e}")
            return None
    
    def get_balances(self):
        """Получить текущие балансы"""
        try:
            account_info = self.mex_api.get_account_info()
            usdt_balance = 0
            usdc_balance = 0
            
            for balance in account_info.get('balances', []):
                if balance['asset'] == 'USDT':
                    usdt_balance = float(balance['free'])
                elif balance['asset'] == 'USDC':
                    usdc_balance = float(balance['free'])
            
            return usdt_balance, usdc_balance
            
        except Exception as e:
            logger.error(f"Ошибка получения балансов: {e}")
            return 0, 0

def main():
    buyer = MarketUSDCBuyer()
    
    # Показываем начальные балансы
    usdt_balance, usdc_balance = buyer.get_balances()
    logger.info(f"💰 Начальные балансы:")
    logger.info(f"   USDT: {usdt_balance:.4f}")
    logger.info(f"   USDC: {usdc_balance:.4f}")
    
    # 1. Отменяем лимитный ордер
    limit_order_id = "C02__582575249619558402067"
    buyer.cancel_order(limit_order_id)
    
    # Ждем немного для обработки отмены
    time.sleep(3)
    
    # 2. Рыночная покупка USDC за 50 USDT
    usdt_amount = 50.0
    market_order = buyer.market_buy_usdc(usdt_amount)
    
    if market_order:
        logger.info(f"✅ Рыночный ордер размещен: {market_order['orderId']}")
        
        # Ждем немного и показываем финальные балансы
        time.sleep(5)
        final_usdt, final_usdc = buyer.get_balances()
        
        final_message = (
            f"🎉 <b>РЫНОЧНАЯ ПОКУПКА ЗАВЕРШЕНА</b>\n\n"
            f"✅ Рыночный ордер исполнен\n"
            f"💰 Конвертировано: {usdt_amount} USDT → USDC\n\n"
            f"💰 <b>Финальные балансы:</b>\n"
            f"💵 USDT: {final_usdt:.4f}\n"
            f"💵 USDC: {final_usdc:.4f}\n\n"
            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        buyer.send_telegram_message(final_message)
        
        logger.info(f"💰 Финальные балансы:")
        logger.info(f"   USDT: {final_usdt:.4f}")
        logger.info(f"   USDC: {final_usdc:.4f}")
    else:
        error_message = "❌ Не удалось разместить рыночный ордер"
        buyer.send_telegram_message(error_message)

if __name__ == "__main__":
    main() 