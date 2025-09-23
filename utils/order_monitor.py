#!/usr/bin/env python3
"""
Скрипт мониторинга ордера конвертации USDT в USDC с Telegram оповещениями
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

class OrderMonitor:
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
    
    def get_order_status(self, order_id: str, symbol: str = 'USDCUSDT'):
        """Получить статус ордера"""
        try:
            open_orders = self.mex_api.get_open_orders(symbol)
            
            for order in open_orders:
                if order.get('orderId') == order_id:
                    return {
                        'status': order.get('status', 'UNKNOWN'),
                        'filled': float(order.get('executedQty', 0)),
                        'total': float(order.get('origQty', 0)),
                        'price': order.get('price', 0),
                        'side': order.get('side', 'UNKNOWN'),
                        'type': order.get('type', 'UNKNOWN'),
                        'time': order.get('time', 0)
                    }
            
            # Если ордер не найден в открытых, значит он исполнен
            return {'status': 'FILLED', 'filled': 0, 'total': 0}
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса ордера: {e}")
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
    
    def cancel_order(self, order_id: str, symbol: str = 'USDCUSDT'):
        """Отменить ордер"""
        try:
            result = self.mex_api.cancel_order(symbol, order_id)
            logger.info(f"Результат отмены ордера: {result}")
            return result
        except Exception as e:
            logger.error(f"Ошибка отмены ордера: {e}")
            return None
    
    def monitor_order(self, order_id: str, symbol: str = 'USDCUSDT', max_wait_minutes: int = 30):
        """Мониторинг ордера с оповещениями"""
        logger.info(f"🔍 Начинаю мониторинг ордера {order_id}")
        
        # Отправляем начальное уведомление
        start_message = (
            f"🔄 <b>МОНИТОРИНГ ОРДЕРА ЗАПУЩЕН</b>\n\n"
            f"📋 <b>Детали ордера:</b>\n"
            f"🆔 ID: <code>{order_id}</code>\n"
            f"💱 Пара: {symbol}\n"
            f"⏰ Время запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
            f"⏳ Максимальное время ожидания: {max_wait_minutes} мин\n\n"
            f"📊 Оповещения будут приходить каждую минуту..."
        )
        self.send_telegram_message(start_message)
        
        start_time = time.time()
        last_notification_time = 0
        notification_interval = 60  # 60 секунд между уведомлениями
        
        while True:
            current_time = time.time()
            elapsed_minutes = (current_time - start_time) / 60
            
            # Проверяем, не истекло ли время ожидания
            if elapsed_minutes >= max_wait_minutes:
                timeout_message = (
                    f"⏰ <b>ВРЕМЯ ОЖИДАНИЯ ИСТЕКЛО</b>\n\n"
                    f"🆔 Ордер: <code>{order_id}</code>\n"
                    f"⏳ Прошло времени: {elapsed_minutes:.1f} мин\n"
                    f"❌ Максимальное время: {max_wait_minutes} мин\n\n"
                    f"🔄 Отменяю ордер..."
                )
                self.send_telegram_message(timeout_message)
                
                # Отменяем ордер
                cancel_result = self.cancel_order(order_id, symbol)
                if cancel_result:
                    cancel_message = f"✅ Ордер успешно отменен"
                else:
                    cancel_message = f"❌ Ошибка отмены ордера"
                
                self.send_telegram_message(cancel_message)
                break
            
            # Получаем статус ордера
            order_status = self.get_order_status(order_id, symbol)
            
            if order_status:
                status = order_status['status']
                filled = order_status['filled']
                total = order_status['total']
                fill_percentage = (filled / total * 100) if total > 0 else 0
                
                # Отправляем уведомление каждую минуту
                if current_time - last_notification_time >= notification_interval:
                    status_message = (
                        f"📊 <b>СТАТУС ОРДЕРА</b>\n\n"
                        f"🆔 ID: <code>{order_id}</code>\n"
                        f"📈 Статус: <b>{status}</b>\n"
                        f"✅ Исполнено: {filled:.4f} / {total:.4f}\n"
                        f"📊 Прогресс: {fill_percentage:.1f}%\n"
                        f"⏰ Прошло времени: {elapsed_minutes:.1f} мин\n"
                        f"🕐 Время: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    self.send_telegram_message(status_message)
                    last_notification_time = current_time
                
                # Проверяем, исполнен ли ордер
                if status == 'FILLED' or filled >= total:
                    # Получаем финальные балансы
                    usdt_balance, usdc_balance = self.get_balances()
                    
                    success_message = (
                        f"🎉 <b>ОРДЕР ИСПОЛНЕН!</b>\n\n"
                        f"🆔 ID: <code>{order_id}</code>\n"
                        f"✅ Статус: <b>{status}</b>\n"
                        f"💰 Исполнено: {filled:.4f} / {total:.4f}\n"
                        f"📊 Прогресс: 100%\n"
                        f"⏱️ Время исполнения: {elapsed_minutes:.1f} мин\n\n"
                        f"💰 <b>Финальные балансы:</b>\n"
                        f"💵 USDT: {usdt_balance:.4f}\n"
                        f"💵 USDC: {usdc_balance:.4f}\n\n"
                        f"🕐 Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                    )
                    self.send_telegram_message(success_message)
                    break
            
            # Ждем 10 секунд перед следующей проверкой
            time.sleep(10)

def main():
    # ID ордера из предыдущего запуска
    order_id = "C02__582571019856932868067"
    symbol = "USDCUSDT"
    max_wait_minutes = 30  # Максимальное время ожидания 30 минут
    
    monitor = OrderMonitor()
    monitor.monitor_order(order_id, symbol, max_wait_minutes)

if __name__ == "__main__":
    main() 