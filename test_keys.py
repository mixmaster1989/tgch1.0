#!/usr/bin/env python3
"""
Тест всех ключей OpenRouter
"""

import requests
from config import OPENROUTER_API_KEY, OPENROUTER_SILVER_KEY_1, OPENROUTER_SILVER_KEY_2, OPENROUTER_SILVER_KEY_3

def test_key(key_name, key_value):
    if not key_value or key_value.startswith('your_'):
        print(f"{key_name}: НЕ НАСТРОЕН")
        return
    
    headers = {
        'Authorization': f'Bearer {key_value}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'deepseek/deepseek-r1-0528:free',
        'messages': [{'role': 'user', 'content': 'test'}],
        'max_tokens': 10
    }
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=10
        )
        
        print(f"{key_name}: {response.status_code} - {response.text[:100]}")
        
    except Exception as e:
        print(f"{key_name}: ОШИБКА - {e}")

def main():
    print("=== ТЕСТ ВСЕХ КЛЮЧЕЙ ===")
    test_key("GOLDEN", OPENROUTER_API_KEY)
    test_key("SILVER_1", OPENROUTER_SILVER_KEY_1)
    test_key("SILVER_2", OPENROUTER_SILVER_KEY_2)
    test_key("SILVER_3", OPENROUTER_SILVER_KEY_3)

if __name__ == "__main__":
    main()