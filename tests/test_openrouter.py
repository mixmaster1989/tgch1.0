#!/usr/bin/env python3
"""
Тест системы OpenRouter ключей
"""

from openrouter_manager import OpenRouterManager

def test_openrouter_keys():
    try:
        print("Тестирую систему OpenRouter ключей...")
        
        # Создаем менеджер
        manager = OpenRouterManager()
        
        # Проверяем статус
        status = manager.get_status()
        print(f"\nСтатус ключей:")
        print(f"Golden key доступен: {status['golden_key_available']}")
        print(f"Silver keys всего: {status['silver_keys_total']}")
        print(f"Silver keys доступно: {status['silver_keys_available']}")
        
        # Тест silver ключей
        print("\n=== Тест Silver Keys ===")
        test_prompt = "Привет! Как дела?"
        
        result = manager.request_with_silver_keys(test_prompt)
        print(f"Успех: {result['success']}")
        print(f"Ключ: {result['key_used']}")
        print(f"Ответ: {result['response'][:100]}...")
        
        # Тест golden ключа
        print("\n=== Тест Golden Key ===")
        trading_prompt = "Проанализируй BTC/USDT: цена 45000, объем растет. Рекомендация?"
        
        result = manager.request_with_golden_key(trading_prompt)
        print(f"Успех: {result['success']}")
        print(f"Ключ: {result['key_used']}")
        print(f"Ответ: {result['response'][:100]}...")
        
    except Exception as e:
        print(f"Ошибка: {str(e)}")

if __name__ == "__main__":
    test_openrouter_keys()