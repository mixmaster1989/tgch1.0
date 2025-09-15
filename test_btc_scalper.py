#!/usr/bin/env python3
"""
Тест BTC скальпера
"""

import asyncio
import time
from btc_scalper import BTCScalper

async def test_btc_scalper():
    """Тест BTC скальпера"""
    print("🧪 ТЕСТ BTC СКАЛЬПЕРА")
    print("=" * 50)
    
    # Создаем скальпер
    scalper = BTCScalper()
    
    # Получаем текущую цену BTC
    print("📊 Получение текущей цены BTC...")
    current_price = scalper.get_current_price()
    if current_price:
        print(f"💰 Текущая цена BTC: ${current_price:.2f}")
    else:
        print("❌ Не удалось получить цену BTC")
        return
    
    # Получаем технический анализ
    print("\n📈 Получение технического анализа...")
    tech_analysis = scalper.get_technical_analysis()
    if tech_analysis:
        print("✅ Технический анализ получен:")
        print(f"   RSI (14): {tech_analysis.get('rsi_14', 'N/A'):.2f}")
        print(f"   SMA (20): ${tech_analysis.get('sma_20', 'N/A'):.2f}")
        print(f"   EMA (12): ${tech_analysis.get('ema_12', 'N/A'):.2f}")
        
        macd = tech_analysis.get('macd', {})
        if macd:
            print(f"   MACD Histogram: {macd.get('histogram', 'N/A'):.4f}")
        
        print(f"   Volume Ratio: {tech_analysis.get('volume_ratio', 'N/A'):.2f}")
    else:
        print("❌ Не удалось получить технический анализ")
        return
    
    # AI анализ убран для скорости
    print("\n🤖 AI анализ: УБРАН для скорости скальпинга")
    ai_analysis = None
    
    # Рассчитываем сигналы
    print("\n🎯 Расчет скальпинговых сигналов...")
    signals = scalper.calculate_scalping_signals(tech_analysis)
    print("✅ Сигналы рассчитаны:")
    print(f"   Действие: {signals['action']}")
    print(f"   Уверенность: {signals['confidence']:.1%}")
    print(f"   Причины: {', '.join(signals['reasons'])}")
    
    # Показываем статус
    print("\n📊 Статус скальпера:")
    status = scalper.get_status()
    print(f"   Работает: {'Да' if status['is_running'] else 'Нет'}")
    print(f"   Размер позиции: ${status['position_size_usdt']}")
    print(f"   Минимальная прибыль: ${status['min_profit_usdt']}")
    print(f"   Интервал сканирования: {status['scan_interval']} сек")
    print(f"   Всего сделок: {status['total_trades']}")
    print(f"   Общая прибыль: ${status['total_profit']:.4f}")
    
    # Тест отправки в Telegram
    print("\n📱 Тест отправки в Telegram...")
    test_message = "🧪 Тест BTC скальпера\n\nЭто тестовое сообщение от BTC скальпера."
    result = scalper.send_telegram_message(test_message)
    if result:
        print("✅ Сообщение отправлено в Telegram")
    else:
        print("❌ Ошибка отправки в Telegram")
    
    print("\n✅ Тест BTC скальпера завершен")

if __name__ == "__main__":
    asyncio.run(test_btc_scalper())
