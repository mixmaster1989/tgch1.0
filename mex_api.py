import hashlib
import hmac
import time
import requests
import json
import logging
from typing import Dict, List, Optional
from config import MEX_API_KEY, MEX_SECRET_KEY, MEX_SPOT_URL

logger = logging.getLogger(__name__)

class MexAPI:
    def __init__(self):
        self.api_key = MEX_API_KEY
        self.secret_key = MEX_SECRET_KEY
        self.base_url = MEX_SPOT_URL
        self.max_retries = 3
        self.retry_delay = 1  # секунды
        
    def _generate_signature(self, query_string: str) -> str:
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _get_headers(self, signed: bool = False) -> Dict:
        headers = {
            'Content-Type': 'application/json',
            'X-MEXC-APIKEY': self.api_key
        }
        return headers

    def _to_v2_symbol(self, symbol: str) -> str:
        """Конвертация символа из формата v3 (BTCUSDT) в v2 (BTC_USDT)"""
        if '_' in symbol:
            return symbol
        known_quotes = ['USDT', 'USDC', 'BTC', 'ETH']
        for quote in known_quotes:
            if symbol.endswith(quote):
                base = symbol[:-len(quote)]
                if base:
                    return f"{base}_{quote}"
        return symbol
    
    def _make_request_with_retry(self, method: str, url: str, **kwargs) -> Dict:
        """Выполнить запрос с повторными попытками"""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Безопасный таймаут по умолчанию, чтобы избежать зависаний
                if 'timeout' not in kwargs or kwargs.get('timeout') is None:
                    kwargs['timeout'] = 10
                if method.upper() == 'GET':
                    response = requests.get(url, **kwargs)
                elif method.upper() == 'POST':
                    response = requests.post(url, **kwargs)
                else:
                    raise ValueError(f"Неподдерживаемый метод: {method}")
                
                # Проверяем статус ответа
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"API ошибка (попытка {attempt + 1}): {response.status_code} - {response.text}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (attempt + 1))  # Увеличиваем задержку
                        continue
                    else:
                        return {'error': f'HTTP {response.status_code}', 'message': response.text}
                        
            except Exception as e:
                last_exception = e
                logger.warning(f"Ошибка запроса (попытка {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                else:
                    logger.error(f"Все попытки исчерпаны. Последняя ошибка: {e}")
                    return {'error': 'request_failed', 'message': str(last_exception)}
        
        return {'error': 'max_retries_exceeded', 'message': str(last_exception)}
    
    def get_account_info(self) -> Dict:
        """Получить информацию об аккаунте"""
        timestamp = int(time.time() * 1000)
        query_string = f'timestamp={timestamp}'
        signature = self._generate_signature(query_string)
        
        url = f"{self.base_url}/api/v3/account?{query_string}&signature={signature}"
        return self._make_request_with_retry('GET', url, headers=self._get_headers(True))
    
    def get_ticker_price(self, symbol: str) -> Dict:
        """Получить текущую цену символа с fallback на open API v2"""
        url = f"{self.base_url}/api/v3/ticker/price"
        params = {'symbol': symbol}
        result = self._make_request_with_retry('GET', url, params=params)
        # Если получили корректный ответ формата v3
        if isinstance(result, dict) and 'price' in result:
            return result
        # Fallback: open API v2
        try:
            v2_symbol = self._to_v2_symbol(symbol)
            v2_url = f"https://www.mexc.com/open/api/v2/market/ticker?symbol={v2_symbol}"
            v2_resp = requests.get(v2_url, timeout=10)
            if v2_resp.status_code == 200:
                data = v2_resp.json()
                if data.get('code') == 200 and isinstance(data.get('data'), dict):
                    last = data['data'].get('last')
                    if last is not None:
                        return {'symbol': symbol, 'price': str(last)}
        except Exception as e:
            logger.warning(f"Fallback v2 get_ticker_price ошибка: {e}")
        # Если ничего не получилось, возвращаем исходный результат/ошибку
        return result if isinstance(result, dict) else {'error': 'unknown_error', 'message': 'no valid response'}
    
    def get_klines(self, symbol: str, interval: str = '1m', limit: int = 100) -> List:
        """Получить данные свечей с оптимизированным выбором API"""
        # Маппинг интервалов для MEXC API
        interval_map = {
            '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
            '1h': '60m', '4h': '4h', '8h': '8h', '1d': '1d', '1w': '1w'
        }
        mapped_interval = interval_map.get(interval, interval)
        
        # Сначала пробуем V3 API (работает для всех пар)
        url = f"{self.base_url}/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': mapped_interval,
            'limit': limit
        }
        result = self._make_request_with_retry('GET', url, params=params)
        if isinstance(result, list) and result:
            return result
        
        # Fallback на v2 только если V3 не сработал
        return self._get_klines_v2(symbol, interval, limit)
    
    def _get_klines_v2(self, symbol: str, interval: str, limit: int) -> List:
        """Получить данные свечей через API v2"""
        try:
            # Маппинг интервалов для v2
            interval_map = {
                '1m': '1m', '5m': '5m', '15m': '15m', '30m': '30m',
                '1h': '60m', '4h': '240m', '240m': '4h', '8h': '480m', '1d': '1d', '1w': '1w'
            }
            v2_interval = interval_map.get(interval, interval)
            v2_symbol = self._to_v2_symbol(symbol)
            v2_url = f"https://www.mexc.com/open/api/v2/market/kline?symbol={v2_symbol}&interval={v2_interval}&limit={limit}"
            v2_resp = requests.get(v2_url, timeout=10)  # Уменьшил timeout
            if v2_resp.status_code == 200:
                data = v2_resp.json()
                if data.get('code') == 200 and isinstance(data.get('data'), list):
                    # Приводим к формату v3 klines [openTime, open, high, low, close, volume, ...]
                    klines = []
                    for k in data['data']:
                        if isinstance(k, list) and len(k) >= 6:
                            klines.append([
                                k[0], k[1], k[2], k[3], k[4], k[5]
                            ])
                    return klines
        except Exception as e:
            logger.warning(f"V2 get_klines ошибка для {symbol}: {e}")
        return []
    
    def _round_quantity(self, symbol: str, quantity: float) -> float:
        """Округлить количество согласно правилам биржи MEX"""
        # Получаем информацию о символе для правильного округления
        try:
            exchange_info = self.get_exchange_info()
            if isinstance(exchange_info, dict) and 'symbols' in exchange_info:
                for symbol_info in exchange_info['symbols']:
                    if symbol_info['symbol'] == symbol:
                        # Находим фильтр LOT_SIZE
                        for filter_info in symbol_info['filters']:
                            if filter_info['filterType'] == 'LOT_SIZE':
                                step_size = float(filter_info['stepSize'])
                                # Округляем до ближайшего шага
                                precision = len(str(step_size).split('.')[-1].rstrip('0'))
                                return round(quantity, precision)
        except Exception as e:
            logger.warning(f"Ошибка получения информации о символе {symbol}: {e}")
        
        # Fallback: округляем до 6 знаков после запятой
        return round(quantity, 6)
    
    def place_order(self, symbol: str, side: str, quantity: float, price: Optional[float] = None) -> Dict:
        """Разместить ордер"""
        timestamp = int(time.time() * 1000)
        
        # Правильно округляем количество
        rounded_quantity = self._round_quantity(symbol, quantity)
        
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET' if price is None else 'LIMIT',
            'quantity': rounded_quantity,
            'timestamp': timestamp
        }
        
        if price:
            params['price'] = price
            params['timeInForce'] = 'GTC'
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = self._generate_signature(query_string)
        
        url = f"{self.base_url}/api/v3/order"
        data = f"{query_string}&signature={signature}"
        
        return self._make_request_with_retry('POST', url, data=data, headers=self._get_headers(True))
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Dict:
        """Разместить маркет ордер"""
        return self.place_order(symbol, side, quantity, price=None)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List:
        """Получить открытые ордера"""
        timestamp = int(time.time() * 1000)
        query_string = f'timestamp={timestamp}'
        
        if symbol:
            query_string = f'symbol={symbol}&{query_string}'
        
        signature = self._generate_signature(query_string)
        url = f"{self.base_url}/api/v3/openOrders?{query_string}&signature={signature}"
        
        response = requests.get(url, headers=self._get_headers(True))
        return response.json()
    
    def get_order_history(self, symbol: Optional[str] = None, limit: int = 100) -> List:
        """Получить историю ордеров"""
        timestamp = int(time.time() * 1000)
        query_string = f'timestamp={timestamp}&limit={limit}'
        
        if symbol:
            query_string = f'symbol={symbol}&{query_string}'
        
        signature = self._generate_signature(query_string)
        url = f"{self.base_url}/api/v3/allOrders?{query_string}&signature={signature}"
        
        response = requests.get(url, headers=self._get_headers(True))
        return response.json()
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """Отменить ордер"""
        timestamp = int(time.time() * 1000)
        query_string = f'symbol={symbol}&orderId={order_id}&timestamp={timestamp}'
        signature = self._generate_signature(query_string)
        
        url = f"{self.base_url}/api/v3/order"
        data = f"{query_string}&signature={signature}"
        
        response = requests.delete(url, data=data, headers=self._get_headers(True))
        return response.json()
    
    def get_24hr_ticker(self, symbol=None):
        """Получить 24ч статистику"""
        url = f"{self.base_url}/api/v3/ticker/24hr"
        params = {'symbol': symbol} if symbol else {}
        response = requests.get(url, params=params)
        return response.json()
    
    def get_symbol_ticker(self, symbol):
        """Получить тикер символа"""
        return self.get_ticker_price(symbol)
    
    def create_order(self, symbol, side, type, quantity, price=None):
        """Создать ордер"""
        return self.place_order(symbol, side, quantity, price)
    
    def get_depth(self, symbol, limit=100):
        """Получить стакан заявок"""
        url = f"{self.base_url}/api/v3/depth"
        params = {
            'symbol': symbol,
            'limit': limit
        }
        response = requests.get(url, params=params)
        return response.json()
    
    def get_exchange_info(self):
        """Получить информацию о бирже и поддерживаемых символах"""
        url = f"{self.base_url}/api/v3/exchangeInfo"
        response = requests.get(url)
        return response.json()

    # ===== Wallet endpoints =====
    def get_deposit_history(self, coin: Optional[str] = None, startTime: Optional[int] = None,
                             endTime: Optional[int] = None, limit: Optional[int] = None) -> Dict:
        """Получить историю депозитов (поддерживающие сети)

        Args:
            coin: Монета, напр. 'USDT'
            startTime: Начало периода (ms)
            endTime: Конец периода (ms)
            limit: Лимит записей
        Returns:
            Dict или List с историей депозитов (как возвращает API)
        """
        timestamp = int(time.time() * 1000)
        params = { 'timestamp': timestamp }
        if coin:
            params['coin'] = coin
        if startTime:
            params['startTime'] = startTime
        if endTime:
            params['endTime'] = endTime
        if limit:
            params['limit'] = limit

        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = self._generate_signature(query_string)
        url = f"{self.base_url}/api/v3/capital/deposit/hisrec?{query_string}&signature={signature}"
        return self._make_request_with_retry('GET', url, headers=self._get_headers(True))

    def sum_deposits_usd(self, coin: str = 'USDT', startTime: Optional[int] = None,
                          endTime: Optional[int] = None) -> Dict:
        """Подсчитать сумму депозитов по монете за период.

        Возвращает словарь с полями total_amount и count. Статусы фильтруются на успешные, если есть.
        """
        data = self.get_deposit_history(coin=coin, startTime=startTime, endTime=endTime)
        total = 0.0
        count = 0
        try:
            if isinstance(data, list):
                for item in data:
                    c = item.get('coin') or item.get('asset')
                    if c != coin:
                        continue
                    # статус успешности (если присутствует)
                    status = str(item.get('status', '')).lower()
                    if status and status not in {'success', 'successful', 'done', 'finished', 'completed', '1', 'true'}:
                        continue
                    amt = float(item.get('amount') or item.get('qty') or 0)
                    total += amt
                    count += 1
            return {'success': True, 'total_amount': total, 'count': count, 'raw': data}
        except Exception as e:
            return {'success': False, 'error': str(e), 'raw': data}

    # ===== Futures endpoints =====
    def get_futures_account_info(self) -> Dict:
        """Получить информацию о фьючерсном аккаунте"""
        try:
            # Используем базовый URL для фьючерсов
            futures_base_url = 'https://contract.mexc.com'
            
            timestamp = int(time.time() * 1000)
            query_string = f'timestamp={timestamp}'
            signature = self._generate_signature(query_string)
            
            url = f"{futures_base_url}/api/v1/private/account/asset?{query_string}&signature={signature}"
            return self._make_request_with_retry('GET', url, headers=self._get_headers(True))
            
        except Exception as e:
            logger.error(f"Ошибка получения фьючерсного баланса: {e}")
            return {'error': str(e)}
    
    def get_futures_balance(self) -> Dict:
        """Получить баланс фьючерсного счета"""
        try:
            # Альтернативный эндпоинт для баланса
            futures_base_url = 'https://contract.mexc.com'
            
            timestamp = int(time.time() * 1000)
            query_string = f'timestamp={timestamp}'
            signature = self._generate_signature(query_string)
            
            url = f"{futures_base_url}/api/v1/account/info?{query_string}&signature={signature}"
            return self._make_request_with_retry('GET', url, headers=self._get_headers(True))
            
        except Exception as e:
            logger.error(f"Ошибка получения фьючерсного баланса: {e}")
            return {'error': str(e)}
    
    def transfer_spot_to_futures(self, asset: str, amount: float) -> Dict:
        """Перевести средства со спотового счета на фьючерсный"""
        try:
            timestamp = int(time.time() * 1000)
            params = {
                'asset': asset,
                'amount': str(amount),
                'type': '1',  # 1: спот → фьючерсы
                'timestamp': timestamp
            }
            
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            signature = self._generate_signature(query_string)
            
            url = f"{self.base_url}/api/v3/asset/transfer"
            data = f"{query_string}&signature={signature}"
            
            return self._make_request_with_retry('POST', url, data=data, headers=self._get_headers(True))
            
        except Exception as e:
            logger.error(f"Ошибка перевода спот → фьючерсы: {e}")
            return {'error': str(e)}
    
    def transfer_futures_to_spot(self, asset: str, amount: float) -> Dict:
        """Перевести средства с фьючерсного счета на спотовый"""
        try:
            timestamp = int(time.time() * 1000)
            params = {
                'asset': asset,
                'amount': str(amount),
                'type': '2',  # 2: фьючерсы → спот
                'timestamp': timestamp
            }
            
            query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
            signature = self._generate_signature(query_string)
            
            url = f"{self.base_url}/api/v3/asset/transfer"
            data = f"{query_string}&signature={signature}"
            
            return self._make_request_with_retry('POST', url, data=data, headers=self._get_headers(True))
            
        except Exception as e:
            logger.error(f"Ошибка перевода фьючерсы → спот: {e}")
            return {'error': str(e)}