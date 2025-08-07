#!/bin/bash

# Скрипт настройки PostgreSQL для MEX Trading Bot
# Автор: AI Assistant
# Дата: 2025-08-06

echo "🔧 Настройка PostgreSQL для MEX Trading Bot..."
echo "================================================"

# Проверяем, запущен ли PostgreSQL
if ! systemctl is-active --quiet postgresql; then
    echo "❌ PostgreSQL не запущен. Запускаем..."
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

echo "✅ PostgreSQL запущен"

# Создаем пользователя с паролем
echo "👤 Создаем пользователя mexca_user..."
sudo -u postgres psql -c "CREATE USER mexca_user WITH PASSWORD '123';" 2>/dev/null || echo "⚠️  Пользователь уже существует"

# Устанавливаем пароль (если пользователь уже существует)
echo "🔐 Устанавливаем пароль для mexca_user..."
sudo -u postgres psql -c "ALTER USER mexca_user PASSWORD '123';"

# Создаем базу данных
echo "🗄️  Создаем базу данных mexca_trade..."
sudo -u postgres createdb mexca_trade 2>/dev/null || echo "⚠️  База данных уже существует"

# Даем права пользователю на базу данных
echo "🔑 Даем права пользователю на базу данных..."
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE mexca_trade TO mexca_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mexca_user;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mexca_user;"

# Настраиваем аутентификацию в pg_hba.conf
echo "🔒 Настраиваем аутентификацию..."
sudo sed -i 's/local   all             all                                     peer/local   all             all                                     md5/' /etc/postgresql/14/main/pg_hba.conf

# Перезапускаем PostgreSQL
echo "🔄 Перезапускаем PostgreSQL..."
sudo systemctl restart postgresql

# Тестируем подключение
echo "🧪 Тестируем подключение..."
if psql -h localhost -U mexca_user -d mexca_trade -c "SELECT version();" 2>/dev/null; then
    echo "✅ Подключение к PostgreSQL успешно!"
else
    echo "❌ Ошибка подключения к PostgreSQL"
    echo "Попробуйте подключиться вручную:"
    echo "psql -h localhost -U mexca_user -d mexca_trade"
    echo "Пароль: 123"
fi

echo ""
echo "🎯 Следующие шаги:"
echo "1. Установить Redis: sudo apt install redis-server"
echo "2. Установить Python зависимости: pip install -r requirements_db.txt"
echo "3. Запустить миграции: python database/migrations.py"
echo "4. Протестировать: python tests/test_database.py"

echo ""
echo "📝 Настройки для .env файла:"
echo "DB_HOST=localhost"
echo "DB_PORT=5432"
echo "DB_NAME=mexca_trade"
echo "DB_USER=mexca_user"
echo "DB_PASSWORD=123"
echo "REDIS_HOST=localhost"
echo "REDIS_PORT=6379" 