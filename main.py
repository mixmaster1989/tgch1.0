import logging
from config import load_config
from logger import setup_logger
from telegram_bot import start_telegram_bot
from webhook import start_webhook_server
from profiles import init_db

if __name__ == "__main__":
    config = load_config()
    setup_logger()
    init_db()
    # Запуск Telegram-бота и сервера вебхуков параллельно
    start_telegram_bot(config)
    start_webhook_server(config) 