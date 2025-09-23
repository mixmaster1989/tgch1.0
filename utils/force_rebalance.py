#!/usr/bin/env python3
"""
Принудительная ребалансировка BTC/ETH через API лимитными ордерами
"""

from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests
import time
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ForceRebalancer:
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Целевое распределение
        self.target_btc_percent = 60.0
        self.target_eth_percent = 40.0
        
    def send_telegram_message(self, message: str):
        """Отправить сообщение в Telegram"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {'chat_id': self.chat_id, 'text': message, 'parse_mode': 'HTML'}
        try:
            response = requests.post(url, data=data)
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
            return None
    
    def get_current_allocation(self):
        """Получить текущее распределение портфеля"""
        try:
            account_info = self.mex_api.get_account_info()
            btc_balance = 0.0
            eth_balance = 0.0
            
            for balance in account_info.get('balances', []):
                asset = balance['asset']
                if asset == 'BTC':
                    btc_balance = float(balance['free']) + float(balance['locked'])
                elif asset == 'ETH':
                    eth_balance = float(balance['free']) + float(balance['locked'])
            
            # Получаем цены
            btc_price = self.mex_api.get_ticker_price('BTCUSDC')
            eth_price = self.mex_api.get_ticker_price('ETHUSDC')
            
            if 'price' in btc_price and 'price' in eth_price:
                btc_price = float(btc_price['price'])
                eth_price = float(eth_price['price'])
                
                btc_value = btc_balance * btc_price
                eth_value = eth_balance * eth_price
                total_crypto = btc_value + eth_value
                
                if total_crypto > 0:
                    return {
                        'btc_balance': btc_balance,
                        'eth_balance': eth_balance,
                        'btc_value': btc_value,
                        'eth_value': eth_value,
                        'total_crypto': total_crypto,
                        'btc_percent': (btc_value / total_crypto) * 100,
                        'eth_percent': (eth_value / total_crypto) * 100,
                        'btc_price': btc_price,
                        'eth_price': eth_price
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения распределения: {e}")
            return None
    
    def calculate_rebalance_orders(self, allocation):
        """Рассчитать ордера для ребалансировки"""
        try:
            btc_percent = allocation['btc_percent']
            eth_percent = allocation['eth_percent']
            total_crypto = allocation['total_crypto']
            
            logger.info(f"📊 Текущее распределение: BTC {btc_percent:.1f}%, ETH {eth_percent:.1f}%")
            logger.info(f"🎯 Целевое распределение: BTC {self.target_btc_percent}%, ETH {self.target_eth_percent}%")
            
            orders = []
            
            # Рассчитываем целевые значения
            target_btc_value = total_crypto * (self.target_btc_percent / 100)
            target_eth_value = total_crypto * (self.target_eth_percent / 100)
            
            current_btc_value = allocation['btc_value']
            current_eth_value = allocation['eth_value']
            
            # Проверяем BTC
            if btc_percent > self.target_btc_percent:
                # BTC слишком много - нужно продать
                excess_btc_value = current_btc_value - target_btc_value
                excess_btc_quantity = excess_btc_value / allocation['btc_price']
                
                if excess_btc_quantity >= 0.0001:  # Минимум для BTC
                    orders.append({
                        'symbol': 'BTCUSDC',
                        'side': 'SELL',
                        'quantity': round(excess_btc_quantity, 6),
                        'value': excess_btc_value,
                        'reason': f'Продажа избытка BTC ({btc_percent:.1f}% → {self.target_btc_percent}%)'
                    })
                    logger.info(f"📤 Продажа BTC: {excess_btc_quantity:.6f} BTC на ${excess_btc_value:.2f}")
            
            elif btc_percent < self.target_btc_percent:
                # BTC слишком мало - нужно купить
                needed_btc_value = target_btc_value - current_btc_value
                needed_btc_quantity = needed_btc_value / allocation['btc_price']
                
                if needed_btc_quantity >= 0.0001:  # Минимум для BTC
                    orders.append({
                        'symbol': 'BTCUSDC',
                        'side': 'BUY',
                        'quantity': round(needed_btc_quantity, 6),
                        'value': needed_btc_value,
                        'reason': f'Покупка недостающего BTC ({btc_percent:.1f}% → {self.target_btc_percent}%)'
                    })
                    logger.info(f"📥 Покупка BTC: {needed_btc_quantity:.6f} BTC на ${needed_btc_value:.2f}")
            
            # Проверяем ETH
            if eth_percent > self.target_eth_percent:
                # ETH слишком много - нужно продать
                excess_eth_value = current_eth_value - target_eth_value
                excess_eth_quantity = excess_eth_value / allocation['eth_price']
                
                if excess_eth_quantity >= 0.001:  # Минимум для ETH
                    orders.append({
                        'symbol': 'ETHUSDC',
                        'side': 'SELL',
                        'quantity': round(excess_eth_quantity, 6),
                        'value': excess_eth_value,
                        'reason': f'Продажа избытка ETH ({eth_percent:.1f}% → {self.target_eth_percent}%)'
                    })
                    logger.info(f"📤 Продажа ETH: {excess_eth_quantity:.6f} ETH на ${excess_eth_value:.2f}")
            
            elif eth_percent < self.target_eth_percent:
                # ETH слишком мало - нужно купить
                needed_eth_value = target_eth_value - current_eth_value
                needed_eth_quantity = needed_eth_value / allocation['eth_price']
                
                if needed_eth_quantity >= 0.001:  # Минимум для ETH
                    orders.append({
                        'symbol': 'ETHUSDC',
                        'side': 'BUY',
                        'quantity': round(needed_eth_quantity, 6),
                        'value': needed_eth_value,
                        'reason': f'Покупка недостающего ETH ({eth_percent:.1f}% → {self.target_eth_percent}%)'
                    })
                    logger.info(f"📥 Покупка ETH: {needed_eth_quantity:.6f} ETH на ${needed_eth_value:.2f}")
            
            return orders
            
        except Exception as e:
            logger.error(f"Ошибка расчета ордеров ребалансировки: {e}")
            return []
    
    def get_limit_price(self, symbol: str, side: str):
        """Получить лимитную цену для ордера"""
        try:
            # Получаем стакан
            orderbook = self.mex_api.get_depth(symbol, limit=10)
            
            if 'bids' in orderbook and 'asks' in orderbook:
                best_bid = float(orderbook['bids'][0][0])
                best_ask = float(orderbook['asks'][0][0])
                
                if side == 'BUY':
                    # Для покупки - ставим чуть ниже лучшей цены продажи
                    return best_ask * 0.9995  # На 0.05% ниже
                else:
                    # Для продажи - ставим чуть выше лучшей цены покупки
                    return best_bid * 1.0005  # На 0.05% выше
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения цены для {symbol}: {e}")
            return None
    
    def place_rebalance_order(self, order_info):
        """Разместить ордер ребалансировки"""
        try:
            symbol = order_info['symbol']
            side = order_info['side']
            quantity = order_info['quantity']
            
            logger.info(f"🔄 Размещение ордера ребалансировки: {side} {quantity} {symbol}")
            
            # Получаем лимитную цену
            limit_price = self.get_limit_price(symbol, side)
            
            if not limit_price:
                logger.error(f"Не удалось получить цену для {symbol}")
                return {'success': False, 'error': 'Не удалось получить цену'}
            
            logger.info(f"💰 Лимитная цена: ${limit_price:.4f}")
            
            # Проверяем баланс для покупки
            if side == 'BUY':
                usdc_balance = 0.0
                account_info = self.mex_api.get_account_info()
                for balance in account_info.get('balances', []):
                    if balance['asset'] == 'USDC':
                        usdc_balance = float(balance['free'])
                        break
                
                required_usdc = quantity * limit_price
                if required_usdc > usdc_balance:
                    logger.error(f"Недостаточно USDC: нужно ${required_usdc:.2f}, доступно ${usdc_balance:.2f}")
                    return {'success': False, 'error': f'Недостаточно USDC: нужно ${required_usdc:.2f}'}
            
            # Размещаем ордер
            order = self.mex_api.place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=limit_price
            )
            
            if order and 'orderId' in order:
                logger.info(f"✅ Ордер размещен: {order['orderId']}")
                return {
                    'success': True,
                    'order_id': order['orderId'],
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': limit_price,
                    'order': order
                }
            else:
                logger.error(f"❌ Ошибка размещения ордера: {order}")
                return {'success': False, 'error': f'API ошибка: {order}'}
                
        except Exception as e:
            logger.error(f"Ошибка размещения ордера ребалансировки: {e}")
            return {'success': False, 'error': str(e)}
    
    def execute_force_rebalance(self):
        """Выполнить принудительную ребалансировку"""
        try:
            logger.info("🚀 ЗАПУСК ПРИНУДИТЕЛЬНОЙ РЕБАЛАНСИРОВКИ BTC/ETH")
            
            # Получаем текущее распределение
            allocation = self.get_current_allocation()
            
            if not allocation:
                logger.error("Не удалось получить текущее распределение")
                return
            
            # Рассчитываем ордера ребалансировки
            rebalance_orders = self.calculate_rebalance_orders(allocation)
            
            if not rebalance_orders:
                logger.info("✅ Ребалансировка не требуется - распределение в норме")
                return
            
            logger.info(f"📋 Найдено {len(rebalance_orders)} ордеров для ребалансировки")
            
            # Выполняем ордера
            results = []
            for order_info in rebalance_orders:
                logger.info(f"\n🔄 Выполнение: {order_info['reason']}")
                result = self.place_rebalance_order(order_info)
                results.append({
                    'order_info': order_info,
                    'result': result
                })
                
                # Пауза между ордерами
                time.sleep(2)
            
            # Отправляем отчет
            self.send_rebalance_report(allocation, rebalance_orders, results)
            
        except Exception as e:
            logger.error(f"Ошибка принудительной ребалансировки: {e}")
    
    def send_rebalance_report(self, allocation, orders, results):
        """Отправить отчет о ребалансировке"""
        try:
            message = f"<b>🔄 ПРИНУДИТЕЛЬНАЯ РЕБАЛАНСИРОВКА BTC/ETH</b>\n\n"
            
            message += f"📊 <b>ДО РЕБАЛАНСИРОВКИ:</b>\n"
            message += f"💚 BTC: {allocation['btc_percent']:.1f}% (${allocation['btc_value']:.2f})\n"
            message += f"💙 ETH: {allocation['eth_percent']:.1f}% (${allocation['eth_value']:.2f})\n"
            message += f"💰 Всего: ${allocation['total_crypto']:.2f}\n\n"
            
            message += f"🎯 <b>ЦЕЛЬ:</b> BTC {self.target_btc_percent}% / ETH {self.target_eth_percent}%\n\n"
            
            if results:
                message += f"📋 <b>ВЫПОЛНЕННЫЕ ОРДЕРА:</b>\n"
                for result in results:
                    order_info = result['order_info']
                    order_result = result['result']
                    
                    if order_result['success']:
                        message += f"✅ {order_info['reason']}\n"
                        message += f"   📊 {order_info['symbol']} {order_result['side']} {order_info['quantity']}\n"
                        message += f"   💰 ${order_info['value']:.2f}\n"
                        message += f"   🆔 {order_result['order_id']}\n\n"
                    else:
                        message += f"❌ {order_info['reason']}\n"
                        message += f"   💥 Ошибка: {order_result['error']}\n\n"
            else:
                message += f"✅ Ребалансировка не требуется\n\n"
            
            message += f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
            
            self.send_telegram_message(message)
            
        except Exception as e:
            logger.error(f"Ошибка отправки отчета: {e}")

def main():
    rebalancer = ForceRebalancer()
    rebalancer.execute_force_rebalance()

if __name__ == "__main__":
    main() 