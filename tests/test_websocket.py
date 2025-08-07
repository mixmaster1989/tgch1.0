#!/usr/bin/env python3
"""
Тест MEX WebSocket API
"""

import sys
import os
import asyncio
import json

# Добавляем корневую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mex_websocket import MarketDataStream

async def test_websocket_connection():
    """Тест подключения к WebSocket"""
    print("🔌 Тестирую подключение к MEX WebSocket...")
    
    stream = MarketDataStream()
    
    try:
        # Запускаем WebSocket
        await stream.start()
        print("✅ WebSocket подключен")
        
        # Подписываемся на BTC тикер
        print("📡 Подписка на BTCUSDT тикер...")
        await stream.start_ticker_stream(['BTCUSDT'])
        
        # Ждем данные 30 секунд
        print("⏳ Ожидание данных (30 секунд)...")
        await asyncio.sleep(30)
        
        # Проверяем полученные данные
        btc_price = stream.get_price('BTCUSDT')
        if btc_price:
            print(f"✅ Получена цена BTC: ${btc_price:,.2f}")
        else:
            print("❌ Цена BTC не получена")
        
        # Получаем все цены
        all_prices = stream.get_all_prices()
        print(f"📊 Всего получено цен: {len(all_prices)}")
        
        # Останавливаем WebSocket
        await stream.stop()
        print("✅ WebSocket отключен")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка WebSocket: {e}")
        await stream.stop()
        return False

async def test_multiple_streams():
    """Тест множественных потоков данных"""
    print("\n🔄 Тестирую множественные потоки...")
    
    stream = MarketDataStream()
    
    try:
        await stream.start()
        print("✅ WebSocket подключен")
        
        # Подписываемся на несколько потоков
        symbols = ['BTCUSDT', 'ETHUSDT']
        
        print(f"📡 Подписка на тикеры: {symbols}")
        await stream.start_ticker_stream(symbols)
        
        print("📡 Подписка на свечи BTC 1m")
        await stream.start_kline_stream('BTCUSDT', '1m')
        
        print("📡 Подписка на стакан BTC")
        await stream.start_depth_stream('BTCUSDT')
        
        # Ждем данные
        print("⏳ Ожидание данных (20 секунд)...")
        await asyncio.sleep(20)
        
        # Проверяем данные
        print("\n📊 Полученные данные:")
        
        for symbol in symbols:
            price = stream.get_price(symbol)
            if price:
                print(f"  {symbol}: ${price:,.2f}")
        
        btc_kline = stream.get_kline('BTCUSDT')
        if btc_kline:
            print(f"  BTC свеча: ${btc_kline['close']:,.2f}")
        
        btc_depth = stream.get_depth('BTCUSDT')
        if btc_depth:
            print(f"  BTC стакан: {len(btc_depth['bids'])} bids, {len(btc_depth['asks'])} asks")
        
        await stream.stop()
        print("✅ Тест завершен")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        await stream.stop()
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 ТЕСТ MEX WEBSOCKET API")
    print("=" * 50)
    
    # Тест 1: Базовое подключение
    test1_ok = await test_websocket_connection()
    
    # Тест 2: Множественные потоки
    test2_ok = await test_multiple_streams()
    
    print("\n" + "=" * 50)
    print("РЕЗУЛЬТАТЫ ТЕСТОВ:")
    print(f"  Базовое подключение: {'✅ OK' if test1_ok else '❌ FAIL'}")
    print(f"  Множественные потоки: {'✅ OK' if test2_ok else '❌ FAIL'}")
    
    if test1_ok and test2_ok:
        print("\n🎉 Все тесты прошли успешно!")
        print("WebSocket готов к использованию в торговом боте")
    else:
        print("\n⚠️ Некоторые тесты не прошли")
        print("Проверьте подключение к интернету и доступность MEX API")

if __name__ == "__main__":
    asyncio.run(main()) 