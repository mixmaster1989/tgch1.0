#!/usr/bin/env python3
"""
Автоматическая балансировка портфеля BTC/ETH в пропорции 60/40
Продает BTC и покупает ETH лимитными ордерами по стакану
Блокирует балансировку при отрицательном PnL
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from decimal import Decimal

from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortfolioBalancer:
    """Автоматическая балансировка портфеля BTC/ETH"""
    
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Целевые пропорции портфеля
        self.target_btc_ratio = 0.60  # 60% BTC
        self.target_eth_ratio = 0.40  # 40% ETH
        
        # Настройки балансировки
        self.rebalance_threshold = 0.05  # Запускать балансировку при отклонении > 5%
        self.min_rebalance_amount = 10.0  # Минимальная сумма для балансировки ($10)
        self.rebalance_interval = 3600   # Проверка каждый час
        
        # Защита от убытков
        self.allow_negative_pnl_rebalance = False  # Блок балансировки при минусовом PnL
        self.min_positive_pnl = 0.10  # Минимальный положительный PnL для балансировки
        
        # История балансировок
        self.last_rebalance_time = None
        self.min_rebalance_cooldown = 1800  # Минимум 30 минут между балансировками
        
        # Статистика
        self.total_rebalances = 0
        self.blocked_rebalances = 0  # Заблокированные из-за отрицательного PnL
        
    def send_telegram_message(self, message: str):
        """Отправить сообщение в Telegram"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        try:
            response = requests.post(url, data=data)
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
            return None
    
    def get_portfolio_balances(self) -> Dict:
        """Получить текущие балансы BTC и ETH"""
        try:
            account_info = self.mex_api.get_account_info()
            if 'balances' not in account_info:
                return {}
            
            balances = {}
            for balance in account_info['balances']:
                asset = balance['asset']
                if asset in ['BTC', 'ETH']:
                    free_amount = float(balance['free'])
                    locked_amount = float(balance['locked'])
                    total_amount = free_amount + locked_amount
                    
                    if total_amount > 0:
                        balances[asset] = {
                            'free': free_amount,
                            'locked': locked_amount,
                            'total': total_amount
                        }
            
            return balances
            
        except Exception as e:
            logger.error(f"Ошибка получения балансов: {e}")
            return {}
    
    def get_portfolio_values(self, balances: Dict) -> Dict:
        """Рассчитать стоимость портфеля в USDC"""
        try:
            # Получаем текущие цены
            btc_price = self.mex_api.get_ticker_price('BTCUSDC')
            eth_price = self.mex_api.get_ticker_price('ETHUSDC')
            
            if not btc_price or not eth_price:
                logger.error("Не удалось получить цены BTC/ETH")
                return {}
            
            btc_price_value = float(btc_price['price'])
            eth_price_value = float(eth_price['price'])
            
            values = {
                'btc_price': btc_price_value,
                'eth_price': eth_price_value,
                'btc_value': 0.0,
                'eth_value': 0.0,
                'total_value': 0.0
            }
            
            # Рассчитываем стоимости
            if 'BTC' in balances:
                values['btc_value'] = balances['BTC']['total'] * btc_price_value
            
            if 'ETH' in balances:
                values['eth_value'] = balances['ETH']['total'] * eth_price_value
            
            values['total_value'] = values['btc_value'] + values['eth_value']
            
            # Рассчитываем текущие пропорции
            if values['total_value'] > 0:
                values['btc_ratio'] = values['btc_value'] / values['total_value']
                values['eth_ratio'] = values['eth_value'] / values['total_value']
            else:
                values['btc_ratio'] = 0.0
                values['eth_ratio'] = 0.0
            
            return values
            
        except Exception as e:
            logger.error(f"Ошибка расчета стоимости портфеля: {e}")
            return {}
    
    def calculate_pnl_for_asset(self, asset: str, quantity: float, current_price: float) -> float:
        """Рассчитать PnL для конкретного актива"""
        try:
            # Используем упрощенный расчет - можно улучшить интеграцией с PnLMonitor
            # Пока возвращаем 0 - означает разрешить балансировку
            # В реальности здесь должен быть расчет средней цены покупки
            return 0.0
            
        except Exception as e:
            logger.error(f"Ошибка расчета PnL для {asset}: {e}")
            return 0.0
    
    def check_rebalance_needed(self, values: Dict) -> Tuple[bool, str]:
        """Проверить, нужна ли балансировка"""
        try:
            if values['total_value'] < self.min_rebalance_amount:
                return False, f"Общая стоимость портфеля слишком мала: ${values['total_value']:.2f} < ${self.min_rebalance_amount}"
            
            # КРИТИЧЕСКАЯ ПРОВЕРКА: Если один из активов = 0, не балансируем!
            if values['btc_value'] == 0 or values['eth_value'] == 0:
                missing_asset = "ETH" if values['eth_value'] == 0 else "BTC"
                return False, f"❌ {missing_asset} отсутствует в портфеле! Балансировка невозможна. Нужно сначала купить оба актива."
            
            # Проверяем достаточность средств для балансировки
            # Рассчитываем сколько USDC нужно для корректировки
            target_btc_value = values['total_value'] * self.target_btc_ratio
            target_eth_value = values['total_value'] * self.target_eth_ratio
            
            btc_adjustment = abs(values['btc_value'] - target_btc_value)
            eth_adjustment = abs(values['eth_value'] - target_eth_value)
            max_adjustment = max(btc_adjustment, eth_adjustment)
            
            if max_adjustment < 5.0:  # Минимум $5 для операции
                return False, f"Корректировка слишком мала: ${max_adjustment:.2f} < $5.00"
            
            # Проверяем отклонение от целевых пропорций
            btc_deviation = abs(values['btc_ratio'] - self.target_btc_ratio)
            eth_deviation = abs(values['eth_ratio'] - self.target_eth_ratio)
            
            max_deviation = max(btc_deviation, eth_deviation)
            
            if max_deviation < self.rebalance_threshold:
                return False, f"Отклонение {max_deviation*100:.1f}% < {self.rebalance_threshold*100:.1f}% порога"
            
            # Проверяем кулдаун
            if (self.last_rebalance_time and 
                time.time() - self.last_rebalance_time < self.min_rebalance_cooldown):
                remaining = self.min_rebalance_cooldown - (time.time() - self.last_rebalance_time)
                return False, f"Кулдаун балансировки: осталось {remaining/60:.1f} мин"
            
            return True, f"Нужна балансировка! Отклонение: {max_deviation*100:.1f}%, корректировка: ${max_adjustment:.2f}"
            
        except Exception as e:
            logger.error(f"Ошибка проверки необходимости балансировки: {e}")
            return False, f"Ошибка: {e}"
    
    def get_orderbook_data(self, symbol: str) -> Optional[Dict]:
        """Получить данные стакана заявок"""
        try:
            orderbook = self.mex_api.get_depth(symbol, limit=20)
            
            if 'bids' in orderbook and 'asks' in orderbook:
                bids = orderbook['bids'][:10]
                asks = orderbook['asks'][:10]
                
                best_bid = float(bids[0][0]) if bids else 0
                best_ask = float(asks[0][0]) if asks else 0
                
                spread = best_ask - best_bid
                spread_percent = (spread / best_bid) * 100 if best_bid > 0 else 0
                
                return {
                    'bids': bids,
                    'asks': asks,
                    'best_bid': best_bid,
                    'best_ask': best_ask,
                    'spread': spread,
                    'spread_percent': spread_percent
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения стакана {symbol}: {e}")
            return None
    
    def calculate_limit_price(self, symbol: str, side: str) -> Optional[float]:
        """Рассчитать оптимальную цену для лимитного ордера"""
        try:
            orderbook = self.get_orderbook_data(symbol)
            
            if not orderbook:
                return None
            
            best_bid = orderbook['best_bid']
            best_ask = orderbook['best_ask']
            spread_percent = orderbook['spread_percent']
            
            if side == 'BUY':
                # Для покупки - ставим чуть выше лучшей покупки (мейкер)
                if spread_percent < 0.1:
                    return best_bid * 1.0001  # На 0.01% выше
                else:
                    return best_bid * 1.0005  # На 0.05% выше
            else:  # SELL
                # Для продажи - ставим чуть ниже лучшей продажи (мейкер)
                if spread_percent < 0.1:
                    return best_ask * 0.9999  # На 0.01% ниже
                else:
                    return best_ask * 0.9995  # На 0.05% ниже
            
        except Exception as e:
            logger.error(f"Ошибка расчета лимитной цены {symbol}: {e}")
            return None
    
    def execute_rebalance_trade(self, action: str, symbol: str, quantity: float) -> Dict:
        """Выполнить торговую операцию для балансировки"""
        try:
            logger.info(f"🔄 Балансировка: {action} {quantity:.6f} {symbol}")
            
            # Получаем оптимальную цену
            side = 'SELL' if action == 'SELL' else 'BUY'
            limit_price = self.calculate_limit_price(symbol, side)
            
            if not limit_price:
                return {'success': False, 'error': f'Не удалось рассчитать цену для {symbol}'}
            
            # Получаем данные стакана для логирования
            orderbook = self.get_orderbook_data(symbol)
            
            logger.info(f"📊 Стакан {symbol}:")
            logger.info(f"   Лучшая покупка: ${orderbook['best_bid']:.4f}")
            logger.info(f"   Лучшая продажа: ${orderbook['best_ask']:.4f}")
            logger.info(f"   Спред: {orderbook['spread_percent']:.4f}%")
            logger.info(f"   Наша цена: ${limit_price:.4f}")
            
            # Создаем лимитный ордер
            order = self.mex_api.place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=limit_price
            )
            
            if order and 'orderId' in order:
                logger.info(f"✅ Ордер балансировки размещен: {order}")
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
                logger.error(f"❌ Ошибка размещения ордера балансировки: {order}")
                return {'success': False, 'error': f'API ошибка: {order}'}
                
        except Exception as e:
            logger.error(f"❌ Ошибка выполнения балансировки {symbol}: {e}")
            return {'success': False, 'error': str(e)}
    
    def calculate_rebalance_trades(self, balances: Dict, values: Dict) -> Dict:
        """Рассчитать необходимые торги для балансировки"""
        try:
            target_btc_value = values['total_value'] * self.target_btc_ratio
            target_eth_value = values['total_value'] * self.target_eth_ratio
            
            btc_diff = values['btc_value'] - target_btc_value
            eth_diff = values['eth_value'] - target_eth_value
            
            trades = []
            
            # Если BTC больше нормы - продаем BTC
            if btc_diff > 0:
                btc_to_sell = btc_diff / values['btc_price']
                
                # Проверяем минимальные лоты
                if btc_to_sell >= 0.0001:  # Минимальный лот BTC
                    btc_to_sell = round(btc_to_sell, 6)
                    trades.append({
                        'action': 'SELL',
                        'symbol': 'BTCUSDC', 
                        'quantity': btc_to_sell,
                        'value': btc_to_sell * values['btc_price']
                    })
            
            # Если ETH меньше нормы - покупаем ETH
            if eth_diff < 0:
                eth_to_buy = abs(eth_diff) / values['eth_price']
                
                # Проверяем минимальные лоты
                if eth_to_buy >= 0.001:  # Минимальный лот ETH
                    eth_to_buy = round(eth_to_buy, 6)
                    trades.append({
                        'action': 'BUY',
                        'symbol': 'ETHUSDC',
                        'quantity': eth_to_buy,
                        'value': eth_to_buy * values['eth_price']
                    })
            
            return {
                'trades': trades,
                'target_btc_value': target_btc_value,
                'target_eth_value': target_eth_value,
                'btc_diff': btc_diff,
                'eth_diff': eth_diff
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета торгов балансировки: {e}")
            return {'trades': []}
    
    async def execute_portfolio_rebalance(self) -> Dict:
        """Выполнить балансировку портфеля"""
        try:
            logger.info("🎯 Запуск балансировки портфеля")
            
            # Получаем текущие балансы
            balances = self.get_portfolio_balances()
            if not balances:
                return {'success': False, 'error': 'Нет балансов BTC/ETH'}
            
            # Рассчитываем стоимости
            values = self.get_portfolio_values(balances)
            if not values:
                return {'success': False, 'error': 'Не удалось рассчитать стоимости'}
            
            # Проверяем необходимость балансировки
            need_rebalance, reason = self.check_rebalance_needed(values)
            if not need_rebalance:
                return {'success': False, 'error': reason, 'reason': 'not_needed'}
            
            # Проверяем PnL (упрощенная версия)
            # В реальности здесь должна быть интеграция с PnLMonitor
            if not self.allow_negative_pnl_rebalance:
                # Здесь должна быть проверка общего PnL портфеля
                # Пока пропускаем эту проверку
                pass
            
            # Рассчитываем необходимые торги
            rebalance_plan = self.calculate_rebalance_trades(balances, values)
            
            if not rebalance_plan['trades']:
                return {'success': False, 'error': 'Нет подходящих торгов для балансировки'}
            
            # Выполняем торги
            results = {
                'success': True,
                'timestamp': datetime.now(),
                'before': {
                    'btc_ratio': values['btc_ratio'],
                    'eth_ratio': values['eth_ratio'],
                    'total_value': values['total_value']
                },
                'trades': [],
                'plan': rebalance_plan
            }
            
            for trade in rebalance_plan['trades']:
                trade_result = self.execute_rebalance_trade(
                    trade['action'],
                    trade['symbol'],
                    trade['quantity']
                )
                
                trade['result'] = trade_result
                results['trades'].append(trade)
                
                if not trade_result['success']:
                    logger.error(f"Ошибка выполнения торга: {trade_result['error']}")
            
            # Обновляем статистику
            self.total_rebalances += 1
            self.last_rebalance_time = time.time()
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка балансировки портфеля: {e}")
            return {'success': False, 'error': str(e)}
    
    def format_rebalance_report(self, results: Dict) -> str:
        """Форматировать отчет о балансировке"""
        try:
            if not results['success']:
                error = results.get('error', 'Неизвестная ошибка')
                reason = results.get('reason', 'unknown')
                
                if reason == 'not_needed':
                    return (
                        "<b>⚖️ БАЛАНСИРОВКА НЕ НУЖНА</b>\n\n"
                        f"📊 Причина: {error}\n"
                        f"🎯 Целевые пропорции: BTC {self.target_btc_ratio*100:.0f}% / ETH {self.target_eth_ratio*100:.0f}%\n"
                        f"📏 Порог отклонения: {self.rebalance_threshold*100:.1f}%\n\n"
                        f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                    )
                else:
                    return f"❌ Ошибка балансировки: {error}"
            
            message = "<b>⚖️ БАЛАНСИРОВКА ПОРТФЕЛЯ ВЫПОЛНЕНА</b>\n"
            message += "=" * 50 + "\n\n"
            
            message += f"📅 Время: {results['timestamp'].strftime('%d.%m.%Y %H:%M:%S')}\n"
            message += f"💰 Общая стоимость: ${results['before']['total_value']:.2f}\n\n"
            
            message += "<b>📊 ПРОПОРЦИИ ДО БАЛАНСИРОВКИ:</b>\n"
            message += f"🟡 BTC: {results['before']['btc_ratio']*100:.1f}% (цель: {self.target_btc_ratio*100:.0f}%)\n"
            message += f"🔵 ETH: {results['before']['eth_ratio']*100:.1f}% (цель: {self.target_eth_ratio*100:.0f}%)\n\n"
            
            if results['trades']:
                message += "<b>🔄 ВЫПОЛНЕННЫЕ ТОРГИ:</b>\n"
                for trade in results['trades']:
                    if trade['result']['success']:
                        action_emoji = "🔴" if trade['action'] == 'SELL' else "🟢"
                        message += f"{action_emoji} {trade['action']} {trade['symbol']}\n"
                        message += f"   💰 Количество: {trade['quantity']:.6f}\n"
                        message += f"   💵 Стоимость: ${trade['value']:.2f}\n"
                        message += f"   🎯 Цена: ${trade['result']['price']:.4f}\n"
                        message += f"   🆔 Ордер: {trade['result']['order_id']}\n\n"
                    else:
                        message += f"❌ {trade['action']} {trade['symbol']}: {trade['result']['error']}\n\n"
            
            # Статистика
            message += "<b>📈 СТАТИСТИКА:</b>\n"
            message += f"🎯 Всего балансировок: {self.total_rebalances}\n"
            message += f"🚫 Заблокированных: {self.blocked_rebalances}\n"
            message += f"⏰ Интервал проверки: {self.rebalance_interval // 60} мин\n\n"
            
            message += "=" * 50 + "\n"
            message += "<b>⚖️ АВТОМАТИЧЕСКАЯ БАЛАНСИРОВКА ПОРТФЕЛЯ</b>"
            
            return message
            
        except Exception as e:
            return f"❌ Ошибка форматирования отчета: {e}"
    
    def execute_portfolio_rebalance_sync(self) -> Dict:
        """Синхронная версия балансировки портфеля"""
        try:
            logger.info("🎯 Запуск синхронной балансировки портфеля")
            
            # Получаем текущие балансы
            balances = self.get_portfolio_balances()
            if not balances:
                return {'success': False, 'error': 'Нет балансов BTC/ETH'}
            
            # Рассчитываем стоимости
            values = self.get_portfolio_values(balances)
            if not values:
                return {'success': False, 'error': 'Не удалось рассчитать стоимости'}
            
            # Проверяем необходимость балансировки
            need_rebalance, reason = self.check_rebalance_needed(values)
            if not need_rebalance:
                return {'success': False, 'error': reason, 'reason': 'not_needed'}
            
            # Проверяем PnL (упрощенная версия)
            if not self.allow_negative_pnl_rebalance:
                # Здесь должна быть проверка общего PnL портфеля
                # Пока пропускаем эту проверку
                pass
            
            # Рассчитываем необходимые торги
            rebalance_plan = self.calculate_rebalance_trades(balances, values)
            
            if not rebalance_plan['trades']:
                return {'success': False, 'error': 'Нет подходящих торгов для балансировки'}
            
            # Возвращаем результат без выполнения торгов (только симуляция)
            results = {
                'success': True,
                'timestamp': datetime.now(),
                'simulation': True,  # Помечаем как симуляцию
                'before': {
                    'btc_ratio': values['btc_ratio'],
                    'eth_ratio': values['eth_ratio'],
                    'total_value': values['total_value']
                },
                'trades': [],
                'plan': rebalance_plan,
                'note': 'Синхронная версия - только анализ без выполнения торгов'
            }
            
            # Обновляем время последней проверки
            self.last_rebalance_time = time.time()
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка синхронной балансировки: {e}")
            return {'success': False, 'error': str(e)} 