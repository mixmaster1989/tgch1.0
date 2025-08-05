import os
from dotenv import load_dotenv

load_dotenv()

# MEX API Configuration
MEX_API_KEY = os.getenv('MEX_API_KEY')
MEX_SECRET_KEY = os.getenv('MEX_SECRET_KEY')
MEX_BASE_URL = 'https://contract.mexc.com'
MEX_SPOT_URL = 'https://api.mexc.com'

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')  # Golden key
OPENROUTER_SILVER_KEY_1 = os.getenv('OPENROUTER_SILVER_KEY_1')
OPENROUTER_SILVER_KEY_2 = os.getenv('OPENROUTER_SILVER_KEY_2')
OPENROUTER_SILVER_KEY_3 = os.getenv('OPENROUTER_SILVER_KEY_3')
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'

# Trading Configuration
DEFAULT_TRADE_AMOUNT = 10  # USDT
MAX_POSITIONS = 5
STOP_LOSS_PERCENT = 2.0
TAKE_PROFIT_PERCENT = 5.0

# Neural Network Configuration
GOLDEN_MODEL = 'deepseek/deepseek-r1-0528:free'  # Бесплатная модель для торговых решений
SILVER_MODEL = 'deepseek/deepseek-r1-0528:free'  # Бесплатная модель для чата
ANALYSIS_INTERVAL = 300  # seconds