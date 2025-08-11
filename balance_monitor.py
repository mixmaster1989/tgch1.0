#!/usr/bin/env python3
"""
Монитор баланса для автоматической покупки BTC/ETH
Отслеживает освободившийся USDT и автоматически покупает BTC и ETH
"""

import asyncio
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from mex_api import MexAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from anti_hype_filter import AntiHypeFilter
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BalanceMonitor:
    """Монитор баланса для автоматических покупок"""
    
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.anti_hype_filter = AntiHypeFilter()
        
        # Настройки мониторинга
        self.min_balance_threshold = 10.0  # Минимальный баланс для покупки ($10)
        self.max_purchase_amount = 100.0   # Максимальная сумма одной покупки ($100)
        self.balance_check_interval = 60   # Проверка каждые 60 секунд
        
        # Стратегия распределения BTC/ETH
        self.btc_allocation = 0.6  # 60% на BTC
        self.eth_allocation = 0.4  # 40% на ETH
        
        # Защита от частых покупок
        self.last_purchase_time = None
        self.min_purchase_interval = 300  # Минимум 5 минут между покупками
        
        # История балансов для отслеживания изменений
        self.balance_history = []
        self.max_history_size = 10
        
        # Статистика
        self.total_purchases = 0
        self.total_spent = 0.0
        
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
    
    def get_usdc_balance(self) -> float:
        """Получить текущий баланс USDC"""
        try:
            account_info = self.mex_api.get_account_info()
            if 'balances' not in account_info:
                return 0.0
            
            for balance in account_info['balances']:
                if balance['asset'] == 'USDC':
                    return float(balance['free'])
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса USDC: {e}")
            return 0.0
    
    def get_usdt_balance(self) -> float:
        """Получить текущий баланс USDT"""
        try:
            account_info = self.mex_api.get_account_info()
            if 'balances' not in account_info:
                return 0.0
            
            for balance in account_info['balances']:
                if balance['asset'] == 'USDT':
                    return float(balance['free'])
            
            return 0.0
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса USDT: {e}")
            return 0.0
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Получить текущую цену символа"""
        try:
            ticker = self.mex_api.get_ticker_price(symbol)
            if 'price' in ticker:
                return float(ticker['price'])
            return None
        except Exception as e:
            logger.error(f"Ошибка получения цены {symbol}: {e}")
            return None
    
    def calculate_purchase_amounts(self, available_amount: float, currency: str = 'USDC') -> Dict[str, float]:
        """Рассчитать суммы для покупки BTC и ETH с умным распределением"""
        try:
            # Ограничиваем максимальную сумму покупки
            purchase_amount = min(available_amount, self.max_purchase_amount)
            
            # Определяем торговые пары на основе валюты
            btc_symbol = f'BTC{currency}'
            eth_symbol = f'ETH{currency}'
            
            # Получаем текущие цены
            btc_price = self.get_current_price(btc_symbol)
            eth_price = self.get_current_price(eth_symbol)
            
            if not btc_price or not eth_price:
                logger.error(f"Не удалось получить цены BTC/ETH в {currency} парах")
                return {}
            
            # Рассчитываем минимальные суммы для каждого актива
            min_btc_amount = 0.0001 * btc_price  # Минимум для BTC
            min_eth_amount = 0.001 * eth_price   # Минимум для ETH
            
            logger.info(f"💰 Доступно: ${purchase_amount:.2f}")
            logger.info(f"📊 Минимумы: BTC ${min_btc_amount:.2f}, ETH ${min_eth_amount:.2f}")
            
            result = {}
            
            # Если средств достаточно для обеих валют
            if purchase_amount >= (min_btc_amount + min_eth_amount):
                # Обычное распределение
                btc_amount = purchase_amount * self.btc_allocation
                eth_amount = purchase_amount * self.eth_allocation
                
                # Корректируем если одна из сумм меньше минимума
                if btc_amount < max(min_btc_amount, 5.0):
                    excess = max(min_btc_amount, 5.0) - btc_amount
                    btc_amount = max(min_btc_amount, 5.0)
                    eth_amount = max(eth_amount - excess, max(min_eth_amount, 5.0))
                
                if eth_amount < max(min_eth_amount, 5.0):
                    excess = max(min_eth_amount, 5.0) - eth_amount
                    eth_amount = max(min_eth_amount, 5.0)
                    btc_amount = max(btc_amount - excess, max(min_btc_amount, 5.0))
                
            # Если средств хватает только на один актив
            elif purchase_amount >= max(min_btc_amount, 5.0):
                # Покупаем только BTC
                btc_amount = purchase_amount
                eth_amount = 0
                logger.info("📈 Недостаточно средств для ETH, покупаем только BTC")
                
            elif purchase_amount >= max(min_eth_amount, 5.0):
                # Покупаем только ETH
                btc_amount = 0
                eth_amount = purchase_amount
                logger.info("📈 Недостаточно средств для BTC, покупаем только ETH")
                
            else:
                logger.warning(f"⚠️ Недостаточно средств для покупки: ${purchase_amount:.2f}")
                return {}
            
            # Обрабатываем BTC с анти-хайп фильтром
            if btc_amount >= max(min_btc_amount, 5.0):
                # Проверяем анти-хайп фильтр для BTC
                btc_filter = self.anti_hype_filter.check_buy_permission(btc_symbol)
                
                if not btc_filter['allowed']:
                    logger.warning(f"🚫 BTC покупка заблокирована: {btc_filter['reason']}")
                else:
                    # Применяем множитель фильтра
                    btc_amount *= btc_filter['multiplier']
                    
                    btc_quantity = btc_amount / btc_price
                    btc_quantity = round(btc_quantity, 6)  # Округляем до 6 знаков
                    actual_btc_amount = btc_quantity * btc_price
                    
                    result[btc_symbol] = {
                        'amount': actual_btc_amount,
                        'quantity': btc_quantity,
                        'price': btc_price,
                        'currency': currency,
                        'filter_reason': btc_filter['reason'],
                        'filter_multiplier': btc_filter['multiplier']
                    }
                    
                    multiplier_text = f" (×{btc_filter['multiplier']})" if btc_filter['multiplier'] != 1.0 else ""
                    logger.info(f"✅ BTC ордер{multiplier_text}: {btc_quantity:.6f} BTC на ${actual_btc_amount:.2f} {currency} [{btc_filter['reason']}]")
            
            # Обрабатываем ETH с анти-хайп фильтром
            if eth_amount >= max(min_eth_amount, 5.0):
                # Проверяем анти-хайп фильтр для ETH
                eth_filter = self.anti_hype_filter.check_buy_permission(eth_symbol)
                
                if not eth_filter['allowed']:
                    logger.warning(f"🚫 ETH покупка заблокирована: {eth_filter['reason']}")
                else:
                    # Применяем множитель фильтра
                    eth_amount *= eth_filter['multiplier']
                    
                    eth_quantity = eth_amount / eth_price
                    eth_quantity = round(eth_quantity, 6)  # Округляем до 6 знаков
                    actual_eth_amount = eth_quantity * eth_price
                    
                    result[eth_symbol] = {
                        'amount': actual_eth_amount,
                        'quantity': eth_quantity,
                        'price': eth_price,
                        'currency': currency,
                        'filter_reason': eth_filter['reason'],
                        'filter_multiplier': eth_filter['multiplier']
                    }
                    
                    multiplier_text = f" (×{eth_filter['multiplier']})" if eth_filter['multiplier'] != 1.0 else ""
                    logger.info(f"✅ ETH ордер{multiplier_text}: {eth_quantity:.6f} ETH на ${actual_eth_amount:.2f} {currency} [{eth_filter['reason']}]")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка расчета сумм покупки: {e}")
            return {}
    
    def can_make_purchase(self) -> bool:
        """Проверить, можно ли совершить покупку"""
        current_time = time.time()
        
        # Проверяем интервал между покупками
        if (self.last_purchase_time and 
            current_time - self.last_purchase_time < self.min_purchase_interval):
            return False
        
        return True
    
    def get_orderbook_data(self, symbol: str) -> Optional[Dict]:
        """Получить данные стакана заявок"""
        try:
            orderbook = self.mex_api.get_depth(symbol, limit=20)
            
            if 'bids' in orderbook and 'asks' in orderbook:
                bids = orderbook['bids'][:10]  # Топ-10 покупок
                asks = orderbook['asks'][:10]  # Топ-10 продаж
                
                # Рассчитываем среднюю цену лучших уровней
                best_bid = float(bids[0][0]) if bids else 0
                best_ask = float(asks[0][0]) if asks else 0
                
                # Рассчитываем спред
                spread = best_ask - best_bid
                spread_percent = (spread / best_bid) * 100 if best_bid > 0 else 0
                
                # Анализируем объемы
                bid_volume = sum(float(bid[1]) for bid in bids)
                ask_volume = sum(float(ask[1]) for ask in asks)
                
                return {
                    'bids': bids,
                    'asks': asks,
                    'best_bid': best_bid,
                    'best_ask': best_ask,
                    'spread': spread,
                    'spread_percent': spread_percent,
                    'bid_volume': bid_volume,
                    'ask_volume': ask_volume,
                    'volume_ratio': bid_volume / ask_volume if ask_volume > 0 else 1.0
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения стакана {symbol}: {e}")
            return None
    
    def calculate_limit_price(self, symbol: str, side: str = 'BUY') -> Optional[float]:
        """Рассчитать оптимальную цену для лимитного ордера"""
        try:
            orderbook = self.get_orderbook_data(symbol)
            
            if not orderbook:
                return None
            
            best_bid = orderbook['best_bid']
            best_ask = orderbook['best_ask']
            spread_percent = orderbook['spread_percent']
            
            if side == 'BUY':
                # Для покупки - ставим чуть ниже лучшей цены продажи
                if spread_percent < 0.1:  # Спред меньше 0.1%
                    # Ставим по лучшей цене продажи (будем мейкером)
                    return best_ask
                else:
                    # Спред большой - ставим посередине
                    return best_ask * 0.9995  # На 0.05% ниже
            else:
                # Для продажи - ставим чуть выше лучшей цены покупки
                if spread_percent < 0.1:
                    return best_bid
                else:
                    return best_bid * 1.0005  # На 0.05% выше
            
        except Exception as e:
            logger.error(f"Ошибка расчета лимитной цены {symbol}: {e}")
            return None
    
    def place_limit_order(self, symbol: str, quantity: float) -> Dict:
        """Разместить лимитный ордер с анализом стакана"""
        try:
            logger.info(f"Размещение лимитного ордера: {symbol} {quantity}")
            
            # Получаем оптимальную цену
            limit_price = self.calculate_limit_price(symbol, 'BUY')
            
            if not limit_price:
                logger.error(f"Не удалось рассчитать цену для {symbol}")
                return {'success': False, 'error': 'Не удалось рассчитать цену'}
            
            # Получаем данные стакана для логирования
            orderbook = self.get_orderbook_data(symbol)
            
            logger.info(f"Стакан {symbol}:")
            logger.info(f"  Лучшая покупка: ${orderbook['best_bid']:.4f}")
            logger.info(f"  Лучшая продажа: ${orderbook['best_ask']:.4f}")
            logger.info(f"  Спред: {orderbook['spread_percent']:.4f}%")
            logger.info(f"  Наша цена: ${limit_price:.4f}")
            
            # Определяем, будем ли мейкером
            is_maker = limit_price < orderbook['best_ask']
            maker_status = "МЕЙКЕР" if is_maker else "ТЕЙКЕР"
            
            logger.info(f"Статус ордера: {maker_status}")
            
            # Создаем лимитный ордер
            order = self.mex_api.place_order(
                symbol=symbol,
                side='BUY',
                quantity=quantity,
                price=limit_price
            )
            
            if order and 'orderId' in order:
                logger.info(f"✅ Ордер размещен: {order}")
                return {
                    'success': True,
                    'order_id': order['orderId'],
                    'symbol': symbol,
                    'quantity': quantity,
                    'order': order
                }
            else:
                logger.error(f"❌ Ошибка размещения ордера: {order}")
                return {
                    'success': False,
                    'error': f"API ошибка: {order}"
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка размещения ордера {symbol}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def execute_auto_purchase(self, available_amount: float, currency: str = 'USDC') -> Dict:
        """Выполнить автоматическую покупку BTC/ETH"""
        try:
            logger.info(f"🚀 Автоматическая покупка на ${available_amount:.2f} {currency}")
            
            # Рассчитываем суммы покупки
            purchase_plan = self.calculate_purchase_amounts(available_amount, currency)
            
            if not purchase_plan:
                logger.warning(f"⚠️ Нет подходящих ордеров для суммы ${available_amount:.2f} {currency}")
                logger.warning("💡 Возможные причины:")
                logger.warning("   - Сумма слишком мала для минимальных лотов")
                logger.warning("   - BTC требует >= $11.70 (0.0001 BTC)")
                logger.warning("   - ETH требует >= $4.17 (0.001 ETH)")
                return {
                    'success': False, 
                    'error': f'Сумма ${available_amount:.2f} {currency} слишком мала. Минимум: BTC ~$11.70, ETH ~$4.17',
                    'reason': 'insufficient_amount'
                }
            
            results = {
                'success': True,
                'timestamp': datetime.now(),
                'available_usdc': available_amount,  # Сохраняем ключ для совместимости
                'currency': currency,
                'purchases': [],
                'total_spent': 0.0
            }
            
            # Выполняем покупки
            for symbol, purchase_data in purchase_plan.items():
                if purchase_data['amount'] < 5:  # Минимум $5 на покупку
                    continue
                
                logger.info(f"Покупка {symbol}: ${purchase_data['amount']:.2f} {purchase_data['currency']}")
                
                # Размещаем лимитный ордер
                order_result = self.place_limit_order(
                    symbol=symbol,
                    quantity=purchase_data['quantity']
                )
                
                if order_result['success']:
                    # Получаем данные стакана для отчета
                    orderbook = self.get_orderbook_data(symbol)
                    limit_price = self.calculate_limit_price(symbol, 'BUY')
                    is_maker = limit_price < orderbook['best_ask'] if orderbook else False
                    
                    results['purchases'].append({
                        'symbol': symbol,
                        'quantity': purchase_data['quantity'],
                        'usdc_amount': purchase_data['amount'],  # Сохраняем ключ для совместимости
                        'amount': purchase_data['amount'],
                        'currency': purchase_data['currency'],
                        'price': purchase_data['price'],
                        'limit_price': limit_price,
                        'order_id': order_result['order_id'],
                        'is_maker': is_maker,
                        'orderbook': orderbook,
                        'filter_reason': purchase_data.get('filter_reason', 'normal'),
                        'filter_multiplier': purchase_data.get('filter_multiplier', 1.0)
                    })
                    results['total_spent'] += purchase_data['amount']
                    
                    # Обновляем статистику
                    self.total_purchases += 1
                    self.total_spent += purchase_data['amount']
                else:
                    logger.error(f"Ошибка покупки {symbol}: {order_result['error']}")
                    results['purchases'].append({
                        'symbol': symbol,
                        'error': order_result['error']
                    })
                
                # Пауза между ордерами
                await asyncio.sleep(1)
            
            # Обновляем время последней покупки
            self.last_purchase_time = time.time()
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Ошибка автоматической покупки: {e}")
            return {'success': False, 'error': str(e)}
    
    def format_purchase_report(self, results: Dict) -> str:
        """Форматировать отчет о покупке"""
        try:
            if not results['success']:
                error_msg = results.get('error', 'Неизвестная ошибка')
                reason = results.get('reason', 'unknown')
                
                if reason == 'insufficient_amount':
                    return (
                        "<b>⚠️ СУММА СЛИШКОМ МАЛА ДЛЯ ПОКУПКИ</b>\n\n"
                        f"💰 Доступно: {error_msg.split('$')[1].split(' ')[0]}$\n\n"
                        "<b>📏 МИНИМАЛЬНЫЕ ТРЕБОВАНИЯ:</b>\n"
                        "🟡 BTC (BTCUSDC): ~$11.70 (0.0001 BTC)\n"
                        "🔵 ETH (ETHUSDC): ~$4.17 (0.001 ETH)\n\n"
                        "<b>💡 РЕКОМЕНДАЦИИ:</b>\n"
                        "• Дождитесь накопления большей суммы\n"
                        "• Или измените настройки минимальных лотов\n\n"
                        f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                    )
                else:
                    return f"❌ Ошибка покупки: {error_msg}"
            
            message = "<b>🛒 АВТОМАТИЧЕСКАЯ ПОКУПКА ВЫПОЛНЕНА</b>\n"
            message += "=" * 50 + "\n\n"
            
            message += f"📅 Время: {results['timestamp'].strftime('%d.%m.%Y %H:%M:%S')}\n"
            message += f"💰 Доступно USDC: ${results['available_usdc']:.2f}\n"
            message += f"💸 Потрачено: ${results['total_spent']:.2f}\n\n"
            
            if results['purchases']:
                message += "<b>📋 КУПЛЕННЫЕ АКТИВЫ:</b>\n"
                for purchase in results['purchases']:
                    if 'error' in purchase:
                        message += f"❌ {purchase['symbol']}: {purchase['error']}\n"
                    else:
                        maker_emoji = "🟢" if purchase.get('is_maker', False) else "🟡"
                        maker_status = "МЕЙКЕР" if purchase.get('is_maker', False) else "ТЕЙКЕР"
                        
                        message += f"✅ {purchase['symbol']}:\n"
                        message += f"   💰 Количество: {purchase['quantity']:.6f}\n"
                        message += f"   💵 Сумма: ${purchase['usdc_amount']:.2f}\n"
                        message += f"   📈 Рыночная цена: ${purchase['price']:.4f}\n"
                        message += f"   🎯 Лимитная цена: ${purchase.get('limit_price', 0):.4f}\n"
                        message += f"   {maker_emoji} Статус: {maker_status}\n"
                        message += f"   🆔 Ордер: {purchase['order_id']}\n"
                        
                        # Добавляем информацию об анти-хайп фильтре
                        filter_reason = purchase.get('filter_reason', 'normal')
                        filter_multiplier = purchase.get('filter_multiplier', 1.0)
                        if filter_reason != 'normal':
                            if filter_multiplier == 2.0:
                                message += f"   🚀 DCA усиление: {filter_reason} → ×{filter_multiplier}\n"
                            elif filter_multiplier < 1.0:
                                message += f"   🛡️ Анти-хайп: {filter_reason} → ×{filter_multiplier}\n"
                            else:
                                message += f"   📊 Фильтр: {filter_reason}\n"
                        
                        # Показываем данные стакана
                        if purchase.get('orderbook'):
                            ob = purchase['orderbook']
                            message += f"   📊 Стакан: ${ob['best_bid']:.4f} / ${ob['best_ask']:.4f}\n"
                            message += f"   📏 Спред: {ob['spread_percent']:.4f}%\n"
                        
                        message += "\n"
            else:
                message += "❌ Покупки не выполнены\n\n"
            
            # Получаем общую стоимость портфеля
            try:
                from account_summary import get_account_summary
                account_info = self.mex_api.get_account_info()
                total_portfolio = 0.0
                if account_info and 'balances' in account_info:
                    for balance in account_info['balances']:
                        asset = balance['asset']
                        total = float(balance.get('free', 0)) + float(balance.get('locked', 0))
                        if total > 0:
                            if asset in ['USDT', 'USDC']:
                                total_portfolio += total
                            else:
                                try:
                                    ticker = self.mex_api.get_ticker_price(f"{asset}USDT")
                                    if ticker and 'price' in ticker:
                                        total_portfolio += total * float(ticker['price'])
                                except:
                                    pass
            except:
                total_portfolio = 0.0
            
            # Статистика
            message += "<b>📊 СТАТИСТИКА:</b>\n"
            message += f"💰 Общий портфель: ${total_portfolio:.2f}\n"
            message += f"🎯 Всего покупок: {self.total_purchases}\n"
            message += f"💵 Потрачено сегодня: ${self.total_spent:.2f}\n"
            message += f"⏰ Следующая покупка через: {self.min_purchase_interval // 60} мин\n\n"
            
            message += "=" * 50 + "\n"
            message += "<b>🤖 MEXCAITRADE - АВТОМАТИЧЕСКАЯ ТОРГОВЛЯ</b>"
            
            return message
            
        except Exception as e:
            return f"❌ Ошибка форматирования отчета: {e}"
    
    async def check_balance_and_purchase(self):
        """Проверить баланс и выполнить покупку при необходимости"""
        try:
            # Получаем балансы USDT и USDC
            usdt_balance = self.get_usdt_balance()
            usdc_balance = self.get_usdc_balance()
            
            logger.info(f"Текущий баланс USDT: ${usdt_balance:.2f}")
            logger.info(f"Текущий баланс USDC: ${usdc_balance:.2f}")
            
            # ПОКУПАЕМ ТОЛЬКО USDC ПАРЫ НА РЕАЛЬНЫЕ USDC! 
            # USDT не может напрямую тратиться на USDC пары
            available_for_purchase = usdc_balance  # Только реальные USDC!
            trading_currency = 'USDC'
            
            logger.info(f"💱 Доступно для покупки USDC пар: ${usdc_balance:.2f} USDC")
            if usdt_balance >= self.min_balance_threshold:
                logger.info(f"⚠️ USDT ${usdt_balance:.2f} недоступен для USDC пар (нужна конвертация)")
            
            # Добавляем в историю
            self.balance_history.append({
                'balance': available_for_purchase,
                'timestamp': datetime.now()
            })
            
            # Ограничиваем размер истории
            if len(self.balance_history) > self.max_history_size:
                self.balance_history = self.balance_history[-self.max_history_size:]
            
            # Проверяем условия для покупки
            if (available_for_purchase >= self.min_balance_threshold and 
                self.can_make_purchase()):
                
                logger.info(f"🎯 Условия для покупки выполнены! Доступно: ${available_for_purchase:.2f}")
                
                # Выполняем покупку (ВСЕГДА USDC пары)
                results = await self.execute_auto_purchase(available_for_purchase, 'USDC')
                
                # Отправляем отчет в Telegram
                report = self.format_purchase_report(results)
                self.send_telegram_message(report)
                
                return results
            else:
                if available_for_purchase < self.min_balance_threshold:
                    logger.info(f"Баланс слишком мал: ${available_for_purchase:.2f} < ${self.min_balance_threshold}")
                elif not self.can_make_purchase():
                    remaining_time = self.min_purchase_interval - (time.time() - self.last_purchase_time)
                    logger.info(f"Слишком рано для покупки. Осталось: {remaining_time:.0f} сек")
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки баланса: {e}")
            return None
    
    async def start_monitoring(self):
        """Запустить мониторинг баланса"""
        logger.info("🚀 Запуск мониторинга баланса для автоматических покупок")
        logger.info(f"📊 Настройки:")
        logger.info(f"   Минимальный баланс: ${self.min_balance_threshold}")
        logger.info(f"   Максимальная покупка: ${self.max_purchase_amount}")
        logger.info(f"   Интервал проверки: {self.balance_check_interval} сек")
        logger.info(f"   Распределение: BTC {self.btc_allocation*100}% / ETH {self.eth_allocation*100}%")
        
        # Отправляем уведомление о запуске
        startup_message = (
            "<b>🤖 МОНИТОР БАЛАНСА ЗАПУЩЕН</b>\n\n"
            f"📊 Настройки:\n"
            f"💰 Минимальный баланс: ${self.min_balance_threshold}\n"
            f"💸 Максимальная покупка: ${self.max_purchase_amount}\n"
            f"⏰ Проверка каждые {self.balance_check_interval} сек\n"
            f"📈 BTC: {self.btc_allocation*100}% | ETH: {self.eth_allocation*100}%\n\n"
            "🔄 Мониторинг активен..."
        )
        self.send_telegram_message(startup_message)
        
        while True:
            try:
                await self.check_balance_and_purchase()
                await asyncio.sleep(self.balance_check_interval)
                
            except KeyboardInterrupt:
                logger.info("🛑 Мониторинг остановлен пользователем")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в цикле мониторинга: {e}")
                await asyncio.sleep(30)  # Пауза при ошибке

# Функция для тестирования
async def test_balance_monitor():
    """Тест монитора баланса"""
    monitor = BalanceMonitor()
    
    # Тест получения баланса
    balance = monitor.get_usdt_balance()
    print(f"Текущий баланс: ${balance:.2f}")
    
    # Тест расчета покупки
    if balance >= monitor.min_balance_threshold:
        purchase_plan = monitor.calculate_purchase_amounts(balance)
        print(f"План покупки: {purchase_plan}")
    else:
        print("Баланс слишком мал для покупки")

if __name__ == "__main__":
    # Запуск мониторинга
    monitor = BalanceMonitor()
    asyncio.run(monitor.start_monitoring()) 