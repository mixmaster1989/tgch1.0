#!/usr/bin/env python3
"""
Тест Bollinger Bands в comprehensive_data_manager
"""

import asyncio
from comprehensive_data_manager import ComprehensiveDataManager

async def test_bollinger_bands():
    """Тест работы Bollinger Bands"""
    print("🔍 ТЕСТ BOLLINGER BANDS")
    print("=" * 40)
    
    data_manager = ComprehensiveDataManager()
    
    try:
        # Запускаем менеджер
        print("📡 Запуск менеджера данных...")
        await data_manager.start()
        
        # Ждем немного для накопления данных
        print("⏳ Ожидание накопления данных (30 секунд)...")
        await asyncio.sleep(30)
        
        # Проверяем технические индикаторы для ETH
        print("\n📊 ПРОВЕРКА ТЕХНИЧЕСКИХ ИНДИКАТОРОВ ETH:")
        print("-" * 40)
        
        indicators = data_manager.get_technical_indicators('ETHUSDT', '1m')
        
        if indicators:
            print(f"✅ Индикаторы получены для ETHUSDT")
            print(f"   RSI: {indicators.rsi_14:.2f}")
            print(f"   SMA 20: {indicators.sma_20:.2f}")
            print(f"   EMA 12: {indicators.ema_12:.2f}")
            print(f"   ATR 14: {indicators.atr_14:.2f}")
            print(f"   Volume SMA: {indicators.volume_sma:.2f}")
            
            # Проверяем Bollinger Bands
            if indicators.bollinger:
                bb = indicators.bollinger
                print(f"\n📏 BOLLINGER BANDS:")
                print(f"   Upper: ${bb.get('upper', 0):.2f}")
                print(f"   Middle: ${bb.get('middle', 0):.2f}")
                print(f"   Lower: ${bb.get('lower', 0):.2f}")
                
                # Проверяем позицию цены
                current_price = 3700.0  # Примерная цена ETH
                if bb.get('upper', 0) > 0 and bb.get('lower', 0) > 0:
                    if current_price >= bb.get('upper', 0):
                        position = "🔴 Верхняя полоса (сопротивление)"
                    elif current_price <= bb.get('lower', 0):
                        position = "🟢 Нижняя полоса (поддержка)"
                    else:
                        position = "🟡 Между полосами"
                    
                    print(f"   Позиция цены: {position}")
                else:
                    print("   ⚠️ Bollinger Bands не рассчитаны")
            else:
                print("   ❌ Bollinger Bands: нет данных")
            
            # Проверяем MACD
            if indicators.macd:
                macd = indicators.macd
                print(f"\n📈 MACD:")
                print(f"   MACD: {macd.get('macd', 0):.4f}")
                print(f"   Signal: {macd.get('signal', 0):.4f}")
                print(f"   Histogram: {macd.get('histogram', 0):.4f}")
            else:
                print("   ❌ MACD: нет данных")
                
        else:
            print("❌ Индикаторы не найдены")
        
        print("\n✅ ТЕСТ ЗАВЕРШЕН")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Останавливаем менеджер
        print("\n🛑 Остановка менеджера данных...")
        await data_manager.stop()

if __name__ == "__main__":
    asyncio.run(test_bollinger_bands())
