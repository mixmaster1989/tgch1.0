#!/usr/bin/env python3
"""
Тест технических индикаторов и корреляционного анализа
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import numpy as np
from technical_indicators import calculate_indicators_for_symbol
from correlation_analyzer import CorrelationAnalyzer, add_price_to_correlation_analyzer
from comprehensive_data_manager import ComprehensiveDataManager


def test_technical_indicators():
    """Тест технических индикаторов"""
    print("🧪 Тестирование технических индикаторов...")
    
    # Создаем тестовые данные свечей (восходящий тренд с шумом)
    test_klines = []
    base_price = 45000
    base_time = int(time.time() * 1000)
    
    for i in range(100):
        # Создаем восходящий тренд с шумом
        trend = base_price + i * 10  # Восходящий тренд
        noise = np.random.normal(0, 100)  # Шум
        price = trend + noise
        
        # Создаем OHLCV данные
        open_price = price - np.random.uniform(0, 50)
        high_price = price + np.random.uniform(0, 100)
        low_price = price - np.random.uniform(0, 100)
        close_price = price
        volume = np.random.uniform(50, 500)
        
        timestamp = base_time + i * 60000  # Каждую минуту
        
        test_klines.append([
            timestamp,
            str(open_price),
            str(high_price),
            str(low_price),
            str(close_price),
            str(volume),
            timestamp + 60000,  # close_time
            str(volume * close_price)  # quote_volume
        ])
    
    # Тестируем расчет индикаторов
    result = calculate_indicators_for_symbol(test_klines, "BTCUSDT")
    
    print("📊 Результаты технических индикаторов:")
    rsi = result.get('rsi_14', 'N/A')
    sma = result.get('sma_20', 'N/A')
    ema = result.get('ema_12', 'N/A')
    atr = result.get('atr_14', 'N/A')
    vol_sma = result.get('volume_sma', 'N/A')
    
    print(f"  RSI: {rsi:.2f}" if isinstance(rsi, (int, float)) else f"  RSI: {rsi}")
    print(f"  SMA 20: {sma:.2f}" if isinstance(sma, (int, float)) else f"  SMA 20: {sma}")
    print(f"  EMA 12: {ema:.2f}" if isinstance(ema, (int, float)) else f"  EMA 12: {ema}")
    print(f"  ATR: {atr:.2f}" if isinstance(atr, (int, float)) else f"  ATR: {atr}")
    print(f"  Volume SMA: {vol_sma:.2f}" if isinstance(vol_sma, (int, float)) else f"  Volume SMA: {vol_sma}")
    
    if 'macd' in result:
        macd = result['macd']
        print(f"  MACD: {macd.get('macd', 'N/A'):.2f}")
        print(f"  Signal: {macd.get('signal', 'N/A'):.2f}")
        print(f"  Histogram: {macd.get('histogram', 'N/A'):.2f}")
    
    if 'bollinger' in result:
        bb = result['bollinger']
        print(f"  BB Upper: {bb.get('upper', 'N/A'):.2f}")
        print(f"  BB Middle: {bb.get('middle', 'N/A'):.2f}")
        print(f"  BB Lower: {bb.get('lower', 'N/A'):.2f}")
    
    if 'signals' in result:
        signals = result['signals']
        print(f"  Overall Signal: {signals.get('overall_signal', 'N/A')}")
        print(f"  Confidence: {signals.get('confidence', 'N/A'):.2f}")
        print(f"  Buy Signals: {signals.get('buy_signals', 'N/A')}")
        print(f"  Sell Signals: {signals.get('sell_signals', 'N/A')}")
    
    print("✅ Тест технических индикаторов завершен\n")


def test_correlation_analyzer():
    """Тест корреляционного анализатора"""
    print("🔗 Тестирование корреляционного анализатора...")
    
    analyzer = CorrelationAnalyzer()
    base_time = int(time.time() * 1000)
    
    # Добавляем тестовые данные для разных активов
    for i in range(100):
        timestamp = base_time + i * 60000  # Каждую минуту
        
        # BTC с восходящим трендом
        btc_price = 45000 + i * 10 + np.random.normal(0, 100)
        analyzer.add_price_data('BTCUSDT', btc_price, timestamp)
        
        # ETH с высокой корреляцией с BTC
        eth_price = 3000 + i * 0.7 + np.random.normal(0, 10)
        analyzer.add_price_data('ETHUSDT', eth_price, timestamp)
        
        # ADA с низкой корреляцией (синусоида)
        ada_price = 0.5 + np.sin(i * 0.1) * 0.1 + np.random.normal(0, 0.02)
        analyzer.add_price_data('ADAUSDT', ada_price, timestamp)
        
        # SOL с умеренной корреляцией
        sol_price = 100 + i * 0.5 + np.random.normal(0, 5)
        analyzer.add_price_data('SOLUSDT', sol_price, timestamp)
    
    # Тестируем расчет корреляций
    btc_corr = analyzer.calculate_correlations('BTCUSDT')
    eth_corr = analyzer.calculate_correlations('ETHUSDT')
    ada_corr = analyzer.calculate_correlations('ADAUSDT')
    
    print("📈 Результаты корреляционного анализа:")
    print(f"BTC корреляции:")
    for asset, corr in btc_corr.get('correlations', {}).items():
        print(f"  {asset}: {corr:.3f}")
    
    print(f"\nETH корреляции:")
    for asset, corr in eth_corr.get('correlations', {}).items():
        print(f"  {asset}: {corr:.3f}")
    
    print(f"\nADA корреляции:")
    for asset, corr in ada_corr.get('correlations', {}).items():
        print(f"  {asset}: {corr:.3f}")
    
    print(f"\nРанг волатильности:")
    print(f"  BTC: {btc_corr.get('volatility_rank', 'N/A')}")
    print(f"  ETH: {eth_corr.get('volatility_rank', 'N/A')}")
    print(f"  ADA: {ada_corr.get('volatility_rank', 'N/A')}")
    
    # Тестируем анализ портфеля
    portfolio = {
        'BTCUSDT': 0.4,
        'ETHUSDT': 0.3,
        'ADAUSDT': 0.2,
        'SOLUSDT': 0.1
    }
    
    portfolio_analysis = analyzer.get_portfolio_correlation(portfolio)
    print(f"\n📊 Анализ портфеля:")
    print(f"  Корреляция портфеля: {portfolio_analysis.get('portfolio_correlation', 'N/A'):.3f}")
    print(f"  Скор диверсификации: {portfolio_analysis.get('diversification_score', 'N/A'):.3f}")
    print(f"  Уровень риска: {portfolio_analysis.get('risk_level', 'N/A')}")
    print(f"  Рекомендация: {portfolio_analysis.get('recommendation', 'N/A')}")
    
    print("✅ Тест корреляционного анализатора завершен\n")


async def test_comprehensive_data_manager():
    """Тест комплексного менеджера данных"""
    print("🚀 Тестирование комплексного менеджера данных...")
    
    manager = ComprehensiveDataManager()
    
    # Callback для технических индикаторов
    async def indicators_callback(data):
        print(f"📊 Обновление индикаторов: {len(data)} символов")
        for symbol, multidata in data.items():
            if '1h' in multidata.indicators:
                indicators = multidata.indicators['1h']
                print(f"  {symbol}: RSI={indicators.rsi_14:.2f}, Signal={indicators.signals.get('overall_signal', 'N/A')}")
    
    # Подписываемся на обновления
    manager.subscribe_indicators_updates(indicators_callback)
    
    try:
        # Запускаем менеджер
        await manager.start()
        
        # Ждем для накопления данных для корреляций (нужно минимум 10 точек)
        print("⏳ Сбор данных для корреляций...")
        await asyncio.sleep(60)  # Увеличиваем время для накопления данных
        
        # Получаем данные
        btc_data = manager.get_multitimeframe_data('BTCUSDT')
        if btc_data:
            print(f"📈 Данные BTC:")
            print(f"  Таймфреймы: {list(btc_data.timeframes.keys())}")
            print(f"  Индикаторы: {list(btc_data.indicators.keys())}")
            
            if '1h' in btc_data.indicators:
                indicators = btc_data.indicators['1h']
                print(f"  1h RSI: {indicators.rsi_14:.2f}")
                print(f"  1h Signal: {indicators.signals.get('overall_signal', 'N/A')}")
        
        # Получаем корреляции
        btc_corr = manager.get_correlation_data('BTCUSDT')
        if btc_corr:
            print(f"🔗 Корреляции BTC:")
            for asset, corr in btc_corr.get('correlations', {}).items():
                print(f"  {asset}: {corr:.3f}")
        
        # Получаем кандидатов для торговли
        candidates = manager.get_trading_candidates(min_volume=100000)
        print(f"🎯 Кандидаты для торговли: {len(candidates)} символов")
        for i, candidate in enumerate(candidates[:5]):
            print(f"  {i+1}. {candidate['symbol']}: ${candidate['price']:.4f}, Score: {candidate['score']:.2f}")
        
    except Exception as e:
        print(f"❌ Ошибка в тесте: {e}")
    
    finally:
        # Останавливаем менеджер
        await manager.stop()
    
    print("✅ Тест комплексного менеджера данных завершен\n")


if __name__ == "__main__":
    import asyncio
    
    print("🧪 Запуск тестов технического анализа...\n")
    
    # Тест технических индикаторов
    test_technical_indicators()
    
    # Тест корреляционного анализатора
    test_correlation_analyzer()
    
    # Тест комплексного менеджера данных
    asyncio.run(test_comprehensive_data_manager())
    
    print("🎉 Все тесты завершены!") 