#!/usr/bin/env python3
"""
Отладка бота с подробными логами
"""

import logging
from ai_chat_bot import AIChatBot

# Включаем подробное логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

def debug_bot():
    try:
        print("=== ОТЛАДКА AI CHAT BOT ===")
        
        # Создаем бота
        bot = AIChatBot()
        
        print(f"Target Chat ID: {bot.target_chat_id}")
        print(f"Bot Token: {bot.app.bot.token[:20]}...")
        
        # Проверяем OpenRouter
        status = bot.openrouter.get_status()
        print(f"OpenRouter статус: {status}")
        
        # Тестируем OpenRouter
        test_result = bot.openrouter.request_with_silver_keys("Привет, тест!")
        print(f"OpenRouter тест: {test_result}")
        
        print("\nЗапускаю бота с отладкой...")
        bot.run()
        
    except Exception as e:
        print(f"ОШИБКА: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_bot()