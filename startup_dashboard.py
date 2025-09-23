import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

class StartupDashboard:
    def __init__(self):
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
        """Получить информацию для стартовой плашки (упрощённая версия)"""
        return "Здесь будет стартовая плашка"
    
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
    
    def send_auto_purchase_notification(self):
        """Упрощённое уведомление об автопокупках"""
        return self.send_telegram_message("Здесь будет уведомление об автопокупках")
    
    def send_extended_portfolio_report(self):
        """Упрощённая заглушка расширенного отчёта о портфеле"""
        result = self.send_telegram_message("Здесь будет расширенный отчёт о портфеле")
        return bool(result and result.get('ok'))