#!/usr/bin/env python3
"""
Тест исправления технических индикаторов
"""

import asyncio
from comprehensive_data_manager import comprehensive_data_manager

async def test_technical_indicators():
    """Тест технических индикаторов"""
    print("🔧 Тест исправления технических индикаторов")
    print("=" * 50)
    
    try:
        # Запускаем менеджер данных
        print("🚀 Запуск менеджера данных...")
        await comprehensive_data_manager.start()
        
        # Подписываемся на ETHUSDT
        print("📡 Подписка на ETHUSDT...")
        await comprehensive_data_manager.subscribe_multiple_symbols(["ETHUSDT"])
        
        # Ждем немного для загрузки данных
        print("⏳ Ожидание загрузки данных...")
        await asyncio.sleep(5)
        
        # Принудительно загружаем исторические данные
        print("📊 Принудительная загрузка исторических данных...")
        await comprehensive_data_manager._load_historical_data_for_symbol("ETHUSDT")
        
        # Ждем еще немного
        await asyncio.sleep(2)
        
        # Проверяем технические индикаторы для 1m (которые точно есть)
        print("📊 Проверка технических индикаторов для 1m...")
        indicators_1m = comprehensive_data_manager.get_technical_indicators("ETHUSDT", "1m")
        
        if indicators_1m:
            print("✅ Технические индикаторы для 1m получены!")
            print(f"   RSI: {indicators_1m.rsi_14:.2f}")
            print(f"   SMA 20: {indicators_1m.sma_20:.2f}")
            print(f"   EMA 12: {indicators_1m.ema_12:.2f}")
            print(f"   MACD: {indicators_1m.macd}")
            print(f"   Bollinger: {indicators_1m.bollinger}")
            print(f"   ATR: {indicators_1m.atr_14:.2f}")
            print(f"   Volume SMA: {indicators_1m.volume_sma:.2f}")
        else:
            print("❌ Технические индикаторы для 1m не получены")
        
        # Проверяем технические индикаторы для 1h
        print("📊 Проверка технических индикаторов для 1h...")
        indicators_1h = comprehensive_data_manager.get_technical_indicators("ETHUSDT", "1h")
        
        if indicators_1h:
            print("✅ Технические индикаторы для 1h получены!")
            print(f"   RSI: {indicators_1h.rsi_14:.2f}")
            print(f"   SMA 20: {indicators_1h.sma_20:.2f}")
            print(f"   EMA 12: {indicators_1h.ema_12:.2f}")
            print(f"   MACD: {indicators_1h.macd}")
            print(f"   Bollinger: {indicators_1h.bollinger}")
            print(f"   ATR: {indicators_1h.atr_14:.2f}")
            print(f"   Volume SMA: {indicators_1h.volume_sma:.2f}")
        else:
            print("❌ Технические индикаторы для 1h не получены")
            
            # Проверяем кэш свечей
            print("🔍 Детальная диагностика кэша:")
            for key, klines in comprehensive_data_manager.kline_cache.items():
                print(f"   Ключ {key}: {len(klines)} свечей")
            
            # Проверяем мультитаймфрейм кэш
            multitimeframe = comprehensive_data_manager.get_multitimeframe_data("ETHUSDT")
            if multitimeframe:
                print(f"   Мультитаймфрейм кэш: {len(multitimeframe.indicators)} индикаторов")
                for interval, indicators in multitimeframe.indicators.items():
                    print(f"     {interval}: RSI={indicators.rsi_14:.2f}, SMA={indicators.sma_20:.2f}")
            else:
                print("   Мультитаймфрейм кэш пуст")
        
        # Останавливаем менеджер
        print("🛑 Остановка менеджера данных...")
        await comprehensive_data_manager.stop()
        
        print("✅ Тест завершен!")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_technical_indicators()) 