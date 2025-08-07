"""
Redis кэш менеджер
Быстрый доступ к актуальным данным
"""

import json
import time
from typing import Dict, List, Optional, Any, Union
from database.connection import get_db_connection

class RedisCacheManager:
    """Менеджер Redis кэша"""
    
    def __init__(self):
        self.db = get_db_connection()
        self.default_ttl = 3600  # 1 час по умолчанию
        
    def get_redis(self):
        """Получение подключения к Redis"""
        return self.db.get_redis_connection()
    
    # Методы для работы с ценами
    def set_price(self, symbol: str, price: float, ttl: int = None):
        """Сохранение цены в кэш"""
        try:
            redis_conn = self.get_redis()
            key = f"price:{symbol}"
            data = {
                'price': price,
                'timestamp': int(time.time() * 1000)
            }
            redis_conn.setex(key, ttl or self.default_ttl, json.dumps(data))
            # Убираем избыточное логирование каждой цены
        except Exception as e:
            print(f"❌ Ошибка сохранения в Redis: {e}")
    
    def get_price(self, symbol: str) -> Optional[Dict]:
        """Получение цены из кэша"""
        redis_conn = self.get_redis()
        key = f"price:{symbol}"
        data = redis_conn.get(key)
        return json.loads(data) if data else None
    
    def get_all_prices(self) -> Dict[str, float]:
        """Получение всех цен из кэша"""
        redis_conn = self.get_redis()
        prices = {}
        for key in redis_conn.scan_iter("price:*"):
            symbol = key.decode().split(":")[1]
            data = redis_conn.get(key)
            if data:
                price_data = json.loads(data)
                prices[symbol] = price_data['price']
        return prices
    
    # Методы для работы с техническими индикаторами
    def set_indicators(self, symbol: str, interval: str, indicators: Dict, ttl: int = None):
        """Сохранение технических индикаторов"""
        redis_conn = self.get_redis()
        key = f"indicators:{symbol}:{interval}"
        data = {
            'indicators': indicators,
            'timestamp': int(time.time() * 1000)
        }
        redis_conn.setex(key, ttl or self.default_ttl, json.dumps(data))
    
    def get_indicators(self, symbol: str, interval: str) -> Optional[Dict]:
        """Получение технических индикаторов"""
        redis_conn = self.get_redis()
        key = f"indicators:{symbol}:{interval}"
        data = redis_conn.get(key)
        return json.loads(data) if data else None
    
    # Методы для работы со свечами
    def set_kline(self, symbol: str, interval: str, kline_data: Dict, ttl: int = None):
        """Сохранение свечи в кэш"""
        redis_conn = self.get_redis()
        key = f"kline:{symbol}:{interval}"
        data = {
            'kline': kline_data,
            'timestamp': int(time.time() * 1000)
        }
        redis_conn.setex(key, ttl or self.default_ttl, json.dumps(data))
    
    def get_kline(self, symbol: str, interval: str) -> Optional[Dict]:
        """Получение свечи из кэша"""
        redis_conn = self.get_redis()
        key = f"kline:{symbol}:{interval}"
        data = redis_conn.get(key)
        return json.loads(data) if data else None
    
    # Методы для работы с корреляциями
    def set_correlations(self, symbol: str, correlations: Dict, ttl: int = None):
        """Сохранение корреляций"""
        redis_conn = self.get_redis()
        key = f"correlations:{symbol}"
        data = {
            'correlations': correlations,
            'timestamp': int(time.time() * 1000)
        }
        redis_conn.setex(key, ttl or self.default_ttl, json.dumps(data))
    
    def get_correlations(self, symbol: str) -> Optional[Dict]:
        """Получение корреляций"""
        redis_conn = self.get_redis()
        key = f"correlations:{symbol}"
        data = redis_conn.get(key)
        return json.loads(data) if data else None
    
    # Методы для работы с рыночными данными
    def set_market_data(self, symbol: str, market_data: Dict, ttl: int = None):
        """Сохранение рыночных данных"""
        redis_conn = self.get_redis()
        key = f"market:{symbol}"
        data = {
            'market_data': market_data,
            'timestamp': int(time.time() * 1000)
        }
        redis_conn.setex(key, ttl or self.default_ttl, json.dumps(data))
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Получение рыночных данных"""
        redis_conn = self.get_redis()
        key = f"market:{symbol}"
        data = redis_conn.get(key)
        return json.loads(data) if data else None
    
    # Методы для работы с данными аккаунта
    def set_account_data(self, account_data: Dict, ttl: int = None):
        """Сохранение данных аккаунта"""
        redis_conn = self.get_redis()
        key = "account:data"
        data = {
            'account_data': account_data,
            'timestamp': int(time.time() * 1000)
        }
        redis_conn.setex(key, ttl or self.default_ttl, json.dumps(data))
    
    def get_account_data(self) -> Optional[Dict]:
        """Получение данных аккаунта"""
        redis_conn = self.get_redis()
        key = "account:data"
        data = redis_conn.get(key)
        return json.loads(data) if data else None
    
    # Методы для работы с новостными данными
    def set_news_data(self, symbol: str, news_data: Dict, ttl: int = None):
        """Сохранение новостных данных"""
        redis_conn = self.get_redis()
        key = f"news:{symbol}"
        data = {
            'news_data': news_data,
            'timestamp': int(time.time() * 1000)
        }
        redis_conn.setex(key, ttl or self.default_ttl, json.dumps(data))
    
    def get_news_data(self, symbol: str) -> Optional[Dict]:
        """Получение новостных данных"""
        redis_conn = self.get_redis()
        key = f"news:{symbol}"
        data = redis_conn.get(key)
        return json.loads(data) if data else None
    
    # Методы для работы с кандидатами для торговли
    def set_trading_candidates(self, candidates: List[Dict], ttl: int = None):
        """Сохранение кандидатов для торговли"""
        redis_conn = self.get_redis()
        key = "trading:candidates"
        data = {
            'candidates': candidates,
            'timestamp': int(time.time() * 1000)
        }
        redis_conn.setex(key, ttl or 300, json.dumps(data))  # 5 минут для кандидатов
    
    def get_trading_candidates(self) -> Optional[List[Dict]]:
        """Получение кандидатов для торговли"""
        redis_conn = self.get_redis()
        key = "trading:candidates"
        data = redis_conn.get(key)
        return json.loads(data)['candidates'] if data else None
    
    # Методы для работы с сигналами
    def set_trading_signals(self, symbol: str, signals: Dict, ttl: int = None):
        """Сохранение торговых сигналов"""
        redis_conn = self.get_redis()
        key = f"signals:{symbol}"
        data = {
            'signals': signals,
            'timestamp': int(time.time() * 1000)
        }
        redis_conn.setex(key, ttl or 600, json.dumps(data))  # 10 минут для сигналов
    
    def get_trading_signals(self, symbol: str) -> Optional[Dict]:
        """Получение торговых сигналов"""
        redis_conn = self.get_redis()
        key = f"signals:{symbol}"
        data = redis_conn.get(key)
        return json.loads(data) if data else None
    
    # Методы для работы с Order Book
    def set_orderbook(self, symbol: str, orderbook_data: Dict, ttl: int = None):
        """Сохранение Order Book в кэш"""
        redis_conn = self.get_redis()
        key = f"orderbook:{symbol}"
        data = {
            'orderbook': orderbook_data,
            'timestamp': int(time.time() * 1000)
        }
        redis_conn.setex(key, ttl or self.default_ttl, json.dumps(data))
    
    def get_orderbook(self, symbol: str) -> Optional[Dict]:
        """Получение Order Book из кэша"""
        redis_conn = self.get_redis()
        key = f"orderbook:{symbol}"
        data = redis_conn.get(key)
        return json.loads(data) if data else None
    
    # Методы для работы с историей сделок
    def set_trade_history(self, symbol: str, trade_history: Dict, ttl: int = None):
        """Сохранение истории сделок в кэш"""
        redis_conn = self.get_redis()
        key = f"trade_history:{symbol}"
        data = {
            'trades': trade_history,
            'timestamp': int(time.time() * 1000)
        }
        redis_conn.setex(key, ttl or self.default_ttl, json.dumps(data))
    
    def get_trade_history(self, symbol: str) -> Optional[Dict]:
        """Получение истории сделок из кэша"""
        redis_conn = self.get_redis()
        key = f"trade_history:{symbol}"
        data = redis_conn.get(key)
        return json.loads(data) if data else None
    
    # Методы для очистки кэша
    def clear_symbol_cache(self, symbol: str):
        """Очистка кэша для символа"""
        redis_conn = self.get_redis()
        pattern = f"*:{symbol}:*"
        for key in redis_conn.scan_iter(pattern):
            redis_conn.delete(key)
        
        # Также удаляем общие ключи
        keys_to_delete = [
            f"price:{symbol}",
            f"correlations:{symbol}",
            f"market:{symbol}",
            f"news:{symbol}",
            f"signals:{symbol}"
        ]
        for key in keys_to_delete:
            redis_conn.delete(key)
    
    def clear_all_cache(self):
        """Очистка всего кэша"""
        redis_conn = self.get_redis()
        redis_conn.flushdb()
        print("🗑️ Весь кэш очищен")
    
    # Методы для получения статистики
    def get_cache_stats(self) -> Dict:
        """Получение статистики кэша"""
        redis_conn = self.get_redis()
        stats = {
            'total_keys': redis_conn.dbsize(),
            'memory_usage': redis_conn.info('memory')['used_memory_human'],
            'keys_by_type': {}
        }
        
        # Подсчет ключей по типам
        for key in redis_conn.scan_iter("*"):
            key_str = key.decode()
            if key_str.startswith("price:"):
                stats['keys_by_type']['prices'] = stats['keys_by_type'].get('prices', 0) + 1
            elif key_str.startswith("indicators:"):
                stats['keys_by_type']['indicators'] = stats['keys_by_type'].get('indicators', 0) + 1
            elif key_str.startswith("correlations:"):
                stats['keys_by_type']['correlations'] = stats['keys_by_type'].get('correlations', 0) + 1
            elif key_str.startswith("market:"):
                stats['keys_by_type']['market_data'] = stats['keys_by_type'].get('market_data', 0) + 1
            elif key_str.startswith("news:"):
                stats['keys_by_type']['news'] = stats['keys_by_type'].get('news', 0) + 1
        
        return stats


# Глобальный экземпляр для использования в других модулях
redis_cache = RedisCacheManager()


def get_redis_cache() -> RedisCacheManager:
    """Получение глобального кэш менеджера"""
    return redis_cache


if __name__ == "__main__":
    # Тест кэш менеджера
    cache = RedisCacheManager()
    
    # Тест сохранения и получения данных
    cache.set_price("BTCUSDT", 45000.0)
    cache.set_indicators("BTCUSDT", "1h", {"rsi": 65.5, "macd": 0.5})
    
    # Получение данных
    price = cache.get_price("BTCUSDT")
    indicators = cache.get_indicators("BTCUSDT", "1h")
    
    print("Тест кэша:")
    print(f"Цена BTC: {price}")
    print(f"Индикаторы BTC: {indicators}")
    
    # Статистика
    stats = cache.get_cache_stats()
    print(f"Статистика кэша: {stats}") 