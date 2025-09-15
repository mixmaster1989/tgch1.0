#!/usr/bin/env python3
"""
Анализ волатильности BTCUSDC и ETHUSDC по разным таймфреймам
"""

from mex_api import MexAPI
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_volatility():
    api = MexAPI()

    symbols = ['BTCUSDC', 'ETHUSDC']
    timeframes = ['1m', '1h', '1d']

    print("АНАЛИЗ ВОЛАТИЛЬНОСТИ")
    print("=" * 60)

    for symbol in symbols:
        print(f"\n🪙 {symbol}")
        print("-" * 30)

        for timeframe in timeframes:
            try:
                # Получаем последние 100 свечей
                candles = api.get_klines(symbol, timeframe, 100)

                if candles and len(candles) > 1:
                    # Анализируем волатильность
                    price_changes = []
                    volumes = []

                    for i in range(1, len(candles)):
                        prev_close = float(candles[i-1][4])  # close price предыдущей свечи
                        curr_close = float(candles[i][4])    # close price текущей свечи

                        if prev_close > 0:
                            change_percent = ((curr_close - prev_close) / prev_close) * 100
                            price_changes.append(abs(change_percent))

                        volume = float(candles[i][5]) if len(candles[i]) > 5 else 0
                        volumes.append(volume)

                    # Статистика
                    avg_change = sum(price_changes) / len(price_changes) if price_changes else 0
                    max_change = max(price_changes) if price_changes else 0
                    min_change = min(price_changes) if price_changes else 0

                    # Волатильность (стандартное отклонение)
                    variance = sum([(x - avg_change)**2 for x in price_changes]) / len(price_changes)
                    volatility = variance ** 0.5

                    print(f"\n📊 {timeframe.upper()} ТФ:")
                    print(f"   📈 Среднее изменение: {avg_change:.4f}%")
                    print(f"   📈 Макс изменение: {max_change:.4f}%")
                    print(f"   📉 Мин изменение: {min_change:.4f}%")
                    print(f"   🎲 Волатильность: {volatility:.4f}%")
                    print(f"   📊 Кол-во свечей: {len(price_changes)}")

                    # Анализ для скальпинга
                    if timeframe == '1m':
                        if avg_change < 0.05:
                            scalp_feasibility = "❌ СЛИШКОМ МАЛО ДВИЖЕНИЯ"
                        elif avg_change < 0.1:
                            scalp_feasibility = "⚠️ СЛАБОВато для $0.02"
                        elif avg_change < 0.2:
                            scalp_feasibility = "✅ ХОРОШО для $0.01-0.02"
                        else:
                            scalp_feasibility = "🔥 ОЧЕНЬ ВОЛАТИЛЬНО"

                        print(f"   💹 Скальпинг: {scalp_feasibility}")

                else:
                    print(f"\n📊 {timeframe.upper()}: Нет данных")

            except Exception as e:
                print(f"\n📊 {timeframe.upper()}: Ошибка - {e}")

def get_current_prices():
    """Получить текущие цены"""
    api = MexAPI()

    print("\n\nАКТУАЛЬНЫЕ ЦЕНЫ:")
    print("=" * 30)

    for symbol in ['BTCUSDC', 'ETHUSDC']:
        try:
            ticker = api.get_ticker_price(symbol)
            if 'price' in ticker:
                price = float(ticker['price'])
                print(f"{symbol}: ${price:.2f}")
            else:
                print(f"{symbol}: Ошибка получения цены")
        except Exception as e:
            print(f"{symbol}: Ошибка - {e}")

if __name__ == "__main__":
    analyze_volatility()
    get_current_prices()

