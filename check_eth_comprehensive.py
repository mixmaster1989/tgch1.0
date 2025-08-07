#!/usr/bin/env python3
"""
Проверка всех данных ETH из ComprehensiveDataManager
"""

import asyncio
import signal
import sys
from datetime import datetime
from comprehensive_data_manager import ComprehensiveDataManager

class TimeoutError(Exception):
    """Исключение для таймаута"""
    pass

async def check_eth_comprehensive(max_iterations: int = 10, data_collection_time: int = 15, timeout: int = 60):
    """
    Проверка всех данных ETH из комплексного менеджера
    
    Args:
        max_iterations: Максимальное количество итераций сбора данных
        data_collection_time: Время сбора данных в секундах
        timeout: Общий таймаут выполнения в секундах
    """
    data_manager = None
    callback_count = 0  # Счетчик callback'ов
    
    def timeout_handler():
        """Обработчик таймаута"""
        print(f"\n⏰ ТАЙМАУТ: Превышено время выполнения ({timeout} сек)")
        print(f"📊 Всего получено callback'ов: {callback_count}")
        # Не создаем дополнительную задачу остановки, так как она уже будет вызвана в finally
    
    try:
        print("🔍 ПРОВЕРКА ВСЕХ ДАННЫХ ETH")
        print("=" * 60)
        print(f"Время: {datetime.now()}")
        print(f"Максимум итераций: {max_iterations}")
        print(f"Время сбора данных: {data_collection_time} сек")
        print(f"Общий таймаут: {timeout} сек")
        print()
        
        # Устанавливаем таймаут
        timer = asyncio.create_task(asyncio.sleep(timeout))
        timer.add_done_callback(lambda _: timeout_handler())
        
        # Создаем менеджер данных
        data_manager = ComprehensiveDataManager()
        
        # Запускаем менеджер
        print("🚀 Запуск менеджера данных...")
        await data_manager.start()
        
        # Подписываемся только на ETH
        print("📡 Подписка на ETHUSDT...")
        await data_manager.subscribe_multiple_symbols(["ETHUSDT"])
        
        # Ждем немного для сбора данных
        print(f"⏳ Сбор данных ETH ({data_collection_time} секунд)...")
        print("   (Callback'ы будут выводиться в реальном времени)")
        
        # Создаем задачу для мониторинга callback'ов
        async def monitor_callbacks():
            nonlocal callback_count
            while data_manager and data_manager.is_running:
                await asyncio.sleep(1)
                # Здесь можно добавить логику подсчета callback'ов
                # Пока просто ждем
        
        monitor_task = asyncio.create_task(monitor_callbacks())
        
        await asyncio.sleep(data_collection_time)
        
        # Отменяем мониторинг
        monitor_task.cancel()
        
        # Отменяем таймаут
        timer.cancel()
        
        print(f"\n📊 Сбор данных завершен. Время: {datetime.now()}")
        
        # Проверяем рыночные данные
        print("\n📊 РЫНОЧНЫЕ ДАННЫЕ ETH:")
        print("-" * 40)
        market_data = data_manager.get_market_data("ETHUSDT")
        if market_data:
            print(f"   Цена: ${market_data.price:.2f}")
            print(f"   Изменение 24ч: {market_data.change_24h:.2f}%")
            print(f"   Объем 24ч: {market_data.volume_24h:.2f}")
            print(f"   Максимум 24ч: ${market_data.high_24h:.2f}")
            print(f"   Минимум 24ч: ${market_data.low_24h:.2f}")
        else:
            print("   ❌ Нет рыночных данных")
        
        # Проверяем технические индикаторы
        print("\n📈 ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ ETH:")
        print("-" * 40)
        indicators = data_manager.get_technical_indicators("ETHUSDT", "1m")
        if indicators:
            print(f"   RSI (14): {indicators.rsi_14:.2f}")
            print(f"   SMA (20): ${indicators.sma_20:.2f}")
            print(f"   EMA (12): ${indicators.ema_12:.2f}")
            print(f"   ATR (14): {indicators.atr_14:.4f}")
            print(f"   Volume SMA: {indicators.volume_sma:.2f}")
            
            # MACD
            if indicators.macd:
                if isinstance(indicators.macd, dict):
                    print(f"   MACD: {indicators.macd}")
                else:
                    print(f"   MACD: {indicators.macd:.4f}")
            else:
                print("   MACD: Нет данных")
            
            # Bollinger Bands
            if indicators.bollinger:
                print(f"   Bollinger: {indicators.bollinger}")
            else:
                print("   Bollinger: Нет данных")
        else:
            print("   ❌ Нет технических индикаторов")
        
        # Проверяем ордербук
        print("\n📚 ORDER BOOK ETH:")
        print("-" * 40)
        orderbook = data_manager.get_orderbook_data("ETHUSDT")
        if orderbook:
            print(f"   Спред: ${orderbook.spread:.4f} ({orderbook.spread_percent:.4f}%)")
            print(f"   Bid объем: {orderbook.bid_volume:.2f}")
            print(f"   Ask объем: {orderbook.ask_volume:.2f}")
            print(f"   Соотношение: {orderbook.volume_ratio:.2f}")
            print(f"   Ликвидность: {orderbook.liquidity_score:.2f}")
            
            if orderbook.bids and orderbook.asks:
                print(f"   Лучшая покупка: ${orderbook.bids[0][0]:.2f} ({orderbook.bids[0][1]:.4f})")
                print(f"   Лучшая продажа: ${orderbook.asks[0][0]:.2f} ({orderbook.asks[0][1]:.4f})")
                
                # Показываем топ-5 уровней
                print("\n   Топ-5 покупок:")
                for i, bid in enumerate(orderbook.bids[:5]):
                    print(f"     {i+1}. ${bid[0]:.2f} - {bid[1]:.4f}")
                
                print("\n   Топ-5 продаж:")
                for i, ask in enumerate(orderbook.asks[:5]):
                    print(f"     {i+1}. ${ask[0]:.2f} - {ask[1]:.4f}")
        else:
            print("   ❌ Нет данных ордербука")
        
        # Проверяем историю сделок
        print("\n💱 ИСТОРИЯ СДЕЛОК ETH:")
        print("-" * 40)
        trade_history = data_manager.get_trade_history("ETHUSDT")
        if trade_history:
            print(f"   Покупки: {trade_history.buy_volume:.4f}")
            print(f"   Продажи: {trade_history.sell_volume:.4f}")
            print(f"   Соотношение: {trade_history.volume_ratio:.2f}")
            print(f"   Средний размер: {trade_history.avg_trade_size:.4f}")
            print(f"   Количество сделок: {len(trade_history.trades)}")
            
            # Показываем последние 5 сделок
            if trade_history.trades:
                print("\n   Последние 5 сделок:")
                for i, trade in enumerate(trade_history.trades[-5:]):
                    side_emoji = "🟢" if trade.get('side') == 'BUY' else "🔴"
                    print(f"     {side_emoji} ${trade.get('price', 0):.2f} - {trade.get('quantity', 0):.4f}")
        else:
            print("   ❌ Нет истории сделок")
        
        # Проверяем корреляции
        print("\n🔗 КОРРЕЛЯЦИИ ETH:")
        print("-" * 40)
        correlations = data_manager.get_correlation_data("ETHUSDT")
        if correlations:
            print(f"   BTC корреляция: {correlations.get('btc_correlation', 0):.4f}")
            print(f"   ETH корреляция: {correlations.get('eth_correlation', 0):.4f}")
            print(f"   Ранг волатильности: {correlations.get('volatility_rank', 0)}")
            print(f"   Сила корреляции: {correlations.get('correlation_strength', 'unknown')}")
        else:
            print("   ❌ Нет корреляционных данных")
        
        # Проверяем новости
        print("\n📰 НОВОСТИ ETH:")
        print("-" * 40)
        news_data = data_manager.get_news_data("ETHUSDT")
        if news_data:
            print(f"   Настроения: {news_data.get('sentiment', 'unknown')}")
            print(f"   Влияние: {news_data.get('impact_score', 0):.2f}")
            print(f"   Количество новостей: {len(news_data.get('news', []))}")
        else:
            print("   ❌ Нет новостных данных")
        
        # Проверяем мультитаймфрейм данные
        print("\n⏰ МУЛЬТИТАЙМФРЕЙМ ДАННЫЕ ETH:")
        print("-" * 40)
        multitimeframe = data_manager.get_multitimeframe_data("ETHUSDT")
        if multitimeframe:
            print(f"   Доступные таймфреймы: {list(multitimeframe.timeframes.keys())}")
            print(f"   Доступные индикаторы: {list(multitimeframe.indicators.keys())}")
        else:
            print("   ❌ Нет мультитаймфрейм данных")
        
        print("\n" + "=" * 60)
        print("✅ Проверка ETH завершена!")
        
        # Останавливаем менеджер
        print("🛑 Остановка менеджера данных...")
        await data_manager.stop()
        print("✅ Менеджер данных остановлен")
        
    except asyncio.CancelledError:
        print("\n⏹️ Скрипт отменен")
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        
        # В случае ошибки тоже останавливаем менеджер
        try:
            if data_manager:
                await data_manager.stop()
        except:
            pass

def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    print(f"\n🛑 Получен сигнал {signum}, завершение...")
    sys.exit(0)

if __name__ == "__main__":
    # Устанавливаем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Запускаем с ограничением итераций и таймаутом
    asyncio.run(check_eth_comprehensive(
        max_iterations=5, 
        data_collection_time=15,  # Увеличиваем время сбора данных
        timeout=90  # Увеличиваем таймаут до 90 секунд
    )) 