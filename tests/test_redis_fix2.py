#!/usr/bin/env python3
"""
Тест исправления Redis в comprehensive_data_manager
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_data_manager import ComprehensiveDataManager

async def test_redis_fix():
    """Тест исправления Redis"""
    print("🔧 ТЕСТ REDIS В COMPREHENSIVE_DATA_MANAGER")
    print("=" * 40)
    
    try:
        manager = ComprehensiveDataManager()
        
        # Тест метода
        await manager._add_price_to_correlation_cache('BTCUSDT', 115000.0)
        await manager._add_price_to_correlation_cache('BTCUSDT', 115100.0)
        await manager._add_price_to_correlation_cache('BTCUSDT', 115200.0)
        
        print("✅ Redis методы работают!")
        return True
        
    except Exception as e:
        print(f"❌ Redis ошибка: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_redis_fix()) 