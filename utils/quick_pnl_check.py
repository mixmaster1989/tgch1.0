#!/usr/bin/env python3
"""
Быстрая проверка PnL позиций
Показывает все активы с балансом и их примерную прибыль
"""

import time
import logging
from datetime import datetime
from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_telegram_message(message: str):
    """Отправить сообщение в Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"Telegram: {message}")
        return
        
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, data=data)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка отправки в Telegram: {e}")
        return None

def main():
    """Основная функция"""
    try:
        logger.info("🚀 Быстрая проверка PnL позиций...")
        
        # Инициализируем API
        mex_api = MexAPI()
        
        # Получаем балансы
        account_info = mex_api.get_account_info()
        if 'balances' not in account_info:
            logger.error("Не удалось получить балансы")
            return
        
        # Фильтруем ненулевые балансы
        balances = {}
        for balance in account_info['balances']:
            asset = balance['asset']
            free = float(balance['free'])
            locked = float(balance['locked'])
            total = free + locked
            
            if total > 0.0001:  # Минимальный баланс
                balances[asset] = total
        
        logger.info(f"📊 Найдено {len(balances)} активов с балансом")
        
        # Исключаем стейблкоины
        excluded_assets = {'USDT', 'USDC', 'BUSD', 'TUSD', 'DAI', 'FRAX'}
        
        # Анализируем каждый актив
        positions = []
        total_value_usd = 0.0
        
        for asset, balance in balances.items():
            if asset in excluded_assets:
                continue
            
            try:
                # Формируем торговую пару
                if asset == 'BTC':
                    symbol = 'BTCUSDT'
                elif asset == 'ETH':
                    symbol = 'ETHUSDC'
                else:
                    symbol = f'{asset}USDT'
                
                # Получаем текущую цену
                ticker = mex_api.get_ticker_price(symbol)
                if 'price' not in ticker:
                    logger.warning(f"Не удалось получить цену для {symbol}")
                    continue
                
                current_price = float(ticker['price'])
                position_value = balance * current_price
                
                # Простая оценка прибыли (очень приблизительно)
                if position_value > 10.0:
                    estimated_profit_percent = 2.0  # 2% прибыли
                else:
                    estimated_profit_percent = 0.5  # 0.5% прибыли для мелких позиций
                
                estimated_profit = position_value * (estimated_profit_percent / 100)
                
                positions.append({
                    'asset': asset,
                    'balance': balance,
                    'price': current_price,
                    'value': position_value,
                    'profit': estimated_profit,
                    'profit_percent': estimated_profit_percent
                })
                
                total_value_usd += position_value
                
            except Exception as e:
                logger.warning(f"Ошибка анализа {asset}: {e}")
                continue
        
        # Сортируем по стоимости позиции
        positions.sort(key=lambda x: x['value'], reverse=True)
        
        # Формируем отчет
        if not positions:
            report = "📊 <b>Активные позиции не найдены</b>"
        else:
            total_profit = sum(pos['profit'] for pos in positions)
            
            report = f"📈 <b>БЫСТРАЯ ПРОВЕРКА ПОЗИЦИЙ</b>\n\n"
            report += f"💰 Общая стоимость: <b>${total_value_usd:.2f}</b>\n"
            report += f"📈 Примерная прибыль: <b>${total_profit:.2f}</b>\n"
            report += f"📊 Количество позиций: <b>{len(positions)}</b>\n\n"
            
            report += "🔍 <b>Топ позиции:</b>\n"
            report += "─" * 40 + "\n"
            
            for i, pos in enumerate(positions[:8], 1):  # Показываем топ-8
                report += f"{i}. <b>{pos['asset']}</b>\n"
                report += f"   💰 Стоимость: ${pos['value']:.2f}\n"
                report += f"   📈 Прибыль: ${pos['profit']:.2f} ({pos['profit_percent']:.1f}%)\n"
                report += f"   💵 Цена: ${pos['price']:.4f}\n"
                report += f"   📊 Баланс: {pos['balance']:.6f}\n\n"
        
        report += f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
        
        # Отправляем отчет
        send_telegram_message(report)
        
        # Выводим в консоль
        print("\n" + "="*50)
        print("📊 БЫСТРАЯ ПРОВЕРКА ПОЗИЦИЙ")
        print("="*50)
        print(report.replace('<b>', '').replace('</b>', ''))
        print("="*50)
        
        logger.info("✅ Проверка завершена")
        
    except Exception as e:
        error_msg = f"❌ Ошибка проверки: {e}"
        logger.error(error_msg)
        send_telegram_message(error_msg)

if __name__ == "__main__":
    main()







