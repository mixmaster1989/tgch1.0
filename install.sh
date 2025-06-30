#!/bin/bash

# Установка Python и pip, если не установлены
sudo apt update
sudo apt install -y python3 python3-pip

# Установка зависимостей
pip3 install -r requirements.txt

# Создание .env, если не существует
if [ ! -f .env ]; then
  echo 'BITGET_API_KEY=your_key' > .env
  echo 'BITGET_API_SECRET=your_secret' >> .env
  echo 'BITGET_API_PASSPHRASE=your_passphrase' >> .env
  echo 'TELEGRAM_TOKEN=your_telegram_token' >> .env
  echo 'TELEGRAM_GROUP_ID=your_group_id' >> .env
  echo 'WEBHOOK_PORT=8080' >> .env
  echo 'DB_PATH=profiles.db' >> .env
fi

# Запуск бота
python3 main.py 