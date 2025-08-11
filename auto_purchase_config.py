#!/usr/bin/env python3
"""
Конфигурация автоматических покупок BTC/ETH
"""

# Настройки мониторинга баланса
BALANCE_MONITOR_CONFIG = {
    # Минимальный баланс USDT для покупки
    'min_balance_threshold': 10.0,  # $10
    
    # Максимальная сумма одной покупки
    'max_purchase_amount': 100.0,   # $100
    
    # Интервал проверки баланса (в секундах)
    'balance_check_interval': 60,   # 1 минута
    
    # Минимальный интервал между покупками (в секундах)
    'min_purchase_interval': 300,   # 5 минут
    
    # Максимальное количество покупок в день
    'max_daily_purchases': 10,
    
    # Время торговли (UTC)
    'trading_hours': {
        'start': '00:00',
        'end': '23:59'
    },
    
    # Дни недели для торговли (0=понедельник, 6=воскресенье)
    'trading_days': [0, 1, 2, 3, 4, 5, 6],  # Все дни
}

# Стратегия распределения средств
ALLOCATION_STRATEGY = {
    # Распределение между BTC и ETH
    'btc_allocation': 0.6,    # 60% на BTC
    'eth_allocation': 0.4,    # 40% на ETH
    
    # Минимальная сумма на одну монету
    'min_amount_per_coin': 5.0,  # $5
    
    # Максимальная сумма на одну монету
    'max_amount_per_coin': 50.0,  # $50
}

# Настройки ордеров
ORDER_CONFIG = {
    # Тип ордера
    'order_type': 'LIMIT',  # MARKET или LIMIT
    
    # Для лимитных ордеров - отклонение от рыночной цены (%)
    'limit_price_deviation': 0.05,  # 0.05%
    
    # Анализ стакана для мейкера
    'use_orderbook_analysis': True,
    
    # Минимальный спред для мейкера (%)
    'min_spread_for_maker': 0.1,  # 0.1%
    
    # Таймаут исполнения ордера (в секундах)
    'order_timeout': 300,  # 5 минут для лимитных ордеров
    
    # Количество попыток при ошибке
    'max_retries': 3,
    
    # Задержка между попытками (в секундах)
    'retry_delay': 5,
}

# Настройки безопасности
SAFETY_CONFIG = {
    # Максимальный дневной лимит покупок (в USDT)
    'max_daily_spend': 500.0,  # $500
    
    # Максимальный размер одной покупки (% от баланса)
    'max_purchase_percent': 50.0,  # 50%
    
    # Остановка при достижении лимита
    'stop_on_limit': True,
    
    # Резервный баланс (не тратить)
    'reserve_balance': 20.0,  # $20
}

# Настройки уведомлений
NOTIFICATION_CONFIG = {
    # Включить уведомления в Telegram
    'telegram_enabled': True,
    
    # Отправлять уведомления о покупках
    'purchase_notifications': True,
    
    # Отправлять уведомления об ошибках
    'error_notifications': True,
    
    # Отправлять ежедневные отчеты
    'daily_reports': True,
    
    # Время отправки ежедневного отчета (UTC)
    'daily_report_time': '09:00',
}

# Настройки логирования
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'auto_purchase.log',
    'max_size': 10 * 1024 * 1024,  # 10 MB
    'backup_count': 5,
}

# Настройки тестирования
TEST_CONFIG = {
    # Режим симуляции (не тратить реальные деньги)
    'simulation_mode': False,
    
    # Тестовый баланс для симуляции
    'test_balance': 100.0,  # $100
    
    # Логирование всех операций в симуляции
    'log_simulation': True,
}

# Комбинированная конфигурация
AUTO_PURCHASE_CONFIG = {
    'balance_monitor': BALANCE_MONITOR_CONFIG,
    'allocation': ALLOCATION_STRATEGY,
    'orders': ORDER_CONFIG,
    'safety': SAFETY_CONFIG,
    'notifications': NOTIFICATION_CONFIG,
    'logging': LOGGING_CONFIG,
    'test': TEST_CONFIG,
}

# Функция для получения конфигурации
def get_config() -> dict:
    """Получить полную конфигурацию"""
    return AUTO_PURCHASE_CONFIG

# Функция для обновления конфигурации
def update_config(new_config: dict):
    """Обновить конфигурацию"""
    global AUTO_PURCHASE_CONFIG
    AUTO_PURCHASE_CONFIG.update(new_config)

# Функция для получения конкретной настройки
def get_setting(category: str, key: str, default=None):
    """Получить конкретную настройку"""
    try:
        return AUTO_PURCHASE_CONFIG[category][key]
    except KeyError:
        return default 