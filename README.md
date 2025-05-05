# TGE-MVP: Telegram Growth Engine

Раскрутка Telegram-канала под ключ:
- Рефералка
- Планировщик постов
- Телеметрия и рост

## Установка
```bash
pip install -r requirements.txt
cp .env.example .env
hyperbooster/
├── ai_engine/           # Генерация постов, CTA, ответов
│   ├── __init__.py      # Инициализация модуля
│   ├── post_generator.py# Генерация контента
│   ├── cta_generator.py # Генерация Call To Action (CTA)
│   └── response_bot.py  # AI-ответчик
├── scrapers/            # Парсеры трендовых тем
│   ├── __init__.py
│   ├── telegram_scraper.py # Парсинг Telegram-каналов
│   └── trend_scraper.py    # Парсинг трендов
├── telegram_bot/        # Интерфейс взаимодействия через Telegram
│   ├── __init__.py
│   ├── bot.py           # Основной файл с Telegram-ботом
│   └── handlers.py      # Обработчики команд
├── content_templates/   # Готовые шаблоны контента
│   ├── __init__.py
│   ├── post_templates.py  # Примеры шаблонов для постов
│   └── cta_templates.py   # Примеры шаблонов для CTA
├── data/                # Данные пользователя / кэши
│   ├── __init__.py
│   └── user_data.json    # Хранение данных и кэширования
├── core/                # Логика, планировщик, аналитика
│   ├── __init__.py
│   ├── scheduler.py      # Планировщик задач
│   ├── analytics.py      # Сбор и обработка аналитики
│   └── utils.py          # Утилиты для работы с данными
├── requirements.txt     # Зависимости
└── README.md            # Описание проекта
