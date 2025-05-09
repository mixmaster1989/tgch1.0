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
    try:
        # Преобразуем формат пары для TradingView
        symbol, quote = pair.split('/')
        
        # Для популярных пар используем прямые ссылки на известные тикеры
        popular_pairs = {
            "BTC/USDT": "BINANCE:BTCUSDT",
            "ETH/USDT": "BINANCE:ETHUSDT",
            "BNB/USDT": "BINANCE:BNBUSDT",
            "SOL/USDT": "BINANCE:SOLUSDT",
            "XRP/USDT": "BINANCE:XRPUSDT",
            "ADA/USDT": "BINANCE:ADAUSDT",
            "DOGE/USDT": "BINANCE:DOGEUSDT",
            "DOT/USDT": "BINANCE:DOTUSDT",
            "AVAX/USDT": "BINANCE:AVAXUSDT",
            "MATIC/USDT": "BINANCE:MATICUSDT",
            "LINK/USDT": "BINANCE:LINKUSDT",
            "UNI/USDT": "BINANCE:UNIUSDT",
            "ATOM/USDT": "BINANCE:ATOMUSDT",
            "LTC/USDT": "BINANCE:LTCUSDT",
            "SHIB/USDT": "BINANCE:SHIBUSDT"
        }
        
        if pair in popular_pairs:
            tv_symbol = popular_pairs[pair]
        else:
            # Для остальных пар используем стандартный формат
            tv_symbol = f"BINANCE:{symbol}{quote}"
        
        # Формируем ссылку с параметрами
        # Добавляем параметр interval=15 для 15-минутного графика по умолчанию
        return f"https://tradingview.com/chart/?symbol={tv_symbol}&interval=15"
    except Exception:
        # В случае ошибки возвращаем ссылку на главную страницу TradingView
        return "https://tradingview.com/chart/"