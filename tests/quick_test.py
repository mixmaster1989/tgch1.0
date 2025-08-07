#!/usr/bin/env python3
"""
Быстрая проверка проблем
"""

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from openrouter_manager import OpenRouterManager

def quick_check():
    print("=== БЫСТРАЯ ДИАГНОСТИКА ===")
    
    # 1. Проверяем переменные
    print(f"Bot Token: {'OK' if TELEGRAM_BOT_TOKEN else 'ОТСУТСТВУЕТ'}")
    print(f"Chat ID: {TELEGRAM_CHAT_ID}")
    
    # 2. Проверяем OpenRouter
    try:
        manager = OpenRouterManager()
        status = manager.get_status()
        print(f"Silver keys доступно: {status['silver_keys_available']}")
        
        # Тест запроса
        result = manager.request_with_silver_keys("тест")
        print(f"OpenRouter работает: {result['success']}")
        if not result['success']:
            print(f"Ошибка: {result['response']}")
            
    except Exception as e:
        print(f"Ошибка OpenRouter: {e}")
    
    # 3. Проверяем Chat ID формат
    try:
        chat_id_int = int(TELEGRAM_CHAT_ID)
        print(f"Chat ID число: {chat_id_int}")
    except:
        print("ОШИБКА: Chat ID не число!")

if __name__ == "__main__":
    quick_check()