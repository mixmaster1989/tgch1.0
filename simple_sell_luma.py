#!/usr/bin/env python3
"""
ПРОСТАЯ ПРОДАЖА LUMAUSDT
Без лишних модулей - только продажа!
"""

import json
import time
import hmac
import hashlib
import urllib.parse
from urllib.request import Request, urlopen

# Загружаем ключи из .env
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('MEXC_API_KEY')
SECRET_KEY = os.getenv('MEXC_SECRET_KEY')

def get_signature(query_string):
    """Создание подписи для API"""
    return hmac.new(
        SECRET_KEY.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

def make_request(endpoint, params=None, method='GET'):
    """Простой запрос к API"""
    base_url = "https://api.mexc.com"
    url = base_url + endpoint
    
    if params:
        query_string = urllib.parse.urlencode(params)
        url += "?" + query_string
    
    headers = {
        'X-MEXC-APIKEY': API_KEY,
        'Content-Type': 'application/json'
    }
    
    if method == 'POST':
        data = json.dumps(params).encode('utf-8')
        req = Request(url, data=data, headers=headers)
    else:
        req = Request(url, headers=headers)
    
    try:
        with urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return None

def get_luma_balance():
    """Получить баланс LUMA"""
    timestamp = int(time.time() * 1000)
    params = {
        'timestamp': timestamp,
        'recvWindow': 5000
    }
    
    signature = get_signature(urllib.parse.urlencode(params))
    params['signature'] = signature
    
    result = make_request('/api/v3/account', params)
    
    if result and 'balances' in result:
        for balance in result['balances']:
            if balance['asset'] == 'LUMA':
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                return free, locked, total
    
    return 0, 0, 0

def sell_luma(quantity):
    """Продать LUMA по рыночной цене"""
    timestamp = int(time.time() * 1000)
    
    params = {
        'symbol': 'LUMAUSDT',
        'side': 'SELL',
        'type': 'MARKET',
        'quantity': quantity,
        'timestamp': timestamp,
        'recvWindow': 5000
    }
    
    signature = get_signature(urllib.parse.urlencode(params))
    params['signature'] = signature
    
    result = make_request('/api/v3/order', params, 'POST')
    return result

def main():
    """Главная функция"""
    print("🚨 ПРОСТАЯ ПРОДАЖА LUMAUSDT")
    print("=" * 40)
    
    # Проверяем баланс
    print("🔍 Проверяем баланс LUMA...")
    free, locked, total = get_luma_balance()
    
    if total <= 0:
        print("❌ LUMA не найден в балансе")
        return
    
    print(f"💰 Найден LUMA:")
    print(f"   Свободно: {free}")
    print(f"   Заблокировано: {locked}")
    print(f"   Всего: {total}")
    
    # Продаем свободный LUMA
    if free > 0:
        print(f"\n🔥 Продаем {free} LUMA...")
        
        confirm = input("ПРОДАТЬ? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Отменено")
            return
        
        result = sell_luma(free)
        
        if result and 'orderId' in result:
            print(f"✅ LUMA ПРОДАН!")
            print(f"🆔 Ордер: {result['orderId']}")
            print(f"📊 Количество: {free}")
        else:
            print(f"❌ Ошибка продажи: {result}")
    else:
        print("❌ Нет свободного LUMA для продажи")

if __name__ == "__main__":
    print("⚠️  ВАЖНО: Замените API_KEY и SECRET_KEY на свои!")
    print("⚠️  В файле simple_sell_luma.py")
    print()
    
    # Проверяем ключи
    if not API_KEY or not SECRET_KEY:
        print("❌ API ключи не найдены в .env!")
        print("Проверьте MEXC_API_KEY и MEXC_SECRET_KEY")
    else:
        main() 