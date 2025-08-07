#!/usr/bin/env python3
"""
Проверка всех данных из ComprehensiveDataManager
"""

import asyncio
from datetime import datetime
from comprehensive_data_manager import ComprehensiveDataManager

async def check_comprehensive_data():
    """Проверка всех данных из комплексного менеджера"""
    try:
        print("🔍 ПРОВЕРКА COMPREHENSIVE DATA MANAGER")
        print("=" * 60)
        print(f"Время: {datetime.now()}")
        print()
        
        # Создаем менеджер данных
        data_manager = ComprehensiveDataManager()
        
        # Запускаем менеджер
        print("🚀 Запуск менеджера данных...")
        await data_manager.start()
        
        # Подписываемся на символы для активации корреляций
        print("📡 Подписка на символы...")
        await data_manager.subscribe_multiple_symbols(["ETHUSDT", "BTCUSDT", "ADAUSDT"])
        
        # Ждем немного для сбора данных
        print("⏳ Сбор данных (10 секунд)...")
        await asyncio.sleep(10)
        
        # Проверяем рыночные данные
        print("\n📊 РЫНОЧНЫЕ ДАННЫЕ:")
        print("-" * 30)
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
        print("\n📈 ТЕХНИЧЕСКИЕ ИНДИКАТОРЫ:")
        print("-" * 30)
        indicators = data_manager.get_technical_indicators("ETHUSDT", "1m")
        if indicators:
            print(f"   RSI (14): {indicators.rsi_14:.2f}")
            print(f"   SMA (20): ${indicators.sma_20:.2f}")
            print(f"   EMA (12): ${indicators.ema_12:.2f}")
            print(f"   ATR (14): {indicators.atr_14:.4f}")
            print(f"   Volume SMA: {indicators.volume_sma:.2f}")
            
            # MACD
            if indicators.macd:
                macd_line = indicators.macd.get('macd', 0)
                signal_line = indicators.macd.get('signal', 0)
                histogram = indicators.macd.get('histogram', 0)
                print(f"   MACD: {macd_line:.4f}")
                print(f"   Signal: {signal_line:.4f}")
                print(f"   Histogram: {histogram:.4f}")
            
            # Bollinger Bands
            if indicators.bollinger:
                upper = indicators.bollinger.get('upper', 0)
                middle = indicators.bollinger.get('middle', 0)
                lower = indicators.bollinger.get('lower', 0)
                print(f"   Bollinger Upper: ${upper:.2f}")
                print(f"   Bollinger Middle: ${middle:.2f}")
                print(f"   Bollinger Lower: ${lower:.2f}")
        else:
            print("   ❌ Нет технических индикаторов")
        
        # Проверяем ордербук
        print("\n📚 ORDER BOOK:")
        print("-" * 30)
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
        else:
            print("   ❌ Нет данных ордербука")
        
        # Проверяем историю сделок
        print("\n💱 ИСТОРИЯ СДЕЛОК:")
        print("-" * 30)
        trade_history = data_manager.get_trade_history("ETHUSDT")
        if trade_history:
            print(f"   Покупки: {trade_history.buy_volume:.4f}")
            print(f"   Продажи: {trade_history.sell_volume:.4f}")
            print(f"   Соотношение: {trade_history.volume_ratio:.2f}")
            print(f"   Средний размер: {trade_history.avg_trade_size:.4f}")
            print(f"   Количество сделок: {len(trade_history.trades)}")
        else:
            print("   ❌ Нет истории сделок")
        
        # Проверяем корреляции
        print("\n🔗 КОРРЕЛЯЦИИ:")
        print("-" * 30)
        correlations = data_manager.get_correlation_data("ETHUSDT")
        if correlations:
            # Извлекаем данные из правильной структуры
            btc_corr = 0.0
            if 'market_regime' in correlations:
                btc_corr = correlations['market_regime'].get('btc_correlation', 0.0)
            
            volatility_rank = 0
            if 'volatility_analysis' in correlations:
                volatility_rank = correlations['volatility_analysis'].get('volatility_rank', 0)
            
            correlation_strength = 'unknown'
            if 'basic_correlations' in correlations and 'BTCUSDT' in correlations['basic_correlations']:
                correlation_strength = correlations['basic_correlations']['BTCUSDT'].get('strength', 'unknown')
            
            print(f"   BTC корреляция: {btc_corr:.4f}")
            print(f"   Ранг волатильности: {volatility_rank}")
            print(f"   Сила корреляции: {correlation_strength}")
            
            # Дополнительная информация
            if 'market_regime' in correlations:
                regime = correlations['market_regime'].get('regime', 'unknown')
                print(f"   Рыночный режим: {regime}")
            
            if 'portfolio_recommendations' in correlations:
                recommendations = correlations['portfolio_recommendations']
                if recommendations:
                    print(f"   Рекомендации: {recommendations[0]}")
        else:
            print("   ❌ Нет корреляционных данных")
        
        # Проверяем новости
        print("\n📰 НОВОСТИ:")
        print("-" * 30)
        news_data = data_manager.get_news_data("ETHUSDT")
        if news_data:
            print(f"   Настроения: {news_data.get('sentiment', 'unknown')}")
            print(f"   Влияние: {news_data.get('impact_score', 0):.2f}")
            print(f"   Количество новостей: {len(news_data.get('news', []))}")
        else:
            print("   ❌ Нет новостных данных")
        
        # Проверяем кандидатов для торговли
        print("\n🎯 КАНДИДАТЫ ДЛЯ ТОРГОВЛИ:")
        print("-" * 30)
        candidates = data_manager.get_trading_candidates()
        if candidates:
            print(f"   Найдено кандидатов: {len(candidates)}")
            for i, candidate in enumerate(candidates[:5]):
                print(f"   {i+1}. {candidate['symbol']}: ${candidate['price']:.4f} (score: {candidate['score']:.2f})")
        else:
            print("   ❌ Нет кандидатов для торговли")
        
        print("\n" + "=" * 60)
        print("✅ Проверка завершена!")
        
        # Останавливаем менеджер
        await data_manager.stop()
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check_comprehensive_data()) 