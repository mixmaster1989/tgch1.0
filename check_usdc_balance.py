#!/usr/bin/env python3
"""
Проверка точного баланса USDC
"""

from mex_api import MexAPI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_usdc_balance():
    api = MexAPI()

    try:
        account_info = api.get_account_info()
        usdc_balance = 0

        print("ПРОВЕРКА БАЛАНСА USDC")
        print("=" * 40)

        for balance in account_info.get('balances', []):
            if balance['asset'] == 'USDC':
                free = float(balance.get('free', 0))
                locked = float(balance.get('locked', 0))
                usdc_balance = free + locked

                print(f"💰 USDC FREE: ${free:.2f}")
                print(f"🔒 USDC LOCKED: ${locked:.2f}")
                print(f"📊 USDC TOTAL: ${usdc_balance:.2f}")

                return usdc_balance

    except Exception as e:
        print(f"❌ Ошибка получения баланса: {e}")
        return 0

if __name__ == "__main__":
    balance = check_usdc_balance()