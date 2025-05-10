# Smart Money Crypto Trading Bot

Telegram-бот для внутридневного криптоанализа с фокусом на точность сигналов (30 мин — 24 ч) и генерацией трейдинг-сигналов с уровнями и быстрым доступом к TradingView.

## 📊 Основные функции

- Точность сигналов (30 мин — 24 ч)
- Генерация трейдинг-сигналов с уровнями
- Быстрый доступ к TradingView через инлайн-кнопки
- Анализ Smart Money концепций
- Интеграция с Binance и Cryptorank API

## 🧠 Архитектура проекта

```
bot/
├── analytics/          # Основная логика сигналов
│   ├── smart_money.py  # Комплексный анализ и генерация сигналов
│   ├── clustering.py   # DBSCAN с динамическими параметрами
│   └── volatility.py   # Расчёт ATR и временного горизонта
│  
├── data/               # Источники данных
│   ├── websocket_binance.py  # Обработчик сделок Binance
│   └── cryptorank_api.py     # Запросы к Cryptorank API
│  
├── notification/       # Уведомления и форматирование
│   ├── signal_formatter.py   # Форматирование + MarkdownV2
│   └── tradingview_link.py   # Генератор URL с уровнями
│  
├── risk/               # Управление рисками
│   ├── levels_calculator.py  # Расчёт Entry/Stop/TP
│   └── confidence.py         # Процент уверенности (RSI + объём)
│  
└── bot.py              # Запуск + проверка .env
```

## 🛠️ Конфигурация

Все параметры конфигурации находятся в `configs/thresholds.yaml`:

```yaml
dbscan:
  default_eps: 0.002
  volatility_adjust: true

risk_management:
  atr_period: 14
  tp1_multiplier: 1.5
  tp2_multiplier: 3.0
  stop_multiplier: 1.0

confidence:
  volume_weight: 0.4
  rsi_weight: 0.3
  density_weight: 0.3
```

## 🧪 Установка и запуск

1. Клонируйте репозиторий:
```bash
git clone https://github.com/mixmaster1989/tgch1.0.git
cd tgch1.0
```

2. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv env
source env/bin/activate  # Linux/Mac
# или
env\Scripts\activate   # Windows

pip install -r requirements.txt
```

3. Настройте переменные окружения:
```bash
# Создайте файл .env и добавьте туда ваши API-ключи
cp .env.example .env
# Откройте .env и введите ваши реальные значения
```

4. Запустите бота:
```bash
python bot/bot.py
```

## 📦 Требования

- Python 3.9+
- Библиотеки из `requirements.txt`
- API-ключи:
  - Binance API
  - CryptoRank API
  - Telegram Bot Token

## 📈 Пример сигнала

```
📈 *BTC/USDT* ▸ Long
🟢 Уверенность: `78%`
🎯 Вход: `$30,000.00`
🛑 Стоп: `$29,000.00`
🎯 TP1: `$31,500.00` | TP2: `$33,000.00`
📊 R:R = `2.0`
⏱ Горизонт: `4H`
```

## 📚 Дополнительные материалы

- [TradingView API Documentation](https://www.tradingview.com/widget-api-docs/)
- [Binance API Documentation](https://binance-docs.github.io/apidocs/)
- [CryptoRank API Documentation](https://developers.cryptorank.io/)
- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)

## 📦 Пример использования

```python
from bot.analytics.smart_money import SmartMoneySignal
from bot.data.websocket_binance import BinanceWebSocketHandler

async def example_usage():
    # Инициализация компонентов
    ws_handler = BinanceWebSocketHandler()
    signal_generator = SmartMoneySignal()
    
    # Получение исторических данных (пример)
    historical_data = await ws_handler.get_historical_data("BTCUSDT", "1h", 100)
    
    # Генерация сигнала
    signal = signal_generator.generate_signal("BTC/USDT", historical_data)
    
    # Форматирование и вывод сигнала
    formatted_signal = format_signal(signal)
    print(formatted_signal)
    
    # Получение ссылки TradingView
    tv_url = generate_tv_url(signal)
    print(f"TradingView URL: {tv_url}")

# Запуск примера
if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
```

## 🧠 Возможные улучшения

- Добавление машинного обучения для улучшения точности сигналов
- Реализация системы backtesting для тестирования стратегий
- Добавление поддержки других бирж (Coinbase, Kraken)
- Интеграция с системами автоматической торговли
- Реализация веб-интерфейса для настройки параметров и просмотра сигналов