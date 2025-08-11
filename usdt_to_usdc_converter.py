#!/usr/bin/env python3
"""
Скрипт для конвертации USDT в USDC
"""

from mex_api import MexAPI
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class USDTtoUSDCConverter:
    def __init__(self):
        self.mex_api = MexAPI()
        
    def get_balances(self):
        """Получить текущие балансы USDT и USDC"""
        try:
            account_info = self.mex_api.get_account_info()
            usdt_balance = 0
            usdc_balance = 0
            
            for balance in account_info.get('balances', []):
                if balance['asset'] == 'USDT':
                    usdt_balance = float(balance['free'])
                elif balance['asset'] == 'USDC':
                    usdc_balance = float(balance['free'])
            
            return usdt_balance, usdc_balance
            
        except Exception as e:
            logger.error(f"Ошибка получения балансов: {e}")
            return 0, 0
    
    def get_usdc_price(self):
        """Получить текущую цену USDC в USDT"""
        try:
            price_info = self.mex_api.get_ticker_price('USDCUSDT')
            if 'price' in price_info:
                return float(price_info['price'])
            return 1.0  # По умолчанию 1:1
        except Exception as e:
            logger.error(f"Ошибка получения цены USDC: {e}")
            return 1.0
    
    def convert_usdt_to_usdc(self, usdt_amount: float):
        """Конвертировать USDT в USDC"""
        try:
            logger.info(f"🔄 Конвертация {usdt_amount} USDT в USDC...")
            
            # Получаем текущую цену USDC
            usdc_price = self.get_usdc_price()
            logger.info(f"Текущая цена USDC: {usdc_price} USDT")
            
            # Рассчитываем количество USDC
            usdc_quantity = usdt_amount / usdc_price
            logger.info(f"Получим примерно: {usdc_quantity:.4f} USDC")
            
            # Размещаем ордер на покупку USDC
            order = self.mex_api.place_order(
                symbol='USDCUSDT',
                side='BUY',
                quantity=usdc_quantity,
                price=usdc_price  # Покупаем по текущей цене
            )
            
            if 'orderId' in order:
                logger.info(f"✅ Ордер на конвертацию создан: {order['orderId']}")
                logger.info(f"📋 Детали ордера: {order}")
                return order
            else:
                logger.error(f"❌ Ошибка создания ордера: {order}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка конвертации: {e}")
            return None
    
    def wait_for_order_completion(self, order_id: str, max_wait: int = 60):
        """Ожидать завершения ордера"""
        logger.info(f"⏳ Ожидание завершения ордера {order_id}...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                # Получаем статус ордера
                open_orders = self.mex_api.get_open_orders('USDCUSDT')
                
                # Проверяем, есть ли наш ордер в открытых
                order_found = False
                for order in open_orders:
                    if order.get('orderId') == order_id:
                        order_found = True
                        status = order.get('status', 'UNKNOWN')
                        logger.info(f"Статус ордера: {status}")
                        break
                
                if not order_found:
                    logger.info("✅ Ордер выполнен!")
                    return True
                
                time.sleep(5)  # Проверяем каждые 5 секунд
                
            except Exception as e:
                logger.error(f"Ошибка проверки статуса: {e}")
                time.sleep(5)
        
        logger.warning("⏰ Время ожидания истекло")
        return False
    
    def show_final_balances(self):
        """Показать финальные балансы"""
        usdt_balance, usdc_balance = self.get_balances()
        logger.info(f"💰 Финальные балансы:")
        logger.info(f"   USDT: {usdt_balance:.4f}")
        logger.info(f"   USDC: {usdc_balance:.4f}")

def main():
    converter = USDTtoUSDCConverter()
    
    # Показываем начальные балансы
    usdt_balance, usdc_balance = converter.get_balances()
    logger.info(f"💰 Начальные балансы:")
    logger.info(f"   USDT: {usdt_balance:.4f}")
    logger.info(f"   USDC: {usdc_balance:.4f}")
    
    # Конвертируем $50 USDT в USDC
    convert_amount = 50.0
    
    if usdt_balance < convert_amount:
        logger.error(f"❌ Недостаточно USDT. Доступно: {usdt_balance:.2f}, нужно: {convert_amount}")
        return
    
    # Выполняем конвертацию
    order = converter.convert_usdt_to_usdc(convert_amount)
    
    if order:
        # Ждем завершения ордера
        if converter.wait_for_order_completion(order['orderId']):
            # Показываем финальные балансы
            converter.show_final_balances()
        else:
            logger.warning("⚠️ Не удалось дождаться завершения ордера")
    else:
        logger.error("❌ Конвертация не удалась")

if __name__ == "__main__":
    main() 