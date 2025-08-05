#!/usr/bin/env python3
"""
Тест стартовой плашки
"""

from startup_dashboard import StartupDashboard

def test_startup_dashboard():
    try:
        print("Тестирую стартовую плашку...")
        
        # Создаем дашборд
        dashboard = StartupDashboard()
        
        # Получаем информацию
        message = dashboard.get_startup_info()
        
        print("\nСформированное сообщение:")
        print("=" * 50)
        print(message)
        print("=" * 50)
        
        # Отправляем в Telegram (если настроен CHAT_ID)
        if dashboard.chat_id and dashboard.chat_id != 'your_telegram_chat_id':
            print("\nОтправляю в Telegram...")
            result = dashboard.send_startup_notification()
            if result:
                print("Успешно отправлено!")
            else:
                print("Ошибка отправки")
        else:
            print("\nTELEGRAM_CHAT_ID не настроен, сообщение не отправлено")
            
    except Exception as e:
        print(f"Ошибка: {str(e)}")

if __name__ == "__main__":
    test_startup_dashboard()