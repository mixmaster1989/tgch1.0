#!/usr/bin/env python3
"""
Конфигурация автоматического торгового бота
"""

# Настройки торговли
TRADING_CONFIG = {
    # Основной символ для торговли
    'symbol': 'ETHUSDT',
    
    # Минимальный профит (в процентах)
    'min_profit_percent': 0.5,
    
    # Комиссия биржи (в процентах)
    'commission': 0.001,  # 0.1%
    
    # Минимальный размер лота
    'min_lot_size': 0.001,  # Минимальный лот ETH
    
    # Максимальная сумма инвестиций (в USD)
    'max_investment': 0.001,  # Только минимальный лот!
    
    # Интервал анализа (в секундах)
    'analysis_interval': 300,  # 5 минут
    
    # Таймаут исполнения ордера (в секундах)
    'order_timeout': 3600,  # 1 час
    
    # Максимальное количество активных ордеров
    'max_active_orders': 3,
}

# Настройки технического анализа
TECHNICAL_CONFIG = {
    # RSI настройки
    'rsi_period': 14,
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    
    # MACD настройки
    'macd_fast': 12,
    'macd_slow': 26,
    'macd_signal': 9,
    
    # Bollinger Bands настройки
    'bb_period': 20,
    'bb_std_dev': 2,
    
    # ATR настройки
    'atr_period': 14,
}

# Настройки новостного анализа
NEWS_CONFIG = {
    # Минимальный impact score для учета новостей
    'min_impact_score': 0.3,
    
    # Вес новостного фактора в решении
    'news_weight': 0.3,
    
    # Интервал обновления новостей (в секундах)
    'news_update_interval': 1800,  # 30 минут
}

# Настройки Telegram
TELEGRAM_CONFIG = {
    # Включить уведомления
    'enabled': True,
    
    # Отправлять все сообщения
    'send_all_messages': True,
    
    # Отправлять только важные сообщения
    'send_important_only': False,
    
    # Включить детальные логи
    'detailed_logs': True,
}

# Настройки безопасности
SAFETY_CONFIG = {
    # Максимальный убыток за день (в процентах)
    'max_daily_loss': 5.0,
    
    # Максимальный убыток за сделку (в процентах)
    'max_trade_loss': 2.0,
    
    # Остановка торговли при достижении лимита
    'stop_on_loss_limit': True,
    
    # Время торговли (UTC)
    'trading_hours': {
        'start': '00:00',
        'end': '23:59'
    },
    
    # Дни недели для торговли (0=понедельник, 6=воскресенье)
    'trading_days': [0, 1, 2, 3, 4, 5, 6],  # Все дни
}

# Настройки логирования
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'auto_trader.log',
    'max_size': 10 * 1024 * 1024,  # 10 MB
    'backup_count': 5,
} 