#!/usr/bin/env python3
"""
Автоматический балансировщик USDT/USDC
Выравнивает балансы стейблкоинов каждый час
"""

import time
import logging
from datetime import datetime
from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StablecoinBalancer:
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.check_interval = 3600  # 1 час
        self.min_balance_diff = 10.0  # Минимальная разница для балансировки
        self.last_balance_time = 0
        
    def send_telegram_message(self, message: str):
        """Отправить сообщение в Telegram"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {'chat_id': self.chat_id, 'text': message, 'parse_mode': 'HTML'}
        try:
            requests.post(url, data=data)
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
    
    def get_stablecoin_balances(self):
        """Получить балансы USDT и USDC"""
        try:
            account_info = self.mex_api.get_account_info()
            balances = {'USDT': 0.0, 'USDC': 0.0}
            
            for balance in account_info.get('balances', []):
                asset = balance['asset']
                if asset in ['USDT', 'USDC']:
                    balances[asset] = float(balance['free'])
            
            return balances
        except Exception as e:
            logger.error(f"Ошибка получения балансов: {e}")
            return {'USDT': 0.0, 'USDC': 0.0}
    
    def calculate_rebalance(self, usdt_balance, usdc_balance):
        """Рассчитать необходимую балансировку"""
        total = usdt_balance + usdc_balance
        target_each = total / 2
        
        usdt_diff = usdt_balance - target_each
        usdc_diff = usdc_balance - target_each
        
        # Определяем направление конвертации
        if abs(usdt_diff) < self.min_balance_diff:
            return None  # Балансировка не нужна
        
        if usdt_diff > 0:
            # USDT больше - конвертируем в USDC
            return {
                'from': 'USDT',
                'to': 'USDC', 
                'amount': abs(usdt_diff),
                'symbol': 'USDCUSDT',
                'side': 'BUY'  # Покупаем USDC за USDT
            }
        else:
            # USDC больше - конвертируем в USDT
            return {
                'from': 'USDC',
                'to': 'USDT',
                'amount': abs(usdc_diff),
                'symbol': 'USDCUSDT', 
                'side': 'SELL'  # Продаем USDC за USDT
            }
    
    def execute_conversion(self, conversion):
        """Выполнить конвертацию стейблкоинов"""
        try:
            symbol = conversion['symbol']
            side = conversion['side']
            amount = conversion['amount']
            
            # Получаем текущую цену
            ticker = self.mex_api.get_ticker_price(symbol)
            if not ticker or 'price' not in ticker:
                return {'success': False, 'error': 'Не удалось получить цену'}
            
            price = float(ticker['price'])
            
            # Рассчитываем количество
            if side == 'BUY':
                # Покупаем USDC за USDT
                quantity = amount / price
            else:
                # Продаем USDC за USDT
                quantity = amount
            
            # Округляем до 2 знаков для стейблкоинов
            quantity = round(quantity, 2)
            
            # Размещаем маркет ордер для быстрого исполнения
            order = self.mex_api.place_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity
            )
            
            if order and 'orderId' in order:
                return {
                    'success': True,
                    'order_id': order['orderId'],
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': price,
                    'amount': amount
                }
            else:
                return {'success': False, 'error': f'API ошибка: {order}'}
                
        except Exception as e:
            logger.error(f"Ошибка конвертации: {e}")
            return {'success': False, 'error': str(e)}
    
    def check_and_balance(self):
        """Проверить и выполнить балансировку"""
        try:
            current_time = time.time()
            
            # Проверяем интервал
            if current_time - self.last_balance_time < self.check_interval:
                return
            
            self.last_balance_time = current_time
            
            # Получаем балансы
            balances = self.get_stablecoin_balances()
            usdt_balance = balances['USDT']
            usdc_balance = balances['USDC']
            total_balance = usdt_balance + usdc_balance
            
            logger.info(f"💰 Балансы: USDT=${usdt_balance:.2f}, USDC=${usdc_balance:.2f}")
            
            # Проверяем минимальную сумму
            if total_balance < 20.0:
                logger.info("Общий баланс стейблов слишком мал для балансировки")
                return
            
            # Рассчитываем балансировку
            conversion = self.calculate_rebalance(usdt_balance, usdc_balance)
            
            if not conversion:
                logger.info(f"Балансировка не нужна (разница < ${self.min_balance_diff})")
                return
            
            logger.info(f"🔄 Балансировка: {conversion['from']} → {conversion['to']}, ${conversion['amount']:.2f}")
            
            # Выполняем конвертацию
            result = self.execute_conversion(conversion)
            
            # Отправляем отчет
            self.send_balance_report(balances, conversion, result)
            
        except Exception as e:
            logger.error(f"Ошибка балансировки стейблов: {e}")
    
    def send_balance_report(self, before_balances, conversion, result):
        """Отправить отчет о балансировке"""
        try:
            if result['success']:
                message = (
                    f"<b>⚖️ БАЛАНСИРОВКА СТЕЙБЛКОИНОВ</b>\n\n"
                    f"📊 <b>ДО:</b>\n"
                    f"💚 USDT: ${before_balances['USDT']:.2f}\n"
                    f"💙 USDC: ${before_balances['USDC']:.2f}\n"
                    f"💰 Всего: ${sum(before_balances.values()):.2f}\n\n"
                    f"🔄 <b>КОНВЕРТАЦИЯ:</b>\n"
                    f"📤 {conversion['from']} → {conversion['to']}\n"
                    f"💵 Сумма: ${conversion['amount']:.2f}\n"
                    f"📊 Символ: {conversion['symbol']}\n"
                    f"⚡ Тип: {conversion['side']}\n"
                    f"🆔 Ордер: <code>{result['order_id']}</code>\n\n"
                    f"🎯 <b>ЦЕЛЬ:</b> Выравнивание 50/50\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
            else:
                message = (
                    f"<b>❌ ОШИБКА БАЛАНСИРОВКИ СТЕЙБЛОВ</b>\n\n"
                    f"💚 USDT: ${before_balances['USDT']:.2f}\n"
                    f"💙 USDC: ${before_balances['USDC']:.2f}\n\n"
                    f"🔄 Попытка: {conversion['from']} → {conversion['to']}\n"
                    f"💵 Сумма: ${conversion['amount']:.2f}\n"
                    f"❌ Ошибка: {result['error']}\n\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
            
            self.send_telegram_message(message)
            
        except Exception as e:
            logger.error(f"Ошибка отправки отчета: {e}")
    
    def start_monitoring(self):
        """Запустить мониторинг балансировки"""
        logger.info("🚀 Запуск балансировщика стейблкоинов")
        
        # Отправляем уведомление о запуске
        startup_message = (
            f"<b>⚖️ БАЛАНСИРОВЩИК СТЕЙБЛОВ ЗАПУЩЕН</b>\n\n"
            f"🔄 Проверка каждый час\n"
            f"📊 Цель: 50% USDT / 50% USDC\n"
            f"💰 Минимальная разница: ${self.min_balance_diff}\n"
            f"⚡ Маркет ордера для быстрого исполнения\n\n"
            f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
        )
        self.send_telegram_message(startup_message)
        
        while True:
            try:
                self.check_and_balance()
                time.sleep(60)  # Проверяем каждую минуту, но балансируем раз в час
            except KeyboardInterrupt:
                logger.info("🛑 Балансировщик остановлен")
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле балансировщика: {e}")
                time.sleep(60)

if __name__ == "__main__":
    balancer = StablecoinBalancer()
    balancer.start_monitoring()