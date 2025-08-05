import hashlib
import hmac
import time
import requests
import json
from typing import Dict, List, Optional
from config import MEX_API_KEY, MEX_SECRET_KEY, MEX_SPOT_URL

class MexAPI:
    def __init__(self):
        self.api_key = MEX_API_KEY
        self.secret_key = MEX_SECRET_KEY
        self.base_url = MEX_SPOT_URL
        
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
    
    def get_account_info(self) -> Dict:
        """Получить информацию об аккаунте"""
        timestamp = int(time.time() * 1000)
        query_string = f'timestamp={timestamp}'
        signature = self._generate_signature(query_string)
        
        url = f"{self.base_url}/api/v3/account?{query_string}&signature={signature}"
        response = requests.get(url, headers=self._get_headers(True))
        return response.json()
    
    def get_ticker_price(self, symbol: str) -> Dict:
        """Получить текущую цену символа"""
        url = f"{self.base_url}/api/v3/ticker/price"
        params = {'symbol': symbol}
        response = requests.get(url, params=params)
        return response.json()
    
    def get_klines(self, symbol: str, interval: str = '1m', limit: int = 100) -> List:
        """Получить данные свечей"""
        url = f"{self.base_url}/api/v3/klines"
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        response = requests.get(url, params=params)
        return response.json()
    
    def place_order(self, symbol: str, side: str, quantity: float, price: Optional[float] = None) -> Dict:
        """Разместить ордер"""
        timestamp = int(time.time() * 1000)
        
        params = {
            'symbol': symbol,
            'side': side,
            'type': 'MARKET' if price is None else 'LIMIT',
            'quantity': quantity,
            'timestamp': timestamp
        }
        
        if price:
            params['price'] = price
            params['timeInForce'] = 'GTC'
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        signature = self._generate_signature(query_string)
        
        url = f"{self.base_url}/api/v3/order"
        data = f"{query_string}&signature={signature}"
        
        response = requests.post(url, data=data, headers=self._get_headers(True))
        return response.json()
    
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
    
    def cancel_order(self, symbol: str, order_id: int) -> Dict:
        """Отменить ордер"""
        timestamp = int(time.time() * 1000)
        query_string = f'symbol={symbol}&orderId={order_id}&timestamp={timestamp}'
        signature = self._generate_signature(query_string)
        
        url = f"{self.base_url}/api/v3/order"
        data = f"{query_string}&signature={signature}"
        
        response = requests.delete(url, data=data, headers=self._get_headers(True))
        return response.json()