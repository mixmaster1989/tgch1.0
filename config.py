import os
from dotenv import load_dotenv

def load_config():
    load_dotenv()
    return {
        'BITGET_API_KEY': os.getenv('BITGET_API_KEY'),
        'BITGET_API_SECRET': os.getenv('BITGET_API_SECRET'),
        'BITGET_API_PASSPHRASE': os.getenv('BITGET_API_PASSPHRASE'),
        'TELEGRAM_TOKEN': os.getenv('TELEGRAM_TOKEN'),
        'TELEGRAM_GROUP_ID': os.getenv('TELEGRAM_GROUP_ID'),
        'WEBHOOK_PORT': int(os.getenv('WEBHOOK_PORT', 8080)),
        'DB_PATH': os.getenv('DB_PATH', 'profiles.db'),
    } 