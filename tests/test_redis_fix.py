#!/usr/bin/env python3
"""
Быстрый тест исправления Redis ошибки
"""

import asyncio
import redis.asyncio as redis

async def test_redis_fix():
    """Тест Redis методов"""
    print("🔧 ТЕСТ ИСПРАВЛЕНИЯ REDIS")
    print("=" * 30)
    
    try:
        # Подключение к Redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        
        # Тест методов
        key = "test:price_history:BTCUSDT"
        
        # Тест lpush
        await r.lpush(key, 115000.0)
        await r.lpush(key, 115100.0)
        await r.lpush(key, 115200.0)
        
        # Тест ltrim
        await r.ltrim(key, 0, 9)  # Оставить только 10 элементов
        
        # Тест expire
        await r.expire(key, 3600)
        
        # Проверка
        length = await r.llen(key)
        print(f"✅ Redis работает: {length} элементов в списке")
        
        # Очистка
        await r.delete(key)
        
        return True
        
    except Exception as e:
        print(f"❌ Redis ошибка: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_redis_fix()) 