#!/usr/bin/env python3
"""
ОТЛАДКА ПРОДАЖИ LUMAUSDT
Проверяем параметры API
"""

import json
import time
import hmac
import hashlib
import urllib.parse
from urllib.request import Request, urlopen

# Загружаем ключи
def load_env():
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    except:
        pass
    return env_vars

env = load_env()
API_KEY = env.get('MEX_API_KEY', '')
SECRET_KEY = env.get('MEX_SECRET_KEY', '')

def get_signature(query_string):
    return hmac.new(
        SECRET_KEY.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def test_api():
    """Тестируем API"""
    print("🔍 ТЕСТИРУЕМ API MEXC")
    print("=" * 30)
    
    # Тест 1: Получить информацию об аккаунте
    print("1️⃣ Тест получения баланса...")
    timestamp = int(time.time() * 1000)
    params = {
        'timestamp': timestamp,
        'recvWindow': 5000
    }
    
    signature = get_signature(urllib.parse.urlencode(params))
    params['signature'] = signature
    
    url = "https://api.mexc.com/api/v3/account?" + urllib.parse.urlencode(params)
    headers = {'X-MEXC-APIKEY': API_KEY}
    
    try:
        req = Request(url, headers=headers)
        with urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(f"✅ Баланс получен: {len(result.get('balances', []))} активов")
            
            # Ищем LUMA
            for balance in result.get('balances', []):
                if balance['asset'] == 'LUMA':
                    free = float(balance['free'])
                    print(f"💰 LUMA найден: {free}")
                    return free
    except Exception as e:
        print(f"❌ Ошибка получения баланса: {e}")
        return 0

def test_order_params(quantity):
    """Тестируем параметры ордера"""
    print(f"\n2️⃣ Тест параметров ордера для {quantity} LUMA...")
    
    timestamp = int(time.time() * 1000)
    
    # Пробуем разные варианты параметров
    test_cases = [
        {
            'symbol': 'LUMAUSDT',
            'side': 'SELL',
            'type': 'MARKET',
            'quantity': str(quantity),
            'timestamp': timestamp,
            'recvWindow': 5000
        },
        {
            'symbol': 'LUMAUSDT',
            'side': 'SELL',
            'type': 'MARKET',
            'quantity': str(round(quantity, 2)),
            'timestamp': timestamp,
            'recvWindow': 5000
        }
    ]
    
    for i, params in enumerate(test_cases, 1):
        print(f"\nТест {i}:")
        print(f"Параметры: {json.dumps(params, indent=2)}")
        
        signature = get_signature(urllib.parse.urlencode(params))
        params['signature'] = signature
        
        url = "https://api.mexc.com/api/v3/order"
        headers = {
            'X-MEXC-APIKEY': API_KEY,
            'Content-Type': 'application/json'
        }
        
        try:
            data = json.dumps(params).encode('utf-8')
            req = Request(url, data=data, headers=headers)
            with urlopen(req) as response:
                result = json.loads(response.read().decode())
                print(f"✅ Успех: {result}")
                return True
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            if hasattr(e, 'read'):
                try:
                    error_body = e.read().decode()
                    print(f"Детали ошибки: {error_body}")
                except:
                    pass
    
    return False

def main():
    print("🚨 ОТЛАДКА ПРОДАЖИ LUMAUSDT")
    print("=" * 40)
    
    if not API_KEY or not SECRET_KEY:
        print("❌ API ключи не найдены!")
        return
    
    print("✅ API ключи загружены")
    
    # Тест 1: Получаем баланс
    luma_balance = test_api()
    
    if luma_balance <= 0:
        print("❌ LUMA не найден")
        return
    
    # Тест 2: Проверяем параметры ордера
    test_order_params(luma_balance)

if __name__ == "__main__":
    main() 