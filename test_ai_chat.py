#!/usr/bin/env python3
"""
Тест AI чат-бота
"""

from ai_chat_bot import AIChatBot

def test_ai_chat():
    try:
        print("Запускаю AI Chat Bot для тестирования...")
        print("Напишите сообщение в группу для тестирования")
        
        # Создаем и запускаем чат-бота
        bot = AIChatBot()
        bot.run()
        
    except KeyboardInterrupt:
        print("Бот остановлен")
    except Exception as e:
        print(f"Ошибка: {str(e)}")

if __name__ == "__main__":
    test_ai_chat()