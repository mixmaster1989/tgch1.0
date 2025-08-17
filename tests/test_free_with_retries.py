#!/usr/bin/env python3
"""
Тест всех ключей OpenRouter на БЕСПЛАТНОЙ модели с РЕТРАЯМИ
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

async def test_key_with_retries(session, key_name, api_key, max_retries=5, timeout=3):
    """Тестирует один ключ с ретраями"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://mexc-trading-bot.com",
        "X-Title": "MEXC Trading Bot"
    }
    
    data = {
        "model": "deepseek/deepseek-r1-0528:free",  # БЕСПЛАТНАЯ МОДЕЛЬ!
        "messages": [
            {"role": "user", "content": "Привет! Это тест. Ответь одним словом: 'OK'"}
        ],
        "max_tokens": 10
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"      Попытка {attempt}/{max_retries}...")
            
            async with session.post(url, headers=headers, json=data, timeout=timeout) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "status": "✅ РАБОТАЕТ",
                        "response": result.get("choices", [{}])[0].get("message", {}).get("content", "Нет ответа"),
                        "usage": result.get("usage", {}),
                        "model": result.get("model", "Неизвестно"),
                        "attempt": attempt
                    }
                else:
                    error_text = await response.text()
                    error_msg = error_text[:100] + "..." if len(error_text) > 100 else error_text
                    
                    # Если 429 (rate limit), ждем и пробуем снова
                    if response.status == 429 and attempt < max_retries:
                        print(f"      ⏳ Rate limit (429), ждем {timeout} сек...")
                        await asyncio.sleep(timeout)
                        continue
                    else:
                        return {
                            "status": f"❌ ОШИБКА {response.status}",
                            "error": error_msg,
                            "attempt": attempt
                        }
                        
        except asyncio.TimeoutError:
            print(f"      ⏰ Таймаут, попытка {attempt}")
            if attempt < max_retries:
                await asyncio.sleep(timeout)
                continue
            else:
                return {
                    "status": "💥 ТАЙМАУТ",
                    "error": "Превышено время ожидания",
                    "attempt": attempt
                }
        except Exception as e:
            print(f"      💥 Исключение: {str(e)[:50]}")
            if attempt < max_retries:
                await asyncio.sleep(timeout)
                continue
            else:
                return {
                    "status": "💥 ИСКЛЮЧЕНИЕ",
                    "error": str(e),
                    "attempt": attempt
                }
    
    return {
        "status": "❌ ВСЕ ПОПЫТКИ ИСЧЕРПАНЫ",
        "error": f"Не удалось после {max_retries} попыток",
        "attempt": max_retries
    }

async def test_all_keys():
    """Тестирует все ключи на бесплатной модели с ретраями"""
    print("🔍 ТЕСТ ВСЕХ КЛЮЧЕЙ OPENROUTER НА БЕСПЛАТНОЙ МОДЕЛИ С РЕТРАЯМИ")
    print("=" * 80)
    print(f"🤖 Модель: deepseek/deepseek-r1-0528:free")
    print(f"🔄 Ретраи: 5 попыток")
    print(f"⏰ Таймаут: 3 секунды")
    print(f"📅 Время: {datetime.now()}")
    print()
    
    working_keys = []
    failed_keys = []
    
    async with aiohttp.ClientSession() as session:
        for key_name, api_key in KEYS.items():
            print(f"🧪 Тестирую {key_name}...")
            result = await test_key_with_retries(session, key_name, api_key)
            
            print(f"   {result['status']}")
            if "РАБОТАЕТ" in result['status']:
                print(f"   📝 Ответ: {result['response']}")
                print(f"   🤖 Модель: {result['model']}")
                print(f"   🎯 Попытка: {result['attempt']}")
                if result.get('usage'):
                    usage = result['usage']
                    print(f"   📊 Токены: {usage.get('prompt_tokens', 0)} + {usage.get('completion_tokens', 0)}")
                working_keys.append((key_name, result))
            else:
                print(f"   🚫 Ошибка: {result.get('error', 'Неизвестно')}")
                print(f"   🎯 Попытка: {result['attempt']}")
                failed_keys.append((key_name, result))
            print()
    
    # Итоговый отчет
    print("📊 ИТОГОВЫЙ ОТЧЕТ")
    print("=" * 80)
    print(f"✅ Рабочих ключей: {len(working_keys)}")
    print(f"❌ Нерабочих ключей: {len(failed_keys)}")
    print()
    
    if working_keys:
        print("✅ РАБОЧИЕ КЛЮЧИ (на бесплатной модели):")
        for key_name, result in working_keys:
            print(f"   {key_name}: {KEYS[key_name]}")
            print(f"      Попытка: {result['attempt']}, Ответ: {result['response']}")
        print()
        
        # Рекомендации для .env
        print("📝 РЕКОМЕНДАЦИИ ДЛЯ .env:")
        print("=" * 80)
        for i, (key_name, result) in enumerate(working_keys[:3], 1):  # Берем первые 3 рабочих
            print(f"OPENROUTER_API_KEY{i}={KEYS[key_name]}")
        print()
        
        if len(working_keys) > 3:
            print(f"📋 Остальные рабочие ключи ({len(working_keys)-3}):")
            for key_name, result in working_keys[3:]:
                print(f"   {key_name}: {KEYS[key_name]} (попытка {result['attempt']})")
    
    if failed_keys:
        print("❌ НЕРАБОЧИЕ КЛЮЧИ:")
        for key_name, result in failed_keys:
            print(f"   {key_name}: {KEYS[key_name]}")
            print(f"      Ошибка: {result.get('error', 'Неизвестно')} (попытка {result['attempt']})")
    
    return working_keys, failed_keys

if __name__ == "__main__":
    asyncio.run(test_all_keys()) 