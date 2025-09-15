#!/usr/bin/env python3
"""
Продажа SOL и KAVA по рынку и покупка USDC
"""

import time
import logging
from datetime import datetime
from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SellSolKavaBuyUsdc:
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Целевая сумма для покупки USDC
        self.target_usdc_amount = 15.0
        
    def send_telegram_message(self, message: str):
        """Отправить сообщение в Telegram"""
        if not self.bot_token or not self.chat_id:
            logger.info(f"Telegram: {message}")
            return
            
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
    
    def get_account_balances(self) -> dict:
        """Получить балансы аккаунта"""
        try:
            account_info = self.mex_api.get_account_info()
            if 'balances' not in account_info:
                logger.error("Не удалось получить балансы")
                return {}
            
            balances = {}
            for balance in account_info['balances']:
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                if total > 0:
                    balances[asset] = {
                        'free': free,
                        'locked': locked,
                        'total': total
                    }
            
            return balances
            
        except Exception as e:
            logger.error(f"Ошибка получения балансов: {e}")
            return {}
    
    def get_current_price(self, symbol: str) -> float:
        """Получить текущую цену символа"""
        try:
            ticker = self.mex_api.get_ticker_price(symbol)
            if 'price' in ticker:
                return float(ticker['price'])
            return 0.0
        except Exception as e:
            logger.error(f"Ошибка получения цены для {symbol}: {e}")
            return 0.0
    
    def place_market_sell_order(self, symbol: str, quantity: float) -> dict:
        """Разместить рыночный ордер на продажу"""
        try:
            logger.info(f"📤 Продажа {quantity} {symbol} по рынку...")
            
            # Создаем рыночный ордер на продажу
            order = self.mex_api.place_order(
                symbol=symbol,
                side='SELL',
                quantity=quantity,
                price=None  # Рыночный ордер
            )
            
            logger.info(f"✅ Ордер на продажу размещен: {order}")
            return order
            
        except Exception as e:
            logger.error(f"Ошибка размещения ордера на продажу {symbol}: {e}")
            return {'error': str(e)}
    
    def place_market_buy_order(self, symbol: str, quote_quantity: float) -> dict:
        """Разместить рыночный ордер на покупку"""
        try:
            logger.info(f"📥 Покупка {symbol} на ${quote_quantity} по рынку...")
            
            # Создаем рыночный ордер на покупку
            order = self.mex_api.place_order(
                symbol=symbol,
                side='BUY',
                quantity=quote_quantity,
                price=None  # Рыночный ордер
            )
            
            logger.info(f"✅ Ордер на покупку размещен: {order}")
            return order
            
        except Exception as e:
            logger.error(f"Ошибка размещения ордера на покупку {symbol}: {e}")
            return {'error': str(e)}
    
    def execute_sell_and_buy(self):
        """Выполнить продажу SOL/KAVA и покупку USDC"""
        try:
            logger.info("🚀 Начинаем операцию: продажа SOL/KAVA → покупка USDC")
            
            # Получаем балансы
            balances = self.get_account_balances()
            if not balances:
                logger.error("Не удалось получить балансы")
                return False
            
            # Проверяем балансы SOL и KAVA
            sol_balance = balances.get('SOL', {}).get('free', 0)
            kava_balance = balances.get('KAVA', {}).get('free', 0)
            
            logger.info(f"📊 Балансы: SOL={sol_balance}, KAVA={kava_balance}")
            
            if sol_balance <= 0 and kava_balance <= 0:
                logger.warning("Нет балансов SOL и KAVA для продажи")
                return False
            
            # Получаем текущие цены
            sol_price = self.get_current_price('SOLUSDT')
            kava_price = self.get_current_price('KAVAUSDT')
            
            logger.info(f"💰 Текущие цены: SOL=${sol_price}, KAVA=${kava_price}")
            
            # Рассчитываем примерную выручку
            sol_value = sol_balance * sol_price
            kava_value = kava_balance * kava_price
            total_expected_revenue = sol_value + kava_value
            
            logger.info(f"💵 Ожидаемая выручка: SOL=${sol_value:.2f}, KAVA=${kava_value:.2f}, Всего=${total_expected_revenue:.2f}")
            
            # Продаем SOL если есть баланс
            sol_order = None
            if sol_balance > 0:
                logger.info(f"📤 Продаем {sol_balance} SOL по рынку...")
                sol_order = self.place_market_sell_order('SOLUSDT', sol_balance)
                if 'error' in sol_order:
                    logger.error(f"Ошибка продажи SOL: {sol_order['error']}")
                    return False
            
            # Продаем KAVA если есть баланс
            kava_order = None
            if kava_balance > 0:
                logger.info(f"📤 Продаем {kava_balance} KAVA по рынку...")
                kava_order = self.place_market_sell_order('KAVAUSDT', kava_balance)
                if 'error' in kava_order:
                    logger.error(f"Ошибка продажи KAVA: {kava_order['error']}")
                    return False
            
            # Ждем немного для исполнения ордеров
            logger.info("⏳ Ждем исполнения ордеров...")
            time.sleep(3)
            
            # Проверяем новый баланс USDT
            new_balances = self.get_account_balances()
            usdt_balance = new_balances.get('USDT', {}).get('free', 0)
            
            logger.info(f"💰 Новый баланс USDT: ${usdt_balance:.2f}")
            
            # Покупаем USDC на доступную сумму
            if usdt_balance > 0:
                # Используем всю доступную сумму, но с небольшим запасом на комиссии
                buy_amount = usdt_balance * 0.99  # 1% запас на комиссии
                
                logger.info(f"📥 Покупаем USDC на ${buy_amount:.2f} (доступно ${usdt_balance:.2f})...")
                usdc_order = self.place_market_buy_order('USDCUSDT', buy_amount)
                
                if 'error' in usdc_order:
                    logger.error(f"Ошибка покупки USDC: {usdc_order['error']}")
                    return False
                
                # Формируем отчет
                report = f"✅ <b>ОПЕРАЦИЯ ЗАВЕРШЕНА</b>\n\n"
                report += f"📤 <b>Продано:</b>\n"
                if sol_order:
                    report += f"   SOL: {sol_balance} монет\n"
                if kava_order:
                    report += f"   KAVA: {kava_balance} монет\n"
                report += f"📥 <b>Куплено:</b>\n"
                report += f"   USDC: ${buy_amount:.2f}\n\n"
                report += f"💰 Выручка: ${usdt_balance:.2f}\n"
                report += f"💸 Комиссии: ~${(total_expected_revenue - usdt_balance):.2f}\n"
                report += f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                
                self.send_telegram_message(report)
                logger.info("✅ Операция успешно завершена")
                return True
            else:
                logger.error(f"Нет USDT для покупки USDC")
                return False
                
        except Exception as e:
            error_msg = f"❌ Ошибка выполнения операции: {e}"
            logger.error(error_msg)
            self.send_telegram_message(error_msg)
            return False
    
    def run(self):
        """Запустить операцию"""
        logger.info("🚀 Запуск операции продажи SOL/KAVA и покупки USDC")
        
        success = self.execute_sell_and_buy()
        
        if success:
            print("\n" + "="*60)
            print("✅ ОПЕРАЦИЯ УСПЕШНО ЗАВЕРШЕНА")
            print("="*60)
            print("📤 Проданы SOL и KAVA по рынку")
            print("📥 Куплено $15 USDC")
            print("="*60)
        else:
            print("\n" + "="*60)
            print("❌ ОПЕРАЦИЯ НЕ УДАЛАСЬ")
            print("="*60)

def main():
    """Основная функция"""
    trader = SellSolKavaBuyUsdc()
    trader.run()

if __name__ == "__main__":
    main()
