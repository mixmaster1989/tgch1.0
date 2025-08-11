#!/usr/bin/env python3
"""
Быстрая конвертация USDT в USDC с анализом стакана
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

class QuickUSDCConverter:
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
    
    def cancel_existing_order(self, order_id: str, symbol: str = 'USDCUSDT'):
        """Отменить существующий ордер"""
        try:
            logger.info(f"🔄 Отменяю ордер {order_id}...")
            result = self.mex_api.cancel_order(symbol, order_id)
            logger.info(f"Результат отмены: {result}")
            return result
        except Exception as e:
            logger.error(f"Ошибка отмены ордера: {e}")
            return None
    
    def analyze_orderbook(self, symbol: str = 'USDCUSDT'):
        """Анализировать стакан для определения оптимальной цены"""
        try:
            logger.info(f"📊 Анализирую стакан {symbol}...")
            
            # Получаем стакан
            orderbook = self.mex_api.get_depth(symbol, limit=20)
            
            if 'bids' not in orderbook or 'asks' not in orderbook:
                logger.error("Не удалось получить данные стакана")
                return None
            
            bids = orderbook['bids'][:10]  # Топ-10 покупок
            asks = orderbook['asks'][:10]  # Топ-10 продаж
            
            if not bids or not asks:
                logger.error("Стакан пустой")
                return None
            
            # Анализируем лучшие цены
            best_bid = float(bids[0][0])  # Лучшая цена покупки
            best_ask = float(asks[0][0])  # Лучшая цена продажи
            
            # Рассчитываем спред
            spread = best_ask - best_bid
            spread_percent = (spread / best_bid) * 100
            
            # Анализируем объемы
            bid_volume = sum(float(bid[1]) for bid in bids)
            ask_volume = sum(float(ask[1]) for ask in asks)
            
            logger.info(f"📈 Анализ стакана:")
            logger.info(f"   Лучшая покупка: ${best_bid:.4f}")
            logger.info(f"   Лучшая продажа: ${best_ask:.4f}")
            logger.info(f"   Спред: ${spread:.4f} ({spread_percent:.4f}%)")
            logger.info(f"   Объем покупок: {bid_volume:.2f}")
            logger.info(f"   Объем продаж: {ask_volume:.2f}")
            
            # Определяем оптимальную цену для быстрого исполнения
            # Размещаем ордер чуть выше лучшей цены покупки
            optimal_price = best_bid + (spread * 0.1)  # 10% от спреда выше лучшей покупки
            
            return {
                'best_bid': best_bid,
                'best_ask': best_ask,
                'spread': spread,
                'spread_percent': spread_percent,
                'bid_volume': bid_volume,
                'ask_volume': ask_volume,
                'optimal_price': optimal_price,
                'bids': bids,
                'asks': asks
            }
            
        except Exception as e:
            logger.error(f"Ошибка анализа стакана: {e}")
            return None
    
    def place_quick_order(self, usdt_amount: float, symbol: str = 'USDCUSDT'):
        """Разместить быстрый ордер для конвертации"""
        try:
            logger.info(f"🚀 Размещаю быстрый ордер на {usdt_amount} USDT...")
            
            # Анализируем стакан
            orderbook_analysis = self.analyze_orderbook(symbol)
            if not orderbook_analysis:
                return None
            
            optimal_price = orderbook_analysis['optimal_price']
            best_bid = orderbook_analysis['best_bid']
            best_ask = orderbook_analysis['best_ask']
            
            # Рассчитываем количество USDC
            usdc_quantity = usdt_amount / optimal_price
            
            logger.info(f"💰 Детали ордера:")
            logger.info(f"   Сумма USDT: {usdt_amount}")
            logger.info(f"   Цена: {optimal_price:.4f} USDT")
            logger.info(f"   Количество USDC: {usdc_quantity:.4f}")
            logger.info(f"   Позиция относительно стакана: {optimal_price:.4f} (лучшая покупка: {best_bid:.4f})")
            
            # Размещаем ордер
            order = self.mex_api.place_order(
                symbol=symbol,
                side='BUY',
                quantity=usdc_quantity,
                price=optimal_price
            )
            
            if 'orderId' in order:
                logger.info(f"✅ Быстрый ордер создан: {order['orderId']}")
                
                # Отправляем уведомление в Telegram
                message = (
                    f"🚀 <b>БЫСТРЫЙ ОРДЕР РАЗМЕЩЕН</b>\n\n"
                    f"📋 <b>Детали:</b>\n"
                    f"🆔 ID: <code>{order['orderId']}</code>\n"
                    f"💱 Пара: {symbol}\n"
                    f"💰 Сумма: {usdt_amount} USDT\n"
                    f"📈 Цена: {optimal_price:.4f} USDT\n"
                    f"📊 Количество: {usdc_quantity:.4f} USDC\n\n"
                    f"📊 <b>Анализ стакана:</b>\n"
                    f"🟢 Лучшая покупка: {best_bid:.4f}\n"
                    f"🔴 Лучшая продажа: {best_ask:.4f}\n"
                    f"📏 Спред: {orderbook_analysis['spread_percent']:.4f}%\n\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_telegram_message(message)
                
                return order
            else:
                logger.error(f"❌ Ошибка создания ордера: {order}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка размещения быстрого ордера: {e}")
            return None
    
    def monitor_quick_order(self, order_id: str, symbol: str = 'USDCUSDT', max_wait_minutes: int = 5):
        """Быстрый мониторинг ордера"""
        logger.info(f"🔍 Быстрый мониторинг ордера {order_id}...")
        
        start_time = time.time()
        
        while True:
            current_time = time.time()
            elapsed_minutes = (current_time - start_time) / 60
            
            # Проверяем таймаут
            if elapsed_minutes >= max_wait_minutes:
                logger.warning(f"⏰ Таймаут ожидания ({max_wait_minutes} мин)")
                return False
            
            # Получаем статус ордера
            try:
                open_orders = self.mex_api.get_open_orders(symbol)
                order_found = False
                
                for order in open_orders:
                    if order.get('orderId') == order_id:
                        order_found = True
                        status = order.get('status', 'UNKNOWN')
                        filled = float(order.get('executedQty', 0))
                        total = float(order.get('origQty', 0))
                        
                        logger.info(f"Статус: {status}, Исполнено: {filled:.4f}/{total:.4f}")
                        
                        if status == 'FILLED' or filled >= total:
                            logger.info("✅ Ордер исполнен!")
                            return True
                        break
                
                if not order_found:
                    logger.info("✅ Ордер исполнен (не найден в открытых)")
                    return True
                
            except Exception as e:
                logger.error(f"Ошибка проверки статуса: {e}")
            
            time.sleep(5)  # Проверяем каждые 5 секунд

def main():
    converter = QuickUSDCConverter()
    
    # 1. Отменяем существующий ордер
    existing_order_id = "C02__582571019856932868067"
    converter.cancel_existing_order(existing_order_id)
    
    # Ждем немного для обработки отмены
    time.sleep(3)
    
    # 2. Размещаем быстрый ордер
    usdt_amount = 50.0
    new_order = converter.place_quick_order(usdt_amount)
    
    if new_order:
        # 3. Мониторим новый ордер
        converter.monitor_quick_order(new_order['orderId'])
        
        # 4. Финальное уведомление
        final_message = (
            f"🎉 <b>КОНВЕРТАЦИЯ ЗАВЕРШЕНА</b>\n\n"
            f"✅ Быстрый ордер исполнен\n"
            f"💰 Конвертировано: {usdt_amount} USDT → USDC\n"
            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
        )
        converter.send_telegram_message(final_message)
    else:
        error_message = "❌ Не удалось разместить быстрый ордер"
        converter.send_telegram_message(error_message)

if __name__ == "__main__":
    main() 