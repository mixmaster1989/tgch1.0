#!/usr/bin/env python3
"""
Сводка по аккаунту MEXC
Получает данные через API и отправляет в Telegram
"""

import requests
import json
from datetime import datetime
from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def send_telegram_message(text):
    """Отправка сообщения в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': text,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return False

def get_account_summary():
    """Получение сводки аккаунта"""
    try:
        api = MexAPI()
        
        # Получаем данные аккаунта
        account_info = api.get_account_info()
        if not account_info:
            return "❌ Не удалось получить данные аккаунта"
        
        # Парсим балансы
        balances = {}
        total_usdt = 0
        
        for balance in account_info.get('balances', []):
            asset = balance.get('asset', '')
            free = float(balance.get('free', 0))
            locked = float(balance.get('locked', 0))
            total = free + locked
            
            if total > 0:
                balances[asset] = {
                    'free': free,
                    'locked': locked,
                    'total': total
                }
                
                if asset == 'USDT':
                    total_usdt = total
        
        # Получаем цены для конвертации в USDT
        portfolio_value = 0
        asset_values = {}
        
        for asset, balance in balances.items():
            if asset in ['USDT', 'USDC']:
                value = balance['total']
                asset_values[asset] = value
                portfolio_value += value
            else:
                try:
                    ticker = api.get_ticker_price(f"{asset}USDT")
                    if ticker and 'price' in ticker:
                        price = float(ticker['price'])
                        value = balance['total'] * price
                        asset_values[asset] = value
                        portfolio_value += value
                    else:
                        asset_values[asset] = 0
                except:
                    asset_values[asset] = 0
        
        # Получаем открытые ордера
        open_orders = []
        try:
            orders = api.get_open_orders()
            if isinstance(orders, list):
                open_orders = orders
        except:
            pass
        
        # Формируем сводку
        message = f"<b>📊 СВОДКА АККАУНТА MEXC</b>\n"
        message += f"{'='*40}\n\n"
        
        # Общая стоимость
        message += f"<b>💰 ОБЩАЯ СТОИМОСТЬ ПОРТФЕЛЯ</b>\n"
        message += f"💵 ${portfolio_value:.2f} USDT\n\n"
        
        # Активы
        if asset_values:
            message += f"<b>🏦 АКТИВЫ</b>\n"
            sorted_assets = sorted(asset_values.items(), key=lambda x: x[1], reverse=True)
            
            for asset, value in sorted_assets:
                if value > 0.01:  # Показываем только значимые суммы
                    balance_info = balances.get(asset, {})
                    total_amount = balance_info.get('total', 0)
                    free_amount = balance_info.get('free', 0)
                    locked_amount = balance_info.get('locked', 0)
                    
                    percentage = (value / portfolio_value * 100) if portfolio_value > 0 else 0
                    
                    message += f"• <b>{asset}</b>: {total_amount:.6f}\n"
                    message += f"  💵 ${value:.2f} ({percentage:.1f}%)\n"
                    
                    if locked_amount > 0:
                        message += f"  🔒 Заблокировано: {locked_amount:.6f}\n"
                    message += f"  🆓 Доступно: {free_amount:.6f}\n\n"
        
        # Открытые ордера
        if open_orders:
            message += f"<b>📋 ОТКРЫТЫЕ ОРДЕРА ({len(open_orders)})</b>\n"
            for order in open_orders[:5]:  # Показываем только первые 5
                symbol = order.get('symbol', 'N/A')
                side = order.get('side', 'N/A')
                order_type = order.get('type', 'N/A')
                price = float(order.get('price', 0))
                qty = float(order.get('origQty', 0))
                
                message += f"• {symbol} {side} {order_type}\n"
                message += f"  💰 {qty:.6f} @ ${price:.6f}\n"
            
            if len(open_orders) > 5:
                message += f"  ... и еще {len(open_orders) - 5} ордеров\n"
            message += "\n"
        else:
            message += f"<b>📋 ОТКРЫТЫЕ ОРДЕРА</b>\n"
            message += f"Нет открытых ордеров\n\n"
        
        # Статистика
        message += f"<b>📈 СТАТИСТИКА</b>\n"
        message += f"🔢 Активных активов: {len([v for v in asset_values.values() if v > 0.01])}\n"
        message += f"📋 Открытых ордеров: {len(open_orders)}\n"
        message += f"⏰ Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
        
        message += f"{'='*40}\n"
        message += f"<b>🚀 MEXCAITRADE</b>"
        
        return message
        
    except Exception as e:
        return f"❌ Ошибка получения данных: {str(e)}"

def main():
    """Основная функция"""
    print("📊 Получение сводки аккаунта...")
    
    # Получаем сводку
    summary = get_account_summary()
    
    # Выводим в консоль
    print("\n" + "="*50)
    print("СВОДКА АККАУНТА")
    print("="*50)
    # Убираем HTML теги для консоли
    console_summary = summary.replace('<b>', '').replace('</b>', '').replace('<i>', '').replace('</i>', '')
    print(console_summary)
    print("="*50)
    
    # Отправляем в Telegram
    print("\n📤 Отправка в Telegram...")
    success = send_telegram_message(summary)
    
    if success:
        print("✅ Сводка отправлена в Telegram")
    else:
        print("❌ Ошибка отправки в Telegram")

if __name__ == "__main__":
    main()