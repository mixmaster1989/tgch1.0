"""
Модуль для работы с TradingView
"""

def generate_tradingview_link(pair: str) -> str:
    """
    Генерирует ссылку на TradingView для пары
    
    Args:
        pair: Торговая пара в формате BTC/USDT
        
    Returns:
        str: Ссылка на TradingView
    """
    # Преобразуем формат пары для TradingView
    symbol, quote = pair.split('/')
    tv_symbol = f"BINANCE:{symbol}{quote}"
    
    # Формируем ссылку
    return f"https://www.tradingview.com/chart/?symbol={tv_symbol}"