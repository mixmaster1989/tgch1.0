#!/usr/bin/env python3
"""
Скрипт для проверки цены ETH и анализа торговых сигналов
"""

import json
from datetime import datetime
from mex_api import MexAPI
from technical_indicators import TechnicalIndicators

def check_eth_analysis():
    """Проверка цены ETH и технических индикаторов"""
    try:
        print("🔍 АНАЛИЗ ETHUSDT")
        print("=" * 50)
        print(f"Время: {datetime.now()}")
        print()
        
        # Создаем API клиент
        api = MexAPI()
        
        # Получаем текущую цену ETH
        print("📊 Получение цены ETH...")
        ticker = api.get_ticker_price("ETHUSDT")
        current_price = float(ticker['price'])
        print(f"💰 Текущая цена ETH: ${current_price:.2f}")
        print()
        
        # Получаем данные свечей для анализа
        print("📈 Получение исторических данных...")
        klines = api.get_klines("ETHUSDT", interval='1m', limit=100)
        
        if not klines or 'code' in klines:
            print("❌ Не удалось получить данные свечей")
            if 'msg' in klines:
                print(f"   Ошибка: {klines['msg']}")
            return
        
        # Получаем данные из правильной структуры
        if isinstance(klines, dict) and 'data' in klines:
            klines_data = klines['data']
        else:
            klines_data = klines
        
        # Конвертируем данные
        closes = []
        highs = []
        lows = []
        volumes = []
        
        for k in klines_data:
            if len(k) >= 6:  # Проверяем, что есть достаточно элементов
                closes.append(float(k[4]))  # Цена закрытия
                highs.append(float(k[2]))   # Максимум
                lows.append(float(k[3]))    # Минимум
                volumes.append(float(k[5])) # Объем
        
        print(f"📊 Получено {len(closes)} свечей")
        print()
        
        # Рассчитываем технические индикаторы
        print("🔢 Расчет технических индикаторов...")
        indicators = TechnicalIndicators()
        
        # Подготавливаем данные в правильном формате
        klines_formatted = []
        for i in range(len(closes)):
            klines_formatted.append([
                int(datetime.now().timestamp() * 1000) - (len(closes) - i) * 60000,  # timestamp
                closes[i],  # open (используем close как приближение)
                highs[i],   # high
                lows[i],    # low
                closes[i],  # close
                volumes[i]  # volume
            ])
        
        # Рассчитываем все индикаторы
        all_indicators = indicators.calculate_all_indicators(klines_formatted, "ETHUSDT")
        
        if all_indicators:
            rsi_14 = all_indicators.get('rsi_14', 50)
            macd_histogram = all_indicators.get('macd', {}).get('histogram', 0)
            sma_20 = all_indicators.get('sma_20', current_price)
            ema_12 = all_indicators.get('ema_12', current_price)
            
            print(f"📊 RSI (14): {rsi_14:.2f}")
            print(f"📈 MACD Histogram: {macd_histogram:.4f}")
            print(f"📊 SMA (20): ${sma_20:.2f}")
            print(f"📊 EMA (12): ${ema_12:.2f}")
        else:
            print("❌ Не удалось рассчитать индикаторы")
            rsi_14 = 50
            macd_histogram = 0
            sma_20 = current_price
            ema_12 = current_price
        
        print()
        
        # Анализируем сигналы
        print("🎯 АНАЛИЗ ТОРГОВЫХ СИГНАЛОВ:")
        print("-" * 30)
        
        buy_signals = 0
        sell_signals = 0
        
        # RSI сигналы
        if rsi_14 < 30:
            print("🟢 RSI: Сигнал покупки (перепроданность)")
            buy_signals += 1
        elif rsi_14 > 70:
            print("🔴 RSI: Сигнал продажи (перекупленность)")
            sell_signals += 1
        else:
            print(f"🟡 RSI: Нейтрально ({rsi_14:.1f})")
        
        # MACD сигналы
        if macd_histogram > 0:
            print("🟢 MACD: Бычий сигнал")
            buy_signals += 1
        elif macd_histogram < 0:
            print("🔴 MACD: Медвежий сигнал")
            sell_signals += 1
        else:
            print("🟡 MACD: Нейтрально")
        
        # Цена относительно SMA
        if current_price > sma_20:
            print("🟢 Цена выше SMA(20) - бычий тренд")
            buy_signals += 0.5
        else:
            print("🔴 Цена ниже SMA(20) - медвежий тренд")
            sell_signals += 0.5
        
        print()
        print(f"📊 ИТОГО СИГНАЛОВ:")
        print(f"   Покупка: {buy_signals}")
        print(f"   Продажа: {sell_signals}")
        print()
        
        # Рекомендация
        if buy_signals >= 2:
            print("🚀 РЕКОМЕНДАЦИЯ: ПОКУПКА!")
            print(f"   Цена: ${current_price:.2f}")
            print(f"   Количество: 0.001 ETH")
            print(f"   Стоимость: ${current_price * 0.001:.2f}")
        elif sell_signals >= 2:
            print("📉 РЕКОМЕНДАЦИЯ: ПРОДАЖА!")
        else:
            print("⏸️ РЕКОМЕНДАЦИЯ: УДЕРЖАНИЕ")
            print(f"   Недостаточно сигналов для торговли")
        
        print()
        print("✅ Анализ завершен!")
        
    except Exception as e:
        print(f"❌ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_eth_analysis() 