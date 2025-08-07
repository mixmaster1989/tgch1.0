# MEXC WebSocket Client

Модульный WebSocket клиент для работы с API MEXC, поддерживающий все типы потоков данных включая ордербук.

## Особенности

- ✅ Поддержка всех типов потоков данных MEXC
- ✅ Автоматическое управление ордербуком
- ✅ Обработка переподключений
- ✅ Ping/Pong механизм
- ✅ Модульная архитектура
- ✅ Поддержка Protocol Buffers (опционально)
- ✅ Callback система для обработки данных

## Установка

```bash
pip install websockets aiohttp
```

## Быстрый старт

### Базовое использование

```python
import asyncio
from mexc_websocket_client import MEXCWebSocketClient, StreamType

async def trade_callback(trade_data):
    print(f"Сделка: {trade_data['price']} {trade_data['quantity']}")

async def main():
    client = MEXCWebSocketClient()
    await client.connect()
    
    # Подписка на сделки
    await client.subscribe(
        StreamType.TRADES, 
        "BTCUSDT", 
        callback=trade_callback
    )
    
    await client.listen()

asyncio.run(main())
```

### Работа с ордербуком

```python
import asyncio
from mexc_websocket_client import MEXCWebSocketClient, StreamType

async def orderbook_callback(order_book):
    best_bid = order_book.get_best_bid()
    best_ask = order_book.get_best_ask()
    spread = order_book.get_spread()
    
    print(f"Лучшая покупка: {best_bid[0]}")
    print(f"Лучшая продажа: {best_ask[0]}")
    print(f"Спред: {spread}")

async def main():
    client = MEXCWebSocketClient()
    await client.connect()
    
    # Загрузка снапшота ордербука
    await client.load_order_book_snapshot("BTCUSDT")
    
    # Подписка на глубину рынка
    await client.subscribe(
        StreamType.DEPTH, 
        "BTCUSDT", 
        callback=orderbook_callback
    )
    
    await client.listen()

asyncio.run(main())
```

## Типы потоков данных

### 1. Сделки (Trades)
```python
await client.subscribe(StreamType.TRADES, "BTCUSDT", interval="100ms")
```

### 2. Свечи (K-lines)
```python
await client.subscribe(StreamType.KLINES, "BTCUSDT", interval="Min1")
```

### 3. Глубина рынка (Order Book)
```python
await client.subscribe(StreamType.DEPTH, "BTCUSDT", interval="100ms")
```

### 4. Ограниченная глубина
```python
await client.subscribe(StreamType.DEPTH_LIMIT, "BTCUSDT", levels=5)
```

### 5. Лучшие цены (Book Ticker)
```python
await client.subscribe(StreamType.BOOK_TICKER, "BTCUSDT", interval="100ms")
```

## Конфигурация

```python
from mexc_websocket_client import WebSocketConfig

config = WebSocketConfig(
    url="wss://wbs-api.mexc.com/ws",
    ping_interval=30,  # секунды
    reconnect_delay=5,  # секунды
    max_reconnect_attempts=10,
    timeout=10
)

client = MEXCWebSocketClient(config)
```

## Обработка ордербука

Класс `OrderBook` предоставляет методы для работы с локальной копией ордербука:

```python
order_book = client.get_order_book("BTCUSDT")

# Получить лучшую цену покупки
best_bid = order_book.get_best_bid()

# Получить лучшую цену продажи
best_ask = order_book.get_best_ask()

# Получить спред
spread = order_book.get_spread()

# Получить все уровни покупки
bids = order_book.bids

# Получить все уровни продажи
asks = order_book.asks
```

## Интервалы для свечей

- `Min1` - 1 минута
- `Min5` - 5 минут
- `Min15` - 15 минут
- `Min30` - 30 минут
- `Min60` - 1 час
- `Hour4` - 4 часа
- `Hour8` - 8 часов
- `Day1` - 1 день
- `Week1` - 1 неделя
- `Month1` - 1 месяц

## Интервалы для потоков

- `10ms` - 10 миллисекунд
- `100ms` - 100 миллисекунд

## Уровни глубины

- `5` - 5 уровней
- `10` - 10 уровней
- `20` - 20 уровней

## Обработка ошибок

```python
try:
    await client.connect()
    await client.subscribe(StreamType.TRADES, "BTCUSDT")
    await client.listen()
except ConnectionError as e:
    print(f"Ошибка подключения: {e}")
except Exception as e:
    print(f"Общая ошибка: {e}")
finally:
    await client.disconnect()
```

## Protocol Buffers

Для работы с protobuf данными:

```python
from protobuf_handler import DataHandler

# Создание обработчика с поддержкой protobuf
handler = DataHandler(use_protobuf=True)

# Парсинг данных
data = handler.parse_data(raw_bytes)

# Сериализация данных
bytes_data = handler.serialize_data(data_dict)
```

## Примеры использования

Смотрите файл `example_usage.py` для полных примеров использования всех функций.

## Структура проекта

```
├── mexc_websocket_client.py  # Основной WebSocket клиент
├── protobuf_handler.py       # Обработчик Protocol Buffers
├── example_usage.py          # Примеры использования
├── test_websocket_diagnosis.py  # Диагностика подключений
└── README.md                 # Документация
```

## Важные замечания

1. **Снапшот ордербука**: Перед подпиской на глубину рынка обязательно загрузите снапшот через `load_order_book_snapshot()`

2. **Переподключения**: Клиент автоматически обрабатывает переподключения и восстанавливает подписки

3. **Ping/Pong**: Клиент автоматически отправляет ping каждые 30 секунд для поддержания соединения

4. **Лимиты**: Один WebSocket поддерживает максимум 30 подписок

5. **Время жизни**: Соединение действительно не более 24 часов

## Поддержка

При возникновении проблем:

1. Проверьте подключение к интернету
2. Убедитесь, что URL WebSocket доступен
3. Проверьте правильность символов (должны быть в верхнем регистре)
4. Используйте диагностический скрипт `test_websocket_diagnosis.py`