import os
from dotenv import load_dotenv

load_dotenv()

# MEX API Configuration
MEX_API_KEY = os.getenv('MEX_API_KEY')
MEX_SECRET_KEY = os.getenv('MEX_SECRET_KEY')
MEX_BASE_URL = 'https://contract.mexc.com'
MEX_SPOT_URL = 'https://api.mexc.com'
MEX_WEBSOCKET_URL = 'wss://wbs.mexc.com/ws'

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
GOLDEN_MODEL = 'anthropic/claude-opus-4'  # Claude Opus 4 для финальных решений
SILVER_MODEL = 'deepseek/deepseek-r1-0528:free'  # Бесплатная модель для повседневных задач

# AI Trading Models
AI_EXPERT_MODELS = {
    "openai": "openai/gpt-4o-mini",
    "anthropic": "anthropic/claude-3.5-haiku", 
    "google": "google/gemini-2.5-flash-lite"
}

AI_JUDGE_MODEL = "anthropic/claude-opus-4"
ANALYSIS_INTERVAL = 300  # seconds

# Symbols to exclude from market scanning globally
# Extend this list to disable noisy/illiquid pairs from scanner reports and auto-buys
EXCLUDED_SYMBOLS = [
    # База: не сканируем мажоры (уже исключались ранее)
    'BTCUSDT', 'ETHUSDT',
    # Из беседы: балласт/микро‑позиции и слабые проекты — исключить из сканера
    'PUADUSDT', 'DREYAIUSDT', 'LUMAUSDT', 'SUPRAUSDT', 'NOTUSDT', 'ACAUSDT',
    'KERNELUSDT', 'SAPIENUSDT', 'XLMUSDT', 'NEXOUSDT', 'CUSDT', 'THEUSDT',
    'XNYUSDT', 'SENDUSDT', 'RSRUSDT', 'PROMPTUSDT', 'MBGUSDT'
]

# PnL Monitor Configuration
PNL_MONITOR_CONFIG = {
    'profit_threshold': 0.07,  # Снижено с 0.15 до 0.07 (7 центов) для подвижного аккаунта
    'check_interval': 60,      # Проверка каждую минуту (не меняем)
    'notification_interval': 600,  # Уведомления каждые 10 минут (увеличено в 2 раза)
    'trading_pairs': ['BTCUSDC', 'ETHUSDC'],
    'auto_sell_enabled': True,
    'telegram_notifications': True,
    'file_logging': True,
    'log_file': 'pnl_monitor.log'
}