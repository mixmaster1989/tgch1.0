#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отправки ответа балансировщика в Telegram
"""

import asyncio
from active_50_50_balancer import Active5050Balancer

async def test_telegram_response():
    """Тестируем отправку ответа балансировщика в Telegram"""
    print("🧪 ТЕСТИРОВАНИЕ ОТПРАВКИ ОТВЕТА БАЛАНСИРОВЩИКА В TELEGRAM")
    print("=" * 60)
    
    balancer = Active5050Balancer()
    
    # Тестируем сценарий разрешения покупки
    print("\n1️⃣ ТЕСТИРУЕМ РАЗРЕШЕНИЕ ПОКУПКИ:")
    print("   (Сбалансированные пропорции)")
    
    # Симулируем сбалансированный портфель
    def mock_portfolio_balanced():
        return {
            'alts_value': 500.0,      # 50% от портфеля
            'btceth_value': 500.0,    # 50% от портфеля
            'btceth_value_usdt': 500.0,
            'total_value': 1000.0,
            'usdc_usdt_rate': 1.0
        }
    
    balancer.get_portfolio_values = mock_portfolio_balanced
    
    permission = balancer.check_purchase_permission(50.0, "ALTS")
    
    print(f"   📊 Альты: 50.0% (сбалансировано)")
    print(f"   📊 BTC/ETH: 50.0%")
    print(f"   ✅ Разрешено: {permission['allowed']}")
    print(f"   📝 Причина: {permission['reason']}")
    print("   �� Уведомление должно быть отправлено в Telegram")
    
    # Тестируем сценарий блокировки покупки
    print("\n2️⃣ ТЕСТИРУЕМ БЛОКИРОВКУ ПОКУПКИ:")
    print("   (Перевес альтов)")
    
    # Симулируем перевес альтов
    def mock_portfolio_alts_overweight():
        return {
            'alts_value': 600.0,      # 60% от портфеля
            'btceth_value': 400.0,    # 40% от портфеля
            'btceth_value_usdt': 400.0,
            'total_value': 1000.0,
            'usdc_usdt_rate': 1.0
        }
    
    balancer.get_portfolio_values = mock_portfolio_alts_overweight
    
    permission = balancer.check_purchase_permission(50.0, "ALTS")
    
    print(f"   📊 Альты: 60.0% (перевес!)")
    print(f"   📊 BTC/ETH: 40.0%")
    print(f"   🚫 Разрешено: {permission['allowed']}")
    print(f"   📝 Причина: {permission['reason']}")
    print("   📱 Уведомление о блокировке должно быть отправлено в Telegram")
    
    print("\n" + "=" * 60)
    print("✅ ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("\n📋 ПРОВЕРЬТЕ TELEGRAM:")
    print("   • Должно прийти 2 уведомления от балансировщика")
    print("   • Первое: разрешение покупки (сбалансированные пропорции)")
    print("   • Второе: блокировка покупки (перевес альтов)")
    print("   • В каждом уведомлении должны быть текущие пропорции портфеля")

if __name__ == "__main__":
    asyncio.run(test_telegram_response())
