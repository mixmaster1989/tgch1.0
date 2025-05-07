# Telegram Channel Helper

Бот для раскрутки Telegram-каналов с функциями генерации контента, инвайтинга и анализа криптовалютного рынка.

## Функциональность

### Основные возможности
- Генерация постов с использованием ИИ
- Публикация постов в канал
- Инвайтинг пользователей
- Комментирование в других каналах

### Криптовалютный анализ (Smart Money)
- Мониторинг действий крупных игроков
- Отслеживание всплесков объемов
- Анализ Open Interest и Funding Rate
- Обнаружение зон ликвидности и Order Blocks
- Отправка сигналов в Telegram

## Установка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/tgch1.0.git
cd tgch1.0
```

2. Создайте виртуальное окружение и активируйте его:
```bash
python -m venv tgch_env
source tgch_env/bin/activate  # для Linux/Mac
tgch_env\Scripts\activate     # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` с токеном бота:
```
BOT_TOKEN=your_bot_token_here
```

5. Настройте конфигурацию в файлах:
   - `config/config.yaml` - основная конфигурация
   - `config/crypto_config.yaml` - настройки криптовалютного модуля

## Использование

### Запуск бота
```bash
python main.py
```

### Основные команды
- `/start` - начать работу с ботом
- `/help` - показать справку
- `/generate` - сгенерировать пост
- `/publish` - опубликовать пост в канал
- `/promotion` - меню продвижения канала
- `/crypto` - меню криптовалютного анализа

### Команды криптовалютного модуля
- `/crypto_analyze` - выполнить анализ рынка
- `/crypto_start` - запустить мониторинг
- `/crypto_stop` - остановить мониторинг

## Структура проекта

```
tgch1.0/
├── config/
│   ├── config.yaml
│   └── crypto_config.yaml
├── core/
│   ├── generator.py
│   ├── inviting.py
│   ├── commenting.py
│   ├── referral.py
│   ├── scheduler.py
│   └── telemetry.py
├── crypto/
│   ├── __init__.py
│   ├── config.py
│   ├── data_sources.py
│   ├── smart_money_analyzer.py
│   ├── signal_dispatcher.py
│   └── telegram_interface.py
├── data/
│   └── charts/
├── handlers.py
├── handlers_promotion.py
├── main.py
├── requirements.txt
└── README.md
```

## Настройка API ключей

Для работы криптовалютного модуля необходимо настроить API ключи в файле `config/crypto_config.yaml`:

```yaml
api_keys:
  tradingview: 'your_tradingview_api_key'
  cryptorank: 'your_cryptorank_api_key'
  whale_alert: 'your_whale_alert_api_key'
  binance: 'your_binance_api_key'
```

## Лицензия

MIT