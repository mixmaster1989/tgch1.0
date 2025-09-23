#!/usr/bin/env python3
"""
Покупка USDC на доступные USDT
"""

import logging
from datetime import datetime
from mex_api import MexAPI

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Основная функция"""
    try:
        logger.info("🚀 Покупка USDC на доступные USDT...")
        
        # Инициализируем API
        mex_api = MexAPI()
        
        # Получаем балансы
        account_info = mex_api.get_account_info()
        if 'balances' not in account_info:
            logger.error("Не удалось получить балансы")
            return
        
        # Находим баланс USDT
        usdt_balance = 0.0
        for balance in account_info['balances']:
            if balance['asset'] == 'USDT':
                usdt_balance = float(balance['free'])
                break
        
        logger.info(f"💰 Баланс USDT: ${usdt_balance:.2f}")
        
        if usdt_balance < 1.0:
            logger.warning("Недостаточно USDT для покупки USDC")
            return
        
        # Покупаем USDC с запасом на комиссии
        buy_amount = usdt_balance * 0.99  # 1% запас на комиссии
        
        # Округляем до 2 знаков после запятой для USDC
        buy_amount = round(buy_amount, 2)
        
        logger.info(f"📥 Покупаем USDC на ${buy_amount:.2f}...")
        
        # Размещаем рыночный ордер
        order = mex_api.place_order(
            symbol='USDCUSDT',
            side='BUY',
            quantity=buy_amount,
            price=None  # Рыночный ордер
        )
        
        logger.info(f"✅ Ордер размещен: {order}")
        
        print("\n" + "="*50)
        print("✅ ПОКУПКА USDC ЗАВЕРШЕНА")
        print("="*50)
        print(f"💰 Потрачено USDT: ${buy_amount:.2f}")
        print(f"📥 Куплено USDC: ~${buy_amount:.2f}")
        print(f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}")
        print("="*50)
        
    except Exception as e:
        logger.error(f"Ошибка покупки USDC: {e}")
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
