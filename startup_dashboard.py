import requests
import os
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
    
    def send_video(self, video_path: str, caption: str = ""):
        """Отправить видео в Telegram"""
        if not os.path.exists(video_path):
            print(f"Файл {video_path} не найден")
            return None
            
        url = f"https://api.telegram.org/bot{self.bot_token}/sendVideo"
        
        try:
            with open(video_path, 'rb') as video_file:
                files = {'video': video_file}
                data = {
                    'chat_id': self.chat_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                response = requests.post(url, files=files, data=data)
                return response.json()
        except Exception as e:
            print(f"Ошибка отправки видео в Telegram: {e}")
            return None
    
    def send_startup_notification(self):
        """Отправить стартовое видео"""
        video_path = "intro.mp4"
        caption = "🚀 <b>MEXCAITRADE ЗАПУЩЕН</b>\n\n🤖 Торговый бот активирован и готов к работе!"
        
        result = self.send_video(video_path, caption)
        
        if result and result.get('ok'):
            print("Стартовое видео отправлено в Telegram")
        else:
            print("Ошибка отправки стартового видео")
            print(f"Результат: {result}")
        
        return result
    
    def send_auto_purchase_notification(self):
        """Уведомление об автопокупках (отключено)"""
        return None
    
    def send_extended_portfolio_report(self):
        """Расширенный отчёт о портфеле (отключен)"""
        return True