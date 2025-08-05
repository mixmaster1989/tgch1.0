import requests
from datetime import datetime
from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class StartupDashboard:
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
            print(f"Ошибка отправки в Telegram: {e}")
            return None
    
    def get_startup_info(self):
        """Получить информацию для стартовой плашки"""
        try:
            # Получаем баланс
            account_info = self.mex_api.get_account_info()
            
            # Получаем открытые ордера
            open_orders = self.mex_api.get_open_orders()
            
            # Формируем сообщение
            message = "<b>MEX Trading Bot запущен!</b>\n"
            message += f"Время запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
            
            # Статус подключения
            if 'balances' in account_info:
                message += "<b>Статус подключения:</b> Активно\n"
                message += f"<b>Тип аккаунта:</b> {account_info.get('accountType', 'SPOT')}\n\n"
                
                # Баланс
                message += "<b>Баланс аккаунта:</b>\n"
                balances = [b for b in account_info['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
                
                if balances:
                    for balance in balances[:5]:  # Показываем только первые 5
                        free = float(balance['free'])
                        locked = float(balance['locked'])
                        total = free + locked
                        message += f"  • {balance['asset']}: {total:.4f} (свободно: {free:.4f})\n"
                else:
                    message += "  • Нет активных балансов\n"
                
                # Открытые ордера
                message += f"\n<b>Открытые ордера:</b> {len(open_orders) if isinstance(open_orders, list) else 0}\n"
                
                if isinstance(open_orders, list) and len(open_orders) > 0:
                    for order in open_orders[:3]:  # Показываем только первые 3
                        side_emoji = "[BUY]" if order['side'] == 'BUY' else "[SELL]"
                        message += f"  {side_emoji} {order['symbol']}: {order['side']} {float(order['origQty']):.4f} @ {float(order['price']):.6f}\n"
                
                # Разрешения
                permissions = account_info.get('permissions', [])
                message += f"\n<b>Разрешения:</b> {', '.join(permissions)}\n"
                
                # Статус торговли
                can_trade = account_info.get('canTrade', False)
                can_withdraw = account_info.get('canWithdraw', False)
                can_deposit = account_info.get('canDeposit', False)
                
                message += f"<b>Торговля:</b> {'ДА' if can_trade else 'НЕТ'}\n"
                message += f"<b>Вывод:</b> {'ДА' if can_withdraw else 'НЕТ'}\n"
                message += f"<b>Депозит:</b> {'ДА' if can_deposit else 'НЕТ'}\n"
                
            else:
                message += "<b>Статус подключения:</b> Ошибка\n"
                message += f"<b>Ошибка:</b> {account_info}\n"
            
            message += "\n<b>Бот готов к работе!</b>\n"
            message += "Используйте /start для управления"
            
            return message
            
        except Exception as e:
            error_message = "<b>MEX Trading Bot запущен!</b>\n"
            error_message += f"Время запуска: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n"
            error_message += f"<b>Ошибка получения данных:</b>\n{str(e)}\n\n"
            error_message += "Проверьте настройки API ключей"
            return error_message
    
    def send_startup_notification(self):
        """Отправить стартовое уведомление"""
        message = self.get_startup_info()
        result = self.send_telegram_message(message)
        
        if result and result.get('ok'):
            print("Стартовое уведомление отправлено в Telegram")
        else:
            print("Ошибка отправки стартового уведомления")
            print(f"Сообщение: {message}")
        
        return result