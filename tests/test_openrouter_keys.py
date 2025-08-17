#!/usr/bin/env python3
"""
Тест всех ключей OpenRouter
"""

import asyncio
import aiohttp
import json
from datetime import datetime

# Все ключи для тестирования
KEYS = {
    "KEY1": "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",
    "KEY2": "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",
    "KEY3": "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",
    "KEY4": "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",
    "KEY5": "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",
    "KEY6": "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",
    "KEY7": "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",
    "KEY9": "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",
    "KEY10": "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"
}

async def test_key(session, key_name, api_key):
    """Тестирует один ключ"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [
            {"role": "user", "content": "Привет! Это тест. Ответь одним словом: 'OK'"}
        ],
        "max_tokens": 10
    }
    
    try:
        async with session.post(url, headers=headers, json=data, timeout=10) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    "status": "✅ РАБОТАЕТ",
                    "response": result.get("choices", [{}])[0].get("message", {}).get("content", "Нет ответа"),
                    "usage": result.get("usage", {}),
                    "model": result.get("model", "Неизвестно")
                }
            else:
                error_text = await response.text()
                return {
                    "status": f"❌ ОШИБКА {response.status}",
                    "error": error_text[:100] + "..." if len(error_text) > 100 else error_text
                }
    except Exception as e:
        return {
            "status": "💥 ИСКЛЮЧЕНИЕ",
            "error": str(e)
        }

async def test_all_keys():
    """Тестирует все ключи"""
    print("🔍 ТЕСТ ВСЕХ КЛЮЧЕЙ OPENROUTER")
    print("=" * 60)
    print(f"Время: {datetime.now()}")
    print()
    
    working_keys = []
    failed_keys = []
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for key_name, api_key in KEYS.items():
            task = test_key(session, key_name, api_key)
            tasks.append((key_name, task))
        
        for key_name, task in tasks:
            print(f"🧪 Тестирую {key_name}...")
            result = await task
            
            print(f"   {result['status']}")
            if "РАБОТАЕТ" in result['status']:
                print(f"   📝 Ответ: {result['response']}")
                print(f"   🤖 Модель: {result['model']}")
                if result.get('usage'):
                    usage = result['usage']
                    print(f"   📊 Токены: {usage.get('prompt_tokens', 0)} + {usage.get('completion_tokens', 0)}")
                working_keys.append(key_name)
            else:
                print(f"   🚫 Ошибка: {result.get('error', 'Неизвестно')}")
                failed_keys.append(key_name)
            print()
    
    # Итоговый отчет
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 60)
    print(f"✅ Рабочих ключей: {len(working_keys)}")
    print(f"❌ Нерабочих ключей: {len(failed_keys)}")
    print()
    
    if working_keys:
        print("✅ РАБОЧИЕ КЛЮЧИ:")
        for key in working_keys:
            print(f"   {key}: {KEYS[key]}")
        print()
        
        # Рекомендации для .env
        print("📝 РЕКОМЕНДАЦИИ ДЛЯ .env:")
        print("=" * 60)
        for i, key in enumerate(working_keys[:3], 1):  # Берем первые 3 рабочих
            print(f"OPENROUTER_API_KEY{i}={KEYS[key]}")
        print()
        
        if len(working_keys) > 3:
            print(f"📋 Остальные рабочие ключи ({len(working_keys)-3}):")
            for key in working_keys[3:]:
                print(f"   {key}: {KEYS[key]}")
    
    if failed_keys:
        print("❌ НЕРАБОЧИЕ КЛЮЧИ:")
        for key in failed_keys:
            print(f"   {key}: {KEYS[key]}")
    
    return working_keys, failed_keys

if __name__ == "__main__":
    asyncio.run(test_all_keys()) 