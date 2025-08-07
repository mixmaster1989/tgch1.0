#!/usr/bin/env python3
"""
Тестовый скрипт для запуска активности бота
"""

import asyncio
from native_trader_bot import NativeTraderBot

async def test_activity():
    """Тестируем активность бота"""
    print("🚀 Запуск тестовой активности бота...")
    
    # Создаем экземпляр бота
    bot = NativeTraderBot()
    
    # Запускаем случайную активность
    print("📊 Запускаем случайную активность...")
    await bot.periodic_activity()
    
    print("✅ Активность завершена!")

if __name__ == "__main__":
    asyncio.run(test_activity()) 