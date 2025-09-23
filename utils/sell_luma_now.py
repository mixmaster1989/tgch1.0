#!/usr/bin/env python3
"""
ПРОДАЕМ LUMA ПРЯМО СЕЙЧАС!
Максимально простой скрипт
"""

import json
import time
import hmac
import hashlib
import urllib.parse
from urllib.request import Request, urlopen

print("🚨 ПРОДАЕМ LUMA ПРЯМО СЕЙЧАС!")
print("=" * 40)

# Загружаем ключи из .env
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

API_KEY = env_vars.get('MEX_API_KEY', '')
SECRET_KEY = env_vars.get('MEX_SECRET_KEY', '')

if not API_KEY or not SECRET_KEY:
    print("❌ API ключи не найдены!")
    exit()

print("✅ API ключи загружены")

# 1. Получаем баланс LUMA
print("🔍 Получаем баланс LUMA...")
timestamp = int(time.time() * 1000)
params = {
    'timestamp': timestamp,
    'recvWindow': 5000
}

query_string = urllib.parse.urlencode(params)
signature = hmac.new(
    SECRET_KEY.encode('utf-8'),
    query_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()

params['signature'] = signature
url = "https://api.mexc.com/api/v3/account?" + urllib.parse.urlencode(params)
headers = {'X-MEXC-APIKEY': API_KEY}

try:
    req = Request(url, headers=headers)
    with urlopen(req) as response:
        result = json.loads(response.read().decode())
        
        luma_balance = 0
        for balance in result.get('balances', []):
            if balance['asset'] == 'LUMA':
                luma_balance = float(balance['free'])
                break
        
        if luma_balance <= 0:
            print("❌ LUMA не найден в балансе")
            exit()
        
        print(f"💰 Найден LUMA: {luma_balance}")
        
except Exception as e:
    print(f"❌ Ошибка получения баланса: {e}")
    exit()

# 2. Продаем LUMA
print(f"🔥 Продаем {luma_balance} LUMA...")

# Округляем до 2 знаков
quantity = round(luma_balance, 2)
print(f"📊 Количество для продажи: {quantity}")

# Создаем параметры ордера
order_params = {
    'symbol': 'LUMAUSDT',
    'side': 'SELL',
    'type': 'MARKET',
    'quantity': str(quantity),
    'timestamp': int(time.time() * 1000),
    'recvWindow': 5000
}

# Создаем подпись для POST запроса
# MEXC требует параметры в URL для подписи, но отправляем в body
url_params = order_params.copy()
body_string = urllib.parse.urlencode(url_params)
signature = hmac.new(
    SECRET_KEY.encode('utf-8'),
    body_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()

# Добавляем подпись в параметры
order_params['signature'] = signature

# Отправляем ордер
url = "https://api.mexc.com/api/v3/order"
headers = {
    'X-MEXC-APIKEY': API_KEY,
    'Content-Type': 'application/json'
}

try:
    data = json.dumps(order_params).encode('utf-8')
    req = Request(url, data=data, headers=headers)
    
    with urlopen(req) as response:
        result = json.loads(response.read().decode())
        
        if 'orderId' in result:
            print(f"✅ LUMA ПРОДАН УСПЕШНО!")
            print(f"🆔 Ордер: {result['orderId']}")
            print(f"📊 Количество: {quantity}")
            print(f"💰 Символ: LUMAUSDT")
        else:
            print(f"❌ Ошибка продажи: {result}")
            
except Exception as e:
    print(f"❌ Ошибка отправки ордера: {e}")
    if hasattr(e, 'read'):
        try:
            error_body = e.read().decode()
            print(f"Детали ошибки: {error_body}")
        except:
            pass

print("\n🏁 Скрипт завершен") 