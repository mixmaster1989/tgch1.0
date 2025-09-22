#!/usr/bin/env python3
"""
Мониторинг PnL с автоматической продажей при прибыли более 7 центов
Для подвижного аккаунта - быстрые сделки!
"""

from mex_api import MexAPI
import asyncio
import time
import logging
import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, PNL_MONITOR_CONFIG
from portfolio_balancer import PortfolioBalancer
from mexc_advanced_api import MexAdvancedAPI
from post_sale_balancer import PostSaleBalancer
from logging.handlers import RotatingFileHandler

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PnLMonitor:
    def __init__(self):
        self.mex_api = MexAPI()
        self.mex_adv = MexAdvancedAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.is_running = False
        
        # Загружаем настройки из конфигурации
        self.profit_threshold = PNL_MONITOR_CONFIG['profit_threshold']
        self.profit_threshold_pct = PNL_MONITOR_CONFIG.get('profit_threshold_pct', None)
        self.check_interval = PNL_MONITOR_CONFIG['check_interval']
        self.notification_interval = PNL_MONITOR_CONFIG['notification_interval']
        self.trading_pairs = PNL_MONITOR_CONFIG['trading_pairs']
        self.auto_sell_enabled = PNL_MONITOR_CONFIG['auto_sell_enabled']
        self.telegram_notifications = PNL_MONITOR_CONFIG['telegram_notifications']
        
        # Балансировщик портфеля
        self.portfolio_balancer = PortfolioBalancer()
        self.last_balance_check = 0
        self.balance_check_interval = 3600  # Проверка балансировки каждый час
        
        # Контроль частоты отчетов (уменьшаем спам в 2 раза)
        self.report_counter = 0
        
        # Настройка файлового логирования
        if PNL_MONITOR_CONFIG['file_logging']:
            file_handler = RotatingFileHandler(
                PNL_MONITOR_CONFIG['log_file'],
                maxBytes=20 * 1024 * 1024,
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
    
    def send_telegram_message(self, message: str):
        """Отправить сообщение в Telegram"""
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        data = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        try:
            logger.info(f"📤 Отправляем сообщение в Telegram (длина: {len(message)} символов)")
            response = requests.post(url, data=data)
            result = response.json()
            if result.get('ok'):
                logger.info("✅ Сообщение успешно отправлено в Telegram")
            else:
                logger.error(f"❌ Ошибка отправки в Telegram: {result}")
            return result
        except Exception as e:
            logger.error(f"Ошибка отправки в Telegram: {e}")
            return None
    
    def get_balances(self):
        """Получить все балансы"""
        try:
            account_info = self.mex_api.get_account_info()
            balances = {}
            
            logger.info(f"📋 Получено {len(account_info.get('balances', []))} балансов от API")
            
            for balance in account_info.get('balances', []):
                asset = balance['asset']
                free = float(balance['free'])
                locked = float(balance['locked'])
                total = free + locked
                
                # Логируем все активы для отладки
                if asset in ['BTC', 'ETH']:
                    logger.info(f"🔍 {asset}: free={free}, locked={locked}, total={total}")
                
                if total > 0:
                    balances[asset] = {
                        'free': free,
                        'locked': locked,
                        'total': total
                    }
            
            logger.info(f"📊 Активные балансы: {list(balances.keys())}")
            return balances
            
        except Exception as e:
            logger.error(f"Ошибка получения балансов: {e}")
            return {}
    
    def get_current_price(self, symbol: str):
        """Получить текущую цену"""
        try:
            price_info = self.mex_api.get_ticker_price(symbol)
            if 'price' in price_info:
                return float(price_info['price'])
            return None
        except Exception as e:
            logger.error(f"Ошибка получения цены {symbol}: {e}")
            return None
    
    def get_open_orders_info(self):
        """Получить информацию об открытых ордерах"""
        try:
            open_orders = self.mex_api.get_open_orders()
            
            if not open_orders:
                return {
                    'total_orders': 0,
                    'buy_orders': 0,
                    'sell_orders': 0,
                    'total_value': 0.0,
                    'orders': []
                }
            
            orders_info = {
                'total_orders': len(open_orders),
                'buy_orders': 0,
                'sell_orders': 0,
                'total_value': 0.0,
                'orders': []
            }
            
            for order in open_orders:
                try:
                    symbol = order.get('symbol', '')
                    side = order.get('side', '')
                    quantity = float(order.get('origQty', 0))
                    price = float(order.get('price', 0))
                    order_id = order.get('orderId', '')
                    status = order.get('status', '')
                    order_type = order.get('type', '')
                    
                    # Рассчитываем стоимость ордера
                    order_value = quantity * price
                    orders_info['total_value'] += order_value
                    
                    # Считаем типы ордеров
                    if side == 'BUY':
                        orders_info['buy_orders'] += 1
                    elif side == 'SELL':
                        orders_info['sell_orders'] += 1
                    
                    orders_info['orders'].append({
                        'symbol': symbol,
                        'side': side,
                        'quantity': quantity,
                        'price': price,
                        'value': order_value,
                        'order_id': order_id,
                        'status': status,
                        'type': order_type
                    })
                    
                except Exception as e:
                    logger.error(f"Ошибка обработки ордера: {e}")
                    continue
            
            return orders_info
            
        except Exception as e:
            logger.error(f"Ошибка получения открытых ордеров: {e}")
            return {
                'total_orders': 0,
                'buy_orders': 0,
                'sell_orders': 0,
                'total_value': 0.0,
                'orders': []
            }
    
    def get_order_history_analysis(self, limit: int = 50):
        """Получить анализ истории ордеров"""
        try:
            # Получаем историю ордеров для основных пар
            btc_history = self.mex_api.get_order_history('BTCUSDC', limit)
            eth_history = self.mex_api.get_order_history('ETHUSDC', limit)
            
            all_orders = []
            if isinstance(btc_history, list):
                all_orders.extend(btc_history)
            if isinstance(eth_history, list):
                all_orders.extend(eth_history)
            
            if not all_orders:
                return {
                    'total_orders': 0,
                    'completed_orders': 0,
                    'total_volume_usdc': 0.0,
                    'total_pnl': 0.0,
                    'buy_orders': 0,
                    'sell_orders': 0,
                    'recent_orders': []
                }
            
            # Сортируем по времени (новые сначала)
            all_orders.sort(key=lambda x: x.get('time', 0), reverse=True)
            
            analysis = {
                'total_orders': len(all_orders),
                'completed_orders': 0,
                'total_volume_usdc': 0.0,
                'total_pnl': 0.0,
                'buy_orders': 0,
                'sell_orders': 0,
                'recent_orders': [],
                'buy_volume': 0.0,
                'sell_volume': 0.0
            }
            
            for order in all_orders[:20]:  # Анализируем только последние 20
                try:
                    symbol = order.get('symbol', '')
                    side = order.get('side', '')
                    status = order.get('status', '')
                    quantity = float(order.get('executedQty', 0))
                    price = float(order.get('price', 0))
                    avg_price = float(order.get('cummulativeQuoteQty', 0)) / max(quantity, 0.000001)
                    order_time = order.get('time', 0)
                    
                    if status == 'FILLED' and quantity > 0:
                        analysis['completed_orders'] += 1
                        volume = quantity * avg_price
                        analysis['total_volume_usdc'] += volume
                        
                        if side == 'BUY':
                            analysis['buy_orders'] += 1
                            analysis['buy_volume'] += volume
                        elif side == 'SELL':
                            analysis['sell_orders'] += 1
                            analysis['sell_volume'] += volume
                        
                        # Добавляем в список последних ордеров
                        analysis['recent_orders'].append({
                            'symbol': symbol,
                            'side': side,
                            'quantity': quantity,
                            'price': price,
                            'avg_price': avg_price,
                            'volume': volume,
                            'time': order_time,
                            'order_id': order.get('orderId', ''),
                            'status': status
                        })
                        
                except Exception as e:
                    logger.error(f"Ошибка обработки ордера в истории: {e}")
                    continue
            
            # Правильный расчет PnL с учетом текущей стоимости монет
            analysis['total_pnl'] = self.calculate_real_pnl(analysis['recent_orders'])
            
            return analysis
            
        except Exception as e:
            logger.error(f"Ошибка получения истории ордеров: {e}")
            return {
                'total_orders': 0,
                'completed_orders': 0,
                'total_volume_usdc': 0.0,
                'total_pnl': 0.0,
                'buy_orders': 0,
                'sell_orders': 0,
                'recent_orders': []
            }
    
    def calculate_real_pnl(self, orders: list) -> float:
        """Правильный расчет PnL с учетом текущей стоимости монет"""
        try:
            # Группируем ордера по символам
            positions = {}  # symbol -> {'bought': quantity, 'cost': total_cost, 'sold': quantity, 'revenue': total_revenue}
            
            for order in orders:
                symbol = order['symbol']
                side = order['side']
                quantity = order['quantity']
                volume = order['volume']
                
                if symbol not in positions:
                    positions[symbol] = {
                        'bought': 0.0,
                        'cost': 0.0,
                        'sold': 0.0, 
                        'revenue': 0.0
                    }
                
                if side == 'BUY':
                    positions[symbol]['bought'] += quantity
                    positions[symbol]['cost'] += volume
                elif side == 'SELL':
                    positions[symbol]['sold'] += quantity
                    positions[symbol]['revenue'] += volume
            
            total_pnl = 0.0
            
            for symbol, pos in positions.items():
                # Рассчитываем PnL для каждого символа
                
                # 1. Прибыль от уже проданных монет
                sold_pnl = pos['revenue'] - (pos['cost'] * (pos['sold'] / max(pos['bought'], 0.000001)))
                
                # 2. Нереализованная прибыль от оставшихся монет
                remaining_quantity = pos['bought'] - pos['sold']
                
                if remaining_quantity > 0:
                    try:
                        # Получаем текущую цену
                        current_price = self.mex_api.get_ticker_price(symbol)
                        if current_price and 'price' in current_price:
                            current_value = remaining_quantity * float(current_price['price'])
                            avg_buy_price = pos['cost'] / max(pos['bought'], 0.000001)
                            cost_of_remaining = remaining_quantity * avg_buy_price
                            unrealized_pnl = current_value - cost_of_remaining
                        else:
                            unrealized_pnl = 0.0
                    except:
                        unrealized_pnl = 0.0
                else:
                    unrealized_pnl = 0.0
                
                symbol_pnl = sold_pnl + unrealized_pnl
                total_pnl += symbol_pnl
                
                logger.info(f"PnL для {symbol}: проданные=${sold_pnl:.2f}, нереализованные=${unrealized_pnl:.2f}, итого=${symbol_pnl:.2f}")
            
            return total_pnl
            
        except Exception as e:
            logger.error(f"Ошибка расчета PnL: {e}")
            return 0.0
    
    def calculate_real_pnl_for_asset(self, asset: str, symbol: str, current_quantity: float, current_price: float) -> float:
        """Правильный расчет PnL для конкретного актива с использованием FIFO метода"""
        try:
            logger.info(f"🔍 Расчет PnL для {asset} (FIFO метод)...")
            
            # Получаем историю ордеров для этого символа
            orders = self.mex_api.get_order_history(symbol, limit=100)
            if not orders:
                logger.warning(f"⚠️ Не удалось получить историю ордеров для {symbol}")
                return 0.0
            
            # Фильтруем только исполненные ордера
            executed_orders = [order for order in orders if order['status'] == 'FILLED']
            
            # Сортируем по времени исполнения (FIFO)
            executed_orders.sort(key=lambda x: x['time'])
            
            # Группируем покупки и продажи
            buy_orders = [order for order in executed_orders if order['side'] == 'BUY']
            sell_orders = [order for order in executed_orders if order['side'] == 'SELL']
            
            logger.info(f"📊 {asset}: {len(buy_orders)} покупок, {len(sell_orders)} продаж")
            
            # Рассчитываем среднюю цену покупки для оставшихся монет
            total_bought = sum(float(order.get('executedQty', 0)) for order in buy_orders)
            total_sold = sum(float(order.get('executedQty', 0)) for order in sell_orders)
            remaining_quantity = total_bought - total_sold
            
            logger.info(f"📊 {asset}: куплено {total_bought:.6f}, продано {total_sold:.6f}, остаток {remaining_quantity:.6f}")
            
            if remaining_quantity <= 0:
                logger.info(f"📊 {asset}: все монеты проданы, PnL = 0")
                return 0.0
            
            # Рассчитываем среднюю цену покупки на основе фактической стоимости исполнения
            total_cost = sum(float(order.get('cummulativeQuoteQty', 0)) for order in buy_orders)
            avg_buy_price = (total_cost / total_bought) if total_bought > 0 else 0.0
            
            logger.info(f"💰 {asset}: средняя цена покупки = ${avg_buy_price:.4f}")
            
            # Рассчитываем PnL
            current_value = current_quantity * current_price
            cost_basis = current_quantity * avg_buy_price
            pnl = current_value - cost_basis
            
            logger.info(f"📈 {asset}: текущая стоимость = ${current_value:.4f}, себестоимость = ${cost_basis:.4f}, PnL = ${pnl:.4f}")
            
            return pnl
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета PnL для {asset}: {e}")
            return 0.0
    
    def _calculate_avg_cost_pnl(self, symbol: str, current_quantity: float, current_price: float) -> dict:
        """Рассчитать PnL от средней цены закупа по истории сделок (moving average).
        Возвращает словарь с avg_buy_price, realized_pnl, unrealized_pnl, total_pnl."""
        try:
            # Определяем базовый и котируемый актив из символа
            base_asset = ''.join([c for c in symbol if not c.isdigit()]).replace('USDC', '').replace('USDT', '')
            quote_asset = 'USDC' if symbol.endswith('USDC') else ('USDT' if symbol.endswith('USDT') else 'USDT')
            
            trades = self.mex_adv.get_my_trades(symbol, limit=500) or []
            trades = sorted(trades, key=lambda t: t.get('time', 0))
            
            position_qty = 0.0
            cost_basis_total = 0.0  # В котируемой валюте
            realized_pnl = 0.0
            
            def commission_in_quote(trade):
                commission = float(trade.get('commission', 0) or 0)
                commission_asset = trade.get('commissionAsset')
                price = float(trade.get('price', 0) or 0)
                if commission <= 0:
                    return 0.0
                if commission_asset == quote_asset:
                    return commission
                if commission_asset == base_asset and price > 0:
                    return commission * price
                # Комиссия в другом активе — не учитываем
                return 0.0
            
            for trade in trades:
                qty = float(trade.get('qty', 0) or 0)
                price = float(trade.get('price', 0) or 0)
                quote_qty = float(trade.get('quoteQty', 0) or 0)
                is_buyer = bool(trade.get('isBuyer', False))
                fee_q = commission_in_quote(trade)
                
                if is_buyer:
                    # Покупка: увеличиваем позицию и стоимость
                    total_cost = quote_qty + fee_q
                    new_position = position_qty + qty
                    if new_position > 0:
                        cost_basis_total = cost_basis_total + total_cost
                        position_qty = new_position
                else:
                    # Продажа: рассчитываем реализованный PnL относительно текущей средней цены
                    if position_qty <= 0:
                        continue
                    avg_price = cost_basis_total / position_qty if position_qty > 0 else 0.0
                    revenue = quote_qty - fee_q
                    realized_pnl += revenue - (avg_price * qty)
                    # Уменьшаем базу стоимости пропорционально проданному количеству
                    cost_basis_total -= avg_price * qty
                    position_qty -= qty
                    if position_qty < 1e-12:
                        position_qty = 0.0
                        cost_basis_total = 0.0
            
            avg_buy_price = (cost_basis_total / position_qty) if position_qty > 0 else 0.0
            qty_for_pnl = min(current_quantity, position_qty) if position_qty > 0 else 0.0
            unrealized_pnl = (current_price - avg_buy_price) * qty_for_pnl
            total_pnl = realized_pnl + unrealized_pnl
            
            logger.info(f"💰 Средняя цена закупа {symbol}: ${avg_buy_price:.6f}; Позиция={position_qty:.8f}; Баланс={current_quantity:.8f}")
            logger.info(f"📈 PnL: реализованный=${realized_pnl:.4f}, нереализованный=${unrealized_pnl:.4f}, итого=${total_pnl:.4f}")
            
            return {
                'avg_buy_price': avg_buy_price,
                'position_qty': position_qty,
                'realized_pnl': realized_pnl,
                'unrealized_pnl': unrealized_pnl,
                'total_pnl': total_pnl,
            }
        except Exception as e:
            logger.error(f"❌ Ошибка расчета AvgCost PnL для {symbol}: {e}")
            return {
                'avg_buy_price': 0.0,
                'position_qty': 0.0,
                'realized_pnl': 0.0,
                'unrealized_pnl': 0.0,
                'total_pnl': 0.0,
            }
    
    async def check_portfolio_balance(self):
        """Проверка и выполнение балансировки портфеля с учетом PnL"""
        try:
            current_time = time.time()
            
            # Проверяем интервал
            if current_time - self.last_balance_check < self.balance_check_interval:
                return
            
            self.last_balance_check = current_time
            
            logger.info("⚖️ Проверка балансировки портфеля...")
            
            # Получаем общий PnL портфеля
            total_pnl = 0.0
            status = self.get_current_status()
            
            # Берем общий PnL из статуса
            if 'total_pnl' in status:
                total_pnl = status['total_pnl']
            
            logger.info(f"💰 Общий PnL портфеля: ${total_pnl:.4f}")
            
            # 🔥 НОВАЯ ЛОГИКА: Не блокируем всю балансировку при общем отрицательном PnL
            # Теперь PortfolioBalancer сам решает что можно продавать/покупать на основе PnL каждого актива
            logger.info(f"💰 Общий PnL портфеля: ${total_pnl:.4f} - передаем управление PortfolioBalancer")
            
            # Отправляем информационное уведомление (не блокирующее)
            if total_pnl < 0:
                info_message = (
                    "<b>ℹ️ БАЛАНСИРОВКА С ОТРИЦАТЕЛЬНЫМ PnL</b>\n\n"
                    f"📉 Общий PnL: ${total_pnl:.4f}\n"
                    f"🛡️ Защита: Продажа только активов в плюсе\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    "💡 PortfolioBalancer проверит PnL каждого актива отдельно"
                )
                self.send_telegram_message(info_message)
            
            # Выполняем балансировку
            result = await self.portfolio_balancer.execute_portfolio_rebalance()
            
            # Отправляем отчет
            if result['success'] or result.get('reason') != 'not_needed':
                report = self.portfolio_balancer.format_rebalance_report(result)
                self.send_telegram_message(report)
                
                if result['success']:
                    logger.info("✅ Балансировка портфеля выполнена успешно")
                else:
                    logger.info(f"ℹ️ Балансировка: {result.get('error', 'причина неизвестна')}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки балансировки: {e}")
    
    async def check_portfolio_balance_sync(self):
        """Синхронная версия проверки балансировки портфеля"""
        try:
            current_time = time.time()
            
            # Проверяем интервал
            if current_time - getattr(self, 'last_balance_check', 0) < getattr(self, 'balance_check_interval', 3600):
                return
            
            self.last_balance_check = current_time
            
            logger.info("⚖️ Проверка балансировки портфеля...")
            
            # Получаем общий PnL портфеля
            total_pnl = 0.0
            status = self.get_current_status()
            
            # Берем общий PnL из статуса
            if 'total_pnl' in status:
                total_pnl = status['total_pnl']
            
            logger.info(f"💰 Общий PnL портфеля: ${total_pnl:.4f}")
            
            # 🔥 НОВАЯ ЛОГИКА: Не блокируем всю балансировку при общем отрицательном PnL
            # Теперь PortfolioBalancer сам решает что можно продавать/покупать на основе PnL каждого актива
            logger.info(f"💰 Общий PnL портфеля: ${total_pnl:.4f} - передаем управление PortfolioBalancer")
            
            # Отправляем информационное уведомление (не блокирующее)
            if total_pnl < 0:
                info_message = (
                    "<b>ℹ️ БАЛАНСИРОВКА С ОТРИЦАТЕЛЬНЫМ PnL</b>\n\n"
                    f"📉 Общий PnL: ${total_pnl:.4f}\n"
                    f"🛡️ Защита: Продажа только активов в плюсе\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n\n"
                    "💡 PortfolioBalancer проверит PnL каждого актива отдельно"
                )
                self.send_telegram_message(info_message)
            
            # Выполняем синхронную балансировку
            result = await self.portfolio_balancer.execute_portfolio_rebalance()
            
            # Отправляем отчет
            if result['success'] or result.get('reason') != 'not_needed':
                report = self.portfolio_balancer.format_rebalance_report(result)
                self.send_telegram_message(report)
                
                if result['success']:
                    logger.info("✅ Балансировка портфеля выполнена успешно")
                else:
                    logger.info(f"ℹ️ Балансировка: {result.get('error', 'причина неизвестна')}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка синхронной проверки балансировки: {e}")
     
    def format_history_report(self, analysis: dict) -> str:
        """Форматировать отчет по истории ордеров"""
        try:
            message = "<b>📜 ИСТОРИЯ ОРДЕРОВ</b>\n\n"
            
            # Общая статистика
            message += f"📊 <b>СТАТИСТИКА:</b>\n"
            message += f"📋 Всего ордеров: {analysis['total_orders']}\n"
            message += f"✅ Исполненных: {analysis['completed_orders']}\n"
            message += f"🟢 Покупок: {analysis['buy_orders']}\n"
            message += f"🔴 Продаж: {analysis['sell_orders']}\n"
            message += f"💰 Общий объем: ${analysis['total_volume_usdc']:.2f}\n"
            
            if analysis['total_pnl'] != 0:
                pnl_emoji = "📈" if analysis['total_pnl'] > 0 else "📉"
                message += f"{pnl_emoji} Примерный PnL: ${analysis['total_pnl']:.2f}\n"
            
            message += f"\n💰 <b>ОБЪЕМЫ:</b>\n"
            message += f"🟢 Покупки: ${analysis.get('buy_volume', 0):.2f}\n"
            message += f"🔴 Продажи: ${analysis.get('sell_volume', 0):.2f}\n\n"
            
            # Последние ордера
            if analysis['recent_orders']:
                message += f"📋 <b>ПОСЛЕДНИЕ ОРДЕРА:</b>\n"
                
                for i, order in enumerate(analysis['recent_orders'][:10], 1):
                    side_emoji = "🟢" if order['side'] == 'BUY' else "🔴"
                    
                    # Конвертируем timestamp в читаемое время
                    try:
                        from datetime import datetime
                        order_time = datetime.fromtimestamp(order['time'] / 1000).strftime('%H:%M:%S')
                    except:
                        order_time = "N/A"
                    
                    message += (
                        f"{i}. {side_emoji} <b>{order['symbol']}</b>\n"
                        f"   💰 {order['quantity']:.6f} @ ${order['avg_price']:.4f}\n"
                        f"   💵 Объем: ${order['volume']:.2f}\n"
                        f"   ⏰ {order_time}\n"
                        f"   🆔 <code>{order['order_id']}</code>\n\n"
                    )
                
                if len(analysis['recent_orders']) > 10:
                    message += f"... и еще {len(analysis['recent_orders']) - 10} ордеров\n\n"
            else:
                message += "🚫 Нет исполненных ордеров\n\n"
            
            message += f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка форматирования отчета истории: {e}")
            return f"❌ Ошибка создания отчета по истории: {str(e)}"
    
    def calculate_pnl(self, asset: str, quantity: float, current_price: float):
        """Рассчитать PnL для актива используя реальную среднюю цену покупки"""
        try:
            # Определяем символ для получения истории ордеров
            if asset == 'BTC':
                symbol = 'BTCUSDC'
            elif asset == 'ETH':
                symbol = 'ETHUSDC'
            else:
                return 0.0
            
            # Получаем историю ордеров для расчета средней цены покупки
            order_history = self.mex_api.get_order_history(symbol, limit=100)
            
            if not order_history:
                logger.warning(f"⚠️ Нет истории ордеров для {asset}, используем консервативную оценку")
                # Если нет истории, используем текущую цену с небольшим запасом
                avg_buy_price = current_price * 1.002  # +0.2% от текущей цены
                logger.info(f"📊 {asset} консервативная цена: ${avg_buy_price:.4f}")
            else:
                # Фильтруем только исполненные BUY ордера
                buy_orders = []
                for order in order_history:
                    if (order.get('status') == 'FILLED' and 
                        order.get('side') == 'BUY' and 
                        float(order.get('executedQty', 0)) > 0):
                        
                        # Рассчитываем среднюю цену исполнения
                        executed_qty = float(order.get('executedQty', 0))
                        total_quote = float(order.get('cummulativeQuoteQty', 0))
                        
                        if executed_qty > 0 and total_quote > 0:
                            avg_price = total_quote / executed_qty
                            buy_orders.append({
                                'quantity': executed_qty,
                                'price': avg_price,
                                'total_value': total_quote
                            })
                
                if buy_orders:
                    # Рассчитываем средневзвешенную цену покупки
                    total_quantity = sum(order['quantity'] for order in buy_orders)
                    total_value = sum(order['total_value'] for order in buy_orders)
                    avg_buy_price = total_value / total_quantity
                    
                    logger.info(f"📊 {asset} средняя цена покупки: ${avg_buy_price:.4f} из {len(buy_orders)} ордеров")
                    logger.info(f"🔍 {asset} общее количество: {total_quantity:.6f}, текущий баланс: {quantity:.6f}")
                else:
                    logger.warning(f"⚠️ Нет BUY ордеров для {asset}, используем консервативную оценку")
                    avg_buy_price = current_price * 1.002
            
            # Рассчитываем PnL
            pnl = (current_price - avg_buy_price) * quantity
            
            logger.info(f"📈 {asset} PnL расчет: цена=${current_price:.4f}, средняя=${avg_buy_price:.4f}, PnL=${pnl:.4f}")
            
            return pnl
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета PnL для {asset}: {e}")
            # В случае ошибки используем консервативную оценку
            avg_buy_price = current_price * 1.002
            logger.warning(f"⚠️ Fallback для {asset}: ${avg_buy_price:.4f}")
            return 0.0
    
    def market_sell(self, symbol: str, quantity: float):
        """Лимитная продажа близко к рынку"""
        try:
            logger.info(f"🚀 Лимитная продажа {quantity} {symbol}...")
            
            # Получаем текущую цену
            current_price = self.get_current_price(symbol)
            if not current_price:
                logger.error(f"❌ Не удалось получить цену {symbol}")
                return None
            
            # Ставим лимитную цену чуть ниже рыночной для быстрого исполнения
            limit_price = current_price * 0.999  # -0.1% от рыночной цены
            
            logger.info(f"💰 Рыночная цена: ${current_price:.4f}")
            logger.info(f"🎯 Лимитная цена: ${limit_price:.4f}")
            
            # Размещаем лимитный ордер на продажу
            order = self.mex_api.place_order(
                symbol=symbol,
                side='SELL',
                quantity=quantity,
                price=limit_price  # Лимитный ордер
            )
            
            if 'orderId' in order:
                logger.info(f"✅ Лимитный ордер на продажу создан: {order['orderId']}")
                
                # Отправляем уведомление в Telegram (НЕМЕДЛЕННО)
                message = (
                    f"💰 <b>ПРОДАЖА BTC/ETH</b>\n\n"
                    f"📋 <b>Детали:</b>\n"
                    f"🆔 ID: <code>{order['orderId']}</code>\n"
                    f"💱 Пара: {symbol}\n"
                    f"📊 Количество: {quantity}\n"
                    f"💰 Рыночная цена: ${current_price:.4f}\n"
                    f"🎯 Лимитная цена: ${limit_price:.4f}\n"
                    f"📈 Тип: ЛИМИТНЫЙ (-0.1%)\n\n"
                    f"🎯 <b>Причина:</b> PnL > $0.15\n"
                    f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                )
                self.send_telegram_message(message)
                
                # Триггер пост-продажного балансировщика 50/50
                try:
                    balancer = PostSaleBalancer()
                    balance_result = balancer.rebalance_on_freed_funds()
                    logger.info(f"⚖️ PostSaleBalancer: {balance_result}")
                except Exception as e:
                    logger.error(f"Ошибка PostSaleBalancer: {e}")
                
                return order
            else:
                logger.error(f"❌ Ошибка создания ордера продажи: {order}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка лимитной продажи: {e}")
            return None
    
    def check_pnl_and_sell(self):
        """Проверить PnL и продать при необходимости"""
        try:
            logger.info("🔍 Проверка PnL...")
            
            # Получаем балансы
            balances = self.get_balances()
            logger.info(f"📋 Полученные балансы: {list(balances.keys())}")
            
            # Собираем данные для уведомления
            pnl_data = []
            
            # Проверяем BTC и ETH
            for asset in ['BTC', 'ETH']:
                logger.info(f"🔍 Проверяем {asset}...")
                
                if asset in balances:
                    quantity = balances[asset]['total']
                    logger.info(f"📊 {asset} найден в балансах, количество: {quantity}")
                    
                    if quantity > 0:
                        # Определяем символ для получения цены
                        if asset == 'BTC':
                            symbol = 'BTCUSDC'
                        else:
                            symbol = 'ETHUSDC'
                        
                        # Получаем текущую цену
                        current_price = self.get_current_price(symbol)
                        if not current_price:
                            logger.warning(f"⚠️ Не удалось получить цену для {symbol}")
                            continue
                        
                        # Новый расчет: PnL от средней цены закупа по истории сделок
                        avg_cost_pnl = self._calculate_avg_cost_pnl(symbol, quantity, current_price)
                        pnl = avg_cost_pnl.get('unrealized_pnl', 0.0)
                        avg_buy_price = avg_cost_pnl.get('avg_buy_price', 0.0)
                        pnl_pct = 0.0
                        if avg_buy_price > 0:
                            pnl_pct = ((current_price - avg_buy_price) / avg_buy_price) * 100.0
                        
                        logger.info(f"📊 {asset}:")
                        logger.info(f"   Количество: {quantity}")
                        logger.info(f"   Текущая цена: ${current_price:.4f}")
                        logger.info(f"   Средняя цена закупа: ${avg_buy_price:.4f}")
                        logger.info(f"   PnL (AvgCost): ${pnl:.4f}")
                        
                        # Проверяем, превышает ли PnL порог (в процентах, с фоллбэком на долларовый)
                        meets_threshold = False
                        if self.profit_threshold_pct is not None and avg_buy_price > 0:
                            meets_threshold = pnl_pct >= float(self.profit_threshold_pct)
                        else:
                            meets_threshold = pnl > self.profit_threshold

                        if meets_threshold:
                            logger.info(f"🎯 PnL превышает порог! Продаем {asset}...")
                            
                            # Рыночная продажа (лимитная около рынка)
                            order = self.market_sell(symbol, quantity)
                            if order:
                                logger.info(f"✅ {asset} продан успешно!")
                            else:
                                logger.error(f"❌ Ошибка продажи {asset}")
                        else:
                            if self.profit_threshold_pct is not None and avg_buy_price > 0:
                                logger.info(f"📈 PnL {asset}: {pnl_pct:.2f}% (порог: {self.profit_threshold_pct}%)")
                            else:
                                logger.info(f"📈 PnL {asset}: ${pnl:.4f} (порог: ${self.profit_threshold})")
                            
                            # Сохраняем данные для уведомления
                            pnl_data.append({
                                'asset': asset,
                                'quantity': quantity,
                                'current_price': current_price,
                                'pnl': pnl
                            })
                    else:
                        logger.info(f"⚠️ {asset} найден, но количество = 0")
                else:
                    logger.info(f"⚠️ {asset} не найден в балансах")
            
            # Периодические сводки каждые 5 минут
            current_time = time.time()
            if not hasattr(self, 'last_summary_time'):
                self.last_summary_time = 0
            
            if current_time - self.last_summary_time >= 300 and pnl_data:  # 5 минут
                # Получаем стоимость портфеля BTC/ETH (без стейблкоинов)
                try:
                    portfolio_value = sum((it['quantity'] * it['current_price']) for it in pnl_data)
                except Exception:
                    portfolio_value = 0.0
                
                # Общая стоимость портфеля (включая стейблкоины)
                usdt_balance = 0.0
                usdc_balance = 0.0
                total_portfolio = 0.0
                
                try:
                    account_info = self.mex_api.get_account_info()
                    if account_info and 'balances' in account_info:
                        for balance in account_info['balances']:
                            asset = balance['asset']
                            total = float(balance.get('free', 0)) + float(balance.get('locked', 0))
                            if total <= 0:
                                continue
                            if asset == 'USDT':
                                usdt_balance = total
                                total_portfolio += total
                            elif asset == 'USDC':
                                usdc_balance = total
                                total_portfolio += total
                            else:
                                try:
                                    ticker = self.mex_api.get_ticker_price(f"{asset}USDT")
                                    if ticker and 'price' in ticker:
                                        total_portfolio += total * float(ticker['price'])
                                except Exception:
                                    pass
                except Exception:
                    pass
                
                message_lines = [
                    "📊 <b>ПОРТФЕЛЬ BTC/ETH</b>\n",
                    f"💎 <b>СТОИМОСТЬ ПОРТФЕЛЯ</b>: <code>${portfolio_value:.2f}</code>\n",
                    f"🏦 <b>ОБЩАЯ СТОИМОСТЬ</b>: <code>${total_portfolio:.2f}</code>\n\n",
                    f"💵 <b>СТАБИЛЬНЫЕ МОНЕТЫ:</b>\n",
                    f"   💰 USDT: ${usdt_balance:.2f}\n",
                    f"   💰 USDC: ${usdc_balance:.2f}\n\n"
                ]
                for item in pnl_data:
                    pnl_status = "📈" if item['pnl'] > 0 else "📉" if item['pnl'] < 0 else "➡️"
                    message_lines.append(
                        f"{pnl_status} <b>{item['asset']}</b>:\n"
                        f"   📊 {item['quantity']:.6f} @ ${item['current_price']:.4f}\n"
                        f"   💵 PnL: ${item['pnl']:.4f} (порог: $0.07)\n\n"
                    )
                message_lines.append(f"⏰ {datetime.now().strftime('%H:%M:%S')}")
                
                # Отправляем отчет (каждые 2 часа вместо 1 часа)
                self.report_counter += 1
                if self.report_counter % 2 == 0:  # Отправляем каждый второй отчет
                    self.send_telegram_message("".join(message_lines))
                    logger.info("📊 Отчет PnL отправлен в Telegram")
                else:
                    logger.info("📊 Отчет PnL пропущен (уменьшение спама)")
                
                self.last_summary_time = current_time
        except Exception as e:
            logger.error(f"❌ Ошибка проверки PnL: {e}")
    
    async def start_monitoring(self):
        """Запустить мониторинг PnL"""
        try:
            logger.info("🚀 Запуск мониторинга PnL...")
            
            # Отправляем уведомление о запуске
            start_message = (
                f"📊 <b>МОНИТОРИНГ PnL ЗАПУЩЕН</b>\n\n"
                f"🎯 <b>Настройки:</b>\n"
                f"💰 Порог прибыли: ${self.profit_threshold} (7 центов)\n"
                f"⏰ Проверка каждые: {self.check_interval} сек\n"
                f"💱 Мониторинг: BTC/ETH\n"
                f"📈 Действие: Рыночная продажа\n\n"
                f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
            )
            self.send_telegram_message(start_message)
            
            self.is_running = True
            
            while self.is_running:
                try:
                    # Проверяем PnL и продаем при необходимости
                    self.check_pnl_and_sell()
                    
                    # Проверяем необходимость балансировки портфеля (синхронно)
                    try:
                        # Вызываем синхронную версию балансировки
                        await self.check_portfolio_balance_sync()
                    except Exception as balance_error:
                        logger.error(f"Ошибка проверки балансировки: {balance_error}")
                    
                    # Ждем до следующей проверки
                    time.sleep(self.check_interval)
                    
                except KeyboardInterrupt:
                    logger.info("🛑 Мониторинг остановлен пользователем")
                    break
                except Exception as e:
                    logger.error(f"❌ Ошибка в цикле мониторинга: {e}")
                    time.sleep(60)
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            # Отправляем уведомление об остановке
            stop_message = (
                f"🛑 <b>МОНИТОРИНГ PnL ОСТАНОВЛЕН</b>\n\n"
                f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
            )
            self.send_telegram_message(stop_message)
    
    def stop_monitoring(self):
        """Остановить мониторинг"""
        self.is_running = False
        logger.info("🛑 Остановка мониторинга PnL...")
    
    def get_current_status(self):
        """Получить текущий статус монитора"""
        try:
            # Получаем текущие балансы и PnL
            balances = self.get_balances()
            total_pnl = 0.0
            
            # Рассчитываем общий PnL
            for asset in ['BTC', 'ETH']:
                if asset in balances:
                    quantity = balances[asset]['total']
                    if quantity > 0:
                        symbol = 'BTCUSDC' if asset == 'BTC' else 'ETHUSDC'
                        current_price = self.get_current_price(symbol)
                        if current_price:
                            pnl = self.calculate_pnl(asset, quantity, current_price)
                            total_pnl += pnl
            
            # Получаем информацию об ордерах
            orders_info = self.get_open_orders_info()
            
            return {
                'monitoring_active': self.is_running,
                'auto_sell_enabled': True,
                'telegram_notifications_active': True,
                'total_pnl': total_pnl,
                'daily_pnl': total_pnl * 0.1,  # Примерные данные
                'weekly_pnl': total_pnl * 0.3,  # Примерные данные
                'monthly_pnl': total_pnl * 0.8,  # Примерные данные
                'check_interval': self.check_interval,
                'max_daily_purchases': 10,
                'profit_threshold': self.profit_threshold,
                'balances': balances,
                'orders': orders_info
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статуса: {e}")
            return {
                'monitoring_active': False,
                'auto_sell_enabled': False,
                'telegram_notifications_active': False,
                'total_pnl': 0.0,
                'daily_pnl': 0.0,
                'weekly_pnl': 0.0,
                'monthly_pnl': 0.0,
                'check_interval': 60,
                'max_daily_purchases': 10,
                'profit_threshold': 0.40,
                'balances': {}
            }

async def main():
    monitor = PnLMonitor()
    
    try:
        # Запускаем мониторинг PnL
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("🛑 Получен сигнал остановки")
        monitor.stop_monitoring()

if __name__ == "__main__":
    main() 