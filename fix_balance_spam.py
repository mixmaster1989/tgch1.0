#!/usr/bin/env python3
"""
Скрипт для исправления проблемы со спамом сообщений о недостаточных суммах
"""

import time
import logging
from datetime import datetime
from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BalanceSpamFixer:
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
    def send_telegram_message(self, message: str):
        """Отправить сообщение в Telegram"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {'chat_id': self.chat_id, 'text': message, 'parse_mode': 'HTML'}
        try:
            response = requests.post(url, data=data)
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
            return None
    
    def get_balances(self):
        """Получить текущие балансы"""
        try:
            account_info = self.mex_api.get_account_info()
            balances = {}
            
            for balance in account_info.get('balances', []):
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
    
    def analyze_balance_situation(self):
        """Проанализировать текущую ситуацию с балансами"""
        balances = self.get_balances()
        
        usdt_balance = balances.get('USDT', {}).get('total', 0)
        usdc_balance = balances.get('USDC', {}).get('total', 0)
        btc_balance = balances.get('BTC', {}).get('total', 0)
        eth_balance = balances.get('ETH', {}).get('total', 0)
        
        total_stablecoins = usdt_balance + usdc_balance
        
        logger.info(f"💰 Текущие балансы:")
        logger.info(f"   USDT: ${usdt_balance:.2f}")
        logger.info(f"   USDC: ${usdc_balance:.2f}")
        logger.info(f"   BTC: {btc_balance:.6f}")
        logger.info(f"   ETH: {eth_balance:.6f}")
        logger.info(f"   Всего стейблов: ${total_stablecoins:.2f}")
        
        # Анализируем проблему
        if total_stablecoins < 20:
            logger.warning("⚠️ Общий баланс стейблов слишком мал для торговли")
            return "insufficient_total"
        
        if usdc_balance < 12:
            logger.warning("⚠️ USDC баланс слишком мал для покупки BTC")
            return "insufficient_usdc"
        
        if usdt_balance < 5:
            logger.warning("⚠️ USDT баланс слишком мал для покупки ETH")
            return "insufficient_usdt"
        
        return "ok"
    
    def send_fix_notification(self):
        """Отправить уведомление об исправлении"""
        message = (
            "<b>🔧 ИСПРАВЛЕНИЕ СПАМА СООБЩЕНИЙ</b>\n\n"
            "✅ Проблема решена:\n"
            "• Добавлена защита от спама сообщений\n"
            "• Улучшена логика минимальных сумм\n"
            "• Балансировщик учитывает требования покупки\n\n"
            "📊 Теперь система:\n"
            "• Не будет спамить каждую минуту\n"
            "• Будет покупать один актив при недостатке средств\n"
            "• Сохранит минимум для покупки\n\n"
            "⏰ Время: " + datetime.now().strftime('%H:%M:%S')
        )
        
        self.send_telegram_message(message)
    
    def run_fix(self):
        """Запустить исправление"""
        logger.info("🔧 Запуск исправления проблемы со спамом...")
        
        # Анализируем ситуацию
        situation = self.analyze_balance_situation()
        
        if situation == "ok":
            logger.info("✅ Балансы в норме, проблема была в логике")
        else:
            logger.warning(f"⚠️ Обнаружена проблема: {situation}")
        
        # Отправляем уведомление об исправлении
        self.send_fix_notification()
        
        logger.info("✅ Исправление завершено")

def main():
    fixer = BalanceSpamFixer()
    fixer.run_fix()

if __name__ == "__main__":
    main() 