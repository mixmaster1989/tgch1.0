# Smart Money Signals Bot

Telegram-бот для генерации внутридневных сигналов по криптовалютам на основе Smart Money логики с использованием данных с биржи MEXC.

## Установка

1. Скопируйте пример конфигурации:
```bash
cp .env.example .env
```

2. Отредактируйте .env файл и внесите свои API-ключи:
```bash
nano .env
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Запустите бота:
```bash
python3 -m bot.bot
```

## Разрешение конфликтов Git

Если вы получаете ошибки конфликтов при git pull, выполните следующее:

1. При конфликте в .gitignore:
```bash
# Открыть .gitignore и вручную объединить изменения
nano .gitignore

# После редактирования добавить изменения
git add .gitignore

# Сделать коммит
git commit -m "Разрешение конфликта в .gitignore"
```

2. Настройка стратегии слияния для будущих операций:
```bash
# Для merge (стандартный способ объединения изменений)
git config pull.rebase false

# Или для rebase (применение ваших изменений поверх удаленных изменений)
git config pull.rebase true