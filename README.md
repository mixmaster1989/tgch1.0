# MEX Trading Bot

Торговый бот для биржи MEX с использованием ИИ анализа через OpenRouter API и интерфейсом Telegram.

## Возможности

- 📊 Спотовая торговля на бирже MEX
- 🤖 Анализ рынка с помощью нейронных сетей
- 💬 Управление через Telegram бота
- 📈 Получение рыночных данных в реальном времени
- 💰 Мониторинг баланса и ордеров

## Установка

1. Клонируйте репозиторий
2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Скопируйте `.env.example` в `.env` и заполните настройки:
```bash
cp .env.example .env
```

4. Настройте переменные окружения:
- `MEX_API_KEY` - API ключ MEX
- `MEX_SECRET_KEY` - Секретный ключ MEX
- `TELEGRAM_BOT_TOKEN` - Токен Telegram бота
- `TELEGRAM_CHAT_ID` - ID чата Telegram
- `OPENROUTER_API_KEY` - API ключ OpenRouter

## Запуск

```bash
python main.py
```

## Команды Telegram бота

- `/start` - Запуск бота и главное меню
- `/balance` - Показать баланс аккаунта
- `/price SYMBOL` - Получить цену символа (например: `/price BTCUSDT`)
- `/analyze SYMBOL` - Анализ символа с помощью ИИ
- `/orders` - Показать открытые ордера

## Структура проекта

- `main.py` - Главный файл запуска
- `config.py` - Конфигурация приложения
- `mex_api.py` - Работа с MEX API
- `neural_analyzer.py` - ИИ анализ через OpenRouter
- `telegram_bot.py` - Telegram бот интерфейс

## Безопасность

⚠️ **ВАЖНО**: Никогда не публикуйте свои API ключи. Используйте файл `.env` для хранения конфиденциальных данных.

## Лицензия

MIT License