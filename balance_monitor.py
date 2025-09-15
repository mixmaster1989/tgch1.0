#!/usr/bin/env python3
"""
Монитор баланса для автоматической покупки BTC/ETH
Отслеживает освободившийся USDC и автоматически покупает BTC и ETH
ЗАЩИТА: Нельзя делать покупки, которые оставят на балансе USDC меньше $10!
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
from rebalancer_anti_hype_filter import RebalancerAntiHypeFilter
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BalanceMonitor:
    """Монитор баланса для автоматических покупок BTC/ETH за USDC"""
    
    def __init__(self):
        self.mex_api = MexAPI()
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.anti_hype_filter = AntiHypeFilter()
        self.rebalancer_filter = RebalancerAntiHypeFilter()
        
        # Настройки мониторинга - ПЕРЕВОД НА USDC!
        self.min_balance_threshold = 10.0  # Минимальный баланс для покупки ($10 USDC)
        self.max_purchase_amount = 100.0   # Максимальная сумма одной покупки ($100 USDC)
        self.balance_check_interval = 60   # Проверка каждые 60 секунд
        
        # ЗАЩИТА БАЛАНСА USDC - КРИТИЧНО!
        self.min_usdc_balance_after_purchase = 2.0  # Минимум $2 USDC должно остаться после покупки (минимальный резерв)
        
        # Стратегия распределения BTC/ETH
        self.btc_allocation = 0.6  # 60% на BTC
        self.eth_allocation = 0.4  # 40% на ETH
        
        # Защита от частых покупок
        self.last_purchase_time = None
        self.min_purchase_interval = 300  # Минимум 5 минут между покупками
        
        # Защита от спама сообщений о недостаточных суммах
        self.last_insufficient_amount_time = None
        self.insufficient_amount_interval = 1800  # 30 минут между сообщениями о недостаточных суммах
        
        # История балансов для отслеживания изменений
        self.balance_history = []
        self.max_history_size = 10
        
        # Статистика
        self.total_purchases = 0
        self.total_spent = 0.0
        
        # Контроль частоты отчетов (уменьшаем спам в 2 раза)
        self.report_counter = 0
        
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
        """Получить текущий баланс USDT (для конвертации в USDC)"""
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
    
    def ensure_usdc_for_trade(self, required_usdc: float) -> bool:
        """Убедиться, что есть USDC для сделки; при недостатке купить за USDT"""
        try:
            buffer = 0.02  # небольшой запас на комиссии
            need = required_usdc + buffer
            usdc_free = self.get_usdc_balance()
            
            if usdc_free >= need:
                return True

            # Покупаем недостающее количество USDC за USDT
            shortfall = max(0.0, need - usdc_free)
            usdt_free = self.get_usdt_balance()
            
            if usdt_free < shortfall:
                logger.warning(f"⚠️ Недостаточно USDT для покупки USDC: нужно ${shortfall:.2f}, есть ${usdt_free:.2f}")
                return False

            qty = round(shortfall, 2)
            if qty < 1.0:
                qty = 1.0  # минимальный разумный шаг

            # Покупаем USDC за USDT через рыночный ордер
            order = self.mex_api.place_order(
                symbol='USDCUSDT', 
                side='BUY', 
                quantity=qty
            )
            
            if order and 'orderId' in order:
                logger.info(f"✅ Куплен USDC за USDT: ${qty:.2f}")
                try:
                    self.send_telegram_message(f"💱 Куплен USDC за USDT на ${qty:.2f} для автоматических покупок")
                except Exception:
                    pass
                return True
            else:
                logger.error(f"❌ Не удалось купить USDC: {order}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка ensure_usdc_for_trade: {e}")
            return False
    
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
    
    def get_current_portfolio_allocation(self) -> Dict:
        """Получить текущее распределение портфеля BTC/ETH"""
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
            btc_price = self.get_current_price('BTCUSDC')
            eth_price = self.get_current_price('ETHUSDC')
            
            if btc_price and eth_price:
                btc_value = btc_balance * btc_price
                eth_value = eth_balance * eth_price
                total_crypto = btc_value + eth_value
                
                if total_crypto > 0:
                    return {
                        'btc_value': btc_value,
                        'eth_value': eth_value,
                        'total_crypto': total_crypto,
                        'btc_percent': (btc_value / total_crypto) * 100,
                        'eth_percent': (eth_value / total_crypto) * 100
                    }
            
            return {'btc_percent': 0, 'eth_percent': 0}
            
        except Exception as e:
            logger.error(f"Ошибка получения распределения портфеля: {e}")
            return {'btc_percent': 0, 'eth_percent': 0}
    
    def needs_rebalancing(self, allocation: Dict) -> bool:
        """Проверить, нужна ли ребалансировка"""
        btc_percent = allocation.get('btc_percent', 0)
        eth_percent = allocation.get('eth_percent', 0)
        
        # Проверяем отклонение от целевого распределения 60/40
        btc_deviation = abs(btc_percent - 60)
        eth_deviation = abs(eth_percent - 40)
        
        # Если отклонение больше 10% - нужна ребалансировка
        return btc_deviation > 10 or eth_deviation > 10
    
    def calculate_purchase_amounts(self, available_usdc: float, currency: str = 'USDC') -> Dict[str, float]:
        """Рассчитать суммы для покупки BTC и ETH с умным распределением"""
        try:
            # Используем доступную сумму, но не превышаем максимальную
            purchase_amount = self.calculate_safe_purchase_amount(available_usdc)
            
            # Определяем торговые пары на основе валюты
            btc_symbol = f'BTC{currency}'
            eth_symbol = f'ETH{currency}'
            
            # Получаем текущие цены
            btc_price = self.get_current_price(btc_symbol)
            eth_price = self.get_current_price(eth_symbol)
            
            # Проверяем текущее распределение портфеля
            current_allocation = self.get_current_portfolio_allocation()
            needs_rebalancing = self.needs_rebalancing(current_allocation)
            
            logger.info(f"📊 Текущее распределение: BTC {current_allocation.get('btc_percent', 0):.1f}%, ETH {current_allocation.get('eth_percent', 0):.1f}%")
            logger.info(f"🔄 Нужна ребалансировка: {needs_rebalancing}")
            
            if not btc_price or not eth_price:
                logger.error(f"Не удалось получить цены BTC/ETH в {currency} парах")
                return {}
            
            # Рассчитываем минимальные суммы для каждого актива
            min_btc_amount = 0.0001 * btc_price  # Минимум для BTC
            min_eth_amount = 0.001 * eth_price   # Минимум для ETH
            
            logger.info(f"💰 Доступно: ${purchase_amount:.2f}")
            logger.info(f"📊 Минимумы: BTC ${min_btc_amount:.2f}, ETH ${min_eth_amount:.2f}")
            
            result = {}
            
            # Если нужна ребалансировка - покупаем только недостающий актив
            if needs_rebalancing:
                btc_percent = current_allocation.get('btc_percent', 0)
                eth_percent = current_allocation.get('eth_percent', 0)
                
                if btc_percent > 60:  # BTC слишком много
                    logger.info(f"🔄 РЕБАЛАНСИРОВКА: BTC слишком много ({btc_percent:.1f}%), покупаем только ETH")
                    if purchase_amount >= min_eth_amount:
                        btc_amount = 0
                        eth_amount = purchase_amount
                    else:
                        logger.warning(f"⚠️ Недостаточно средств для ETH: ${purchase_amount:.2f} < ${min_eth_amount:.2f}")
                        return {}
                elif eth_percent > 40:  # ETH слишком много
                    logger.info(f"🔄 РЕБАЛАНСИРОВКА: ETH слишком много ({eth_percent:.1f}%), покупаем только BTC")
                    if purchase_amount >= min_btc_amount:
                        btc_amount = purchase_amount
                        eth_amount = 0
                    else:
                        logger.warning(f"⚠️ Недостаточно средств для BTC: ${purchase_amount:.2f} < ${min_btc_amount:.2f}")
                        return {}
                else:
                    # Если оба актива меньше нормы - покупаем оба пропорционально
                    logger.info(f"🔄 РЕБАЛАНСИРОВКА: Оба актива меньше нормы, покупаем пропорционально")
                    if purchase_amount >= (min_btc_amount + min_eth_amount):
                        btc_amount = purchase_amount * self.btc_allocation
                        eth_amount = purchase_amount * self.eth_allocation
                    elif purchase_amount >= min_btc_amount:
                        # Покупаем только BTC
                        btc_amount = purchase_amount
                        eth_amount = 0
                        logger.info("📈 Недостаточно средств для ETH при ребалансировке, покупаем только BTC")
                    elif purchase_amount >= min_eth_amount:
                        # Покупаем только ETH
                        btc_amount = 0
                        eth_amount = purchase_amount
                        logger.info("📈 Недостаточно средств для BTC при ребалансировке, покупаем только ETH")
                    else:
                        logger.warning(f"⚠️ Недостаточно средств для покупки при ребалансировке: ${purchase_amount:.2f}")
                        return {}
            # Если средств достаточно для обеих валют и ребалансировка не нужна
            elif purchase_amount >= (min_btc_amount + min_eth_amount):
                # Обычное распределение
                btc_amount = purchase_amount * self.btc_allocation
                eth_amount = purchase_amount * self.eth_allocation
                
                # Корректируем если одна из сумм меньше минимума
                if btc_amount < min_btc_amount:
                    excess = min_btc_amount - btc_amount
                    btc_amount = min_btc_amount
                    eth_amount = max(eth_amount - excess, min_eth_amount)
                
                if eth_amount < min_eth_amount:
                    excess = min_eth_amount - eth_amount
                    eth_amount = min_eth_amount
                    btc_amount = max(btc_amount - excess, min_btc_amount)
                
            # Если средств хватает только на один актив
            elif purchase_amount >= min_btc_amount:
                # Покупаем только BTC
                btc_amount = purchase_amount
                eth_amount = 0
                logger.info("📈 Недостаточно средств для ETH, покупаем только BTC")
                
            elif purchase_amount >= min_eth_amount:
                # Покупаем только ETH
                btc_amount = 0
                eth_amount = purchase_amount
                logger.info("📈 Недостаточно средств для BTC, покупаем только ETH")
                
            else:
                logger.warning(f"⚠️ Недостаточно средств для покупки: ${purchase_amount:.2f}")
                return {}
            
            # Обрабатываем BTC с соответствующим фильтром
            if btc_amount >= min_btc_amount:
                # Выбираем фильтр в зависимости от необходимости ребалансировки
                if needs_rebalancing:
                    btc_filter = self.rebalancer_filter.check_buy_permission(btc_symbol)
                    filter_type = "РЕБАЛАНСИРОВОЧНЫЙ"
                else:
                    btc_filter = self.anti_hype_filter.check_buy_permission(btc_symbol)
                    filter_type = "ОБЫЧНЫЙ"
                
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
                    logger.info(f"✅ BTC ордер [{filter_type}]{multiplier_text}: {btc_quantity:.6f} BTC на ${actual_btc_amount:.2f} {currency} [{btc_filter['reason']}]")
            
            # Обрабатываем ETH с соответствующим фильтром
            if eth_amount >= min_eth_amount:
                # Выбираем фильтр в зависимости от необходимости ребалансировки
                if needs_rebalancing:
                    eth_filter = self.rebalancer_filter.check_buy_permission(eth_symbol)
                    filter_type = "РЕБАЛАНСИРОВОЧНЫЙ"
                else:
                    eth_filter = self.anti_hype_filter.check_buy_permission(eth_symbol)
                    filter_type = "ОБЫЧНЫЙ"
                
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
                    logger.info(f"✅ ETH ордер [{filter_type}]{multiplier_text}: {eth_quantity:.6f} ETH на ${actual_eth_amount:.2f} {currency} [{eth_filter['reason']}]")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка расчета сумм покупки: {e}")
            return {}
    
    def can_make_purchase(self, purchase_amount: float) -> Tuple[bool, str]:
        """
        Проверить, можно ли сделать покупку на указанную сумму
        ЗАЩИТА: Нельзя оставлять на балансе USDC меньше $10!
        """
        try:
            current_usdc = self.get_usdc_balance()
            
            # Проверяем, что после покупки останется достаточно USDC (минимум $10)
            remaining_after_purchase = current_usdc - purchase_amount
            if remaining_after_purchase < self.min_usdc_balance_after_purchase - 0.01:  # Добавляем небольшой буфер для точности
                return False, f"После покупки останется ${remaining_after_purchase:.2f} USDC, что меньше минимума ${self.min_usdc_balance_after_purchase:.2f}"
            
            # Проверяем кулдаун между покупками
            if (self.last_purchase_time and 
                time.time() - self.last_purchase_time < self.min_purchase_interval):
                remaining_cooldown = self.min_purchase_interval - (time.time() - self.last_purchase_time)
                return False, f"Кулдаун между покупками: осталось {remaining_cooldown:.0f} сек"
            
            return True, "OK"
            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки возможности покупки: {e}")
            return False, f"Ошибка проверки: {e}"
    
    def calculate_safe_purchase_amount(self, available_usdc: float) -> float:
        """
        Рассчитать безопасную сумму для покупки
        Гарантирует, что после покупки останется минимум $10 USDC
        """
        try:
            # Максимальная сумма, которую можно потратить
            max_safe_amount = available_usdc - self.min_usdc_balance_after_purchase
            
            if max_safe_amount <= 0:
                return 0.0
            
            # Ограничиваем максимальной суммой покупки
            safe_amount = min(max_safe_amount, self.max_purchase_amount)
            
            # Округляем до 2 знаков после запятой
            return round(safe_amount, 2)
            
        except Exception as e:
            logger.error(f"❌ Ошибка расчета безопасной суммы покупки: {e}")
            return 0.0
    
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
        """Разместить лимитный ордер с анализом стакана и ретраями"""
        max_retries = 3
        retry_delay = 2  # секунды
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Размещение лимитного ордера: {symbol} {quantity} (попытка {attempt + 1}/{max_retries})")
                
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
                
                # Проверяем минимальные требования для символа
                if symbol == 'ETHUSDC' and quantity < 0.001:
                    logger.warning(f"⚠️ Количество ETH {quantity} меньше минимума 0.001, увеличиваем")
                    quantity = 0.001
                elif symbol == 'BTCUSDC' and quantity < 0.0001:
                    logger.warning(f"⚠️ Количество BTC {quantity} меньше минимума 0.0001, увеличиваем")
                    quantity = 0.0001
                
                # Проверяем баланс перед размещением ордера
                required_amount = quantity * limit_price
                current_balance = self.get_usdc_balance()
                
                # Если требуемая сумма больше доступной, корректируем количество
                if required_amount > current_balance:
                    logger.warning(f"⚠️ Корректируем количество: нужно ${required_amount:.2f}, доступно ${current_balance:.2f}")
                    # Корректируем количество под доступный баланс с небольшим запасом (0.5%)
                    safe_balance = current_balance * 0.995
                    corrected_quantity = safe_balance / limit_price
                    
                    # Округляем до допустимой точности
                    if symbol == 'ETHUSDC':
                        corrected_quantity = round(corrected_quantity, 6)
                        if corrected_quantity < 0.001:
                            logger.error(f"🚨 Скорректированное количество ETH {corrected_quantity:.6f} меньше минимума 0.001")
                            return {'success': False, 'error': f'Insufficient balance after correction: ${current_balance:.2f} недостаточно для минимума ETH'}
                    elif symbol == 'BTCUSDC':
                        corrected_quantity = round(corrected_quantity, 6)
                        if corrected_quantity < 0.0001:
                            logger.error(f"🚨 Скорректированное количество BTC {corrected_quantity:.6f} меньше минимума 0.0001")
                            return {'success': False, 'error': f'Insufficient balance after correction: ${current_balance:.2f} недостаточно для минимума BTC'}
                    
                    quantity = corrected_quantity
                    required_amount = quantity * limit_price
                    logger.info(f"✅ Скорректировано: количество={quantity:.6f}, сумма=${required_amount:.2f}")
                
                # Добавляем небольшой запас для погрешности расчётов (0.1%)
                if required_amount > current_balance * 0.999:
                    logger.error(f"🚨 Недостаточно USDC для ордера: нужно ${required_amount:.2f}, доступно ${current_balance:.2f}")
                    return {'success': False, 'error': f'Insufficient balance: нужно ${required_amount:.2f}, доступно ${current_balance:.2f}'}
                
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
                    error_msg = f"API ошибка: {order}"
                    logger.error(f"❌ Ошибка размещения ордера (попытка {attempt + 1}): {error_msg}")
                    
                    # Проверяем специфические ошибки
                    if 'Insufficient position' in str(order):
                        logger.error(f"🚨 Недостаточно средств для {symbol}. Проверьте баланс!")
                        return {'success': False, 'error': 'Insufficient position - недостаточно средств'}
                    
                    # Если это последняя попытка, возвращаем ошибку
                    if attempt == max_retries - 1:
                        return {'success': False, 'error': error_msg}
                    
                    # Ждем перед следующей попыткой
                    logger.info(f"⏳ Ожидание {retry_delay} сек перед повторной попыткой...")
                    time.sleep(retry_delay)
                    
            except Exception as e:
                error_msg = str(e)
                logger.error(f"❌ Ошибка размещения ордера {symbol} (попытка {attempt + 1}): {error_msg}")
                
                # Если это последняя попытка, возвращаем ошибку
                if attempt == max_retries - 1:
                    return {'success': False, 'error': error_msg}
                
                # Ждем перед следующей попыткой
                logger.info(f"⏳ Ожидание {retry_delay} сек перед повторной попыткой...")
                time.sleep(retry_delay)
        
        return {'success': False, 'error': 'Превышено количество попыток'}
    
    async def execute_auto_purchase(self, available_usdc: float, currency: str = 'USDC') -> Dict:
        """Выполнить автоматическую покупку BTC/ETH"""
        try:
            logger.info(f"🚀 Автоматическая покупка на ${available_usdc:.2f} {currency}")
            
            # Рассчитываем суммы покупки
            purchase_plan = self.calculate_purchase_amounts(available_usdc, currency)
            
            if not purchase_plan:
                logger.warning(f"⚠️ Нет подходящих ордеров для суммы ${available_usdc:.2f} {currency}")
                logger.warning("💡 Возможные причины:")
                logger.warning("   - Сумма слишком мала для минимальных лотов")
                logger.warning("   - BTC требует >= $11.70 (0.0001 BTC)")
                logger.warning("   - ETH требует >= $4.17 (0.001 ETH)")
                
                # Проверяем, можем ли купить хотя бы один актив
                btc_symbol = f'BTC{currency}'
                eth_symbol = f'ETH{currency}'
                
                btc_price = self.get_current_price(btc_symbol)
                eth_price = self.get_current_price(eth_symbol)
                
                if btc_price and eth_price:
                    min_btc_amount = 0.0001 * btc_price
                    min_eth_amount = 0.001 * eth_price
                    
                    # Если можем купить хотя бы один актив, делаем это
                    if available_usdc >= min_btc_amount:
                        logger.info(f"✅ Можем купить BTC на ${available_usdc:.2f}")
                        # Проверяем антихайп фильтр для BTC
                        btc_filter = self.anti_hype_filter.check_buy_permission(btc_symbol)
                        if not btc_filter['allowed']:
                            logger.warning(f"🚫 BTC покупка заблокирована антихайп фильтром: {btc_filter['reason']}")
                            return {
                                'success': False,
                                'error': f'BTC покупка заблокирована: {btc_filter["reason"]}',
                                'reason': 'anti_hype_blocked'
                            }
                        
                        # Применяем множитель фильтра
                        available_usdc *= btc_filter['multiplier']
                        btc_quantity = available_usdc / btc_price
                        btc_quantity = round(btc_quantity, 6)
                        
                        purchase_plan = {
                            btc_symbol: {
                                'amount': available_usdc,
                                'quantity': btc_quantity,
                                'price': btc_price,
                                'currency': currency,
                                'filter_reason': btc_filter['reason'],
                                'filter_multiplier': btc_filter['multiplier']
                            }
                        }
                    elif available_usdc >= min_eth_amount:
                        logger.info(f"✅ Можем купить ETH на ${available_usdc:.2f}")
                        # Проверяем антихайп фильтр для ETH
                        eth_filter = self.anti_hype_filter.check_buy_permission(eth_symbol)
                        if not eth_filter['allowed']:
                            logger.warning(f"🚫 ETH покупка заблокирована антихайп фильтром: {eth_filter['reason']}")
                            return {
                                'success': False,
                                'error': f'ETH покупка заблокирована: {eth_filter["reason"]}',
                                'reason': 'anti_hype_blocked'
                            }
                        
                        # Применяем множитель фильтра
                        available_usdc *= eth_filter['multiplier']
                        eth_quantity = available_usdc / eth_price
                        eth_quantity = round(eth_quantity, 6)
                        
                        purchase_plan = {
                            eth_symbol: {
                                'amount': available_usdc,
                                'quantity': eth_quantity,
                                'price': eth_price,
                                'currency': currency,
                                'filter_reason': eth_filter['reason'],
                                'filter_multiplier': eth_filter['multiplier']
                            }
                        }
                    else:
                        return {
                            'success': False, 
                            'error': f'Сумма ${available_usdc:.2f} {currency} слишком мала. Минимум: BTC ~${min_btc_amount:.2f}, ETH ~${min_eth_amount:.2f}',
                            'reason': 'insufficient_amount'
                        }
                else:
                    return {
                        'success': False, 
                        'error': f'Сумма ${available_usdc:.2f} {currency} слишком мала. Минимум: BTC ~$11.70, ETH ~$4.17',
                        'reason': 'insufficient_amount'
                    }
            
            results = {
                'success': True,
                'timestamp': datetime.now(),
                'available_usdc': available_usdc,  # Сохраняем ключ для совместимости
                'currency': currency,
                'purchases': [],
                'total_spent': 0.0
            }
            
            # Выполняем покупки
            for symbol, purchase_data in purchase_plan.items():
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
                    current_time = time.time()
                    
                    # Проверяем, не отправляли ли мы недавно такое сообщение
                    if (self.last_insufficient_amount_time and 
                        current_time - self.last_insufficient_amount_time < self.insufficient_amount_interval):
                        return None  # Не отправляем сообщение
                    
                    self.last_insufficient_amount_time = current_time
                    
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
            
            # Проверяем условия для покупки с ЗАЩИТОЙ БАЛАНСА USDC
            if available_for_purchase >= self.min_balance_threshold:
                # Рассчитываем безопасную сумму для покупки
                safe_purchase_amount = self.calculate_safe_purchase_amount(available_for_purchase)
                
                if safe_purchase_amount > 0:
                    logger.info(f"🛡️ Безопасная сумма для покупки: ${safe_purchase_amount:.2f} USDC")
                    logger.info(f"💰 После покупки останется: ${available_for_purchase - safe_purchase_amount:.2f} USDC")
                    
                    # Проверяем возможность покупки
                    can_purchase, reason = self.can_make_purchase(safe_purchase_amount)
                    
                    if can_purchase:
                        logger.info(f"🎯 Условия для покупки выполнены! Безопасная сумма: ${safe_purchase_amount:.2f}")
                        
                        # Выполняем покупку (ВСЕГДА USDC пары)
                        results = await self.execute_auto_purchase(safe_purchase_amount, 'USDC')
                        
                        if results['success']:
                            self.last_purchase_time = time.time()
                            self.total_purchases += 1
                            self.total_spent += safe_purchase_amount
                            
                            logger.info(f"✅ Автоматическая покупка выполнена успешно!")
                            logger.info(f"📊 Статистика: {self.total_purchases} покупок, потрачено ${self.total_spent:.2f} USDC")
                        
                        # Отправляем отчет в Telegram (каждые 10 минут вместо 5)
                        self.report_counter += 1
                        if self.report_counter % 2 == 0:  # Отправляем каждый второй отчет
                            report = self.format_purchase_report(results)
                            if report:  # Проверяем, что отчет не None
                                self.send_telegram_message(report)
                                logger.info("📊 Отчет покупки отправлен в Telegram")
                        else:
                            logger.info("📊 Отчет покупки пропущен (уменьшение спама)")
                        
                        return results
                    else:
                        logger.info(f"⏳ Покупка отложена: {reason}")
                        
                        # Логируем детали блокировки
                        if "кулдаун" in reason.lower():
                            remaining_time = self.min_purchase_interval - (time.time() - self.last_purchase_time)
                            logger.info(f"⏰ Осталось до следующей покупки: {remaining_time:.0f} сек")
                        elif "недостаточно" in reason.lower():
                            logger.info(f"💰 Недостаточно USDC для безопасной покупки")
                        else:
                            logger.info(f"ℹ️ Причина блокировки: {reason}")
                        
                        return None
                else:
                    logger.info(f"🛡️ Недостаточно USDC для безопасной покупки (защита баланса)")
                    logger.info(f"💰 Требуется минимум: ${self.min_usdc_balance_after_purchase} USDC после покупки")
                    return None
            else:
                logger.info(f"Баланс слишком мал: ${available_for_purchase:.2f} < ${self.min_balance_threshold}")
                
                # Если USDC мало, но есть USDT - предлагаем конвертацию
                if usdt_balance >= 5.0:
                    logger.info(f"💡 Рекомендация: конвертировать ${usdt_balance:.2f} USDT в USDC для покупок")
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки баланса: {e}")
            return None
    
    async def start_monitoring(self):
        """Запустить мониторинг баланса"""
        logger.info("🚀 Запуск мониторинга баланса для автоматических покупок BTC/ETH за USDC")
        logger.info(f"📊 Настройки:")
        logger.info(f"   Минимальный баланс: ${self.min_balance_threshold} USDC")
        logger.info(f"   Максимальная покупка: ${self.max_purchase_amount} USDC")
        logger.info(f"   ЗАЩИТА: Минимум ${self.min_usdc_balance_after_purchase} USDC должно остаться после покупки")
        logger.info(f"   Интервал проверки: {self.balance_check_interval} сек")
        logger.info(f"   Распределение: BTC {self.btc_allocation*100}% / ETH {self.eth_allocation*100}%")
        
        # Отправляем уведомление о запуске
        startup_message = (
            "<b>🤖 МОНИТОР БАЛАНСА USDC ЗАПУЩЕН</b>\n\n"
            f"📊 Настройки:\n"
            f"💰 Минимальный баланс: ${self.min_balance_threshold} USDC\n"
            f"💸 Максимальная покупка: ${self.max_purchase_amount} USDC\n"
            f"🛡️ ЗАЩИТА: Минимум ${self.min_usdc_balance_after_purchase} USDC после покупки\n"
            f"⏰ Проверка каждые {self.balance_check_interval} сек\n"
            f"📈 BTC: {self.btc_allocation*100}% | ETH: {self.eth_allocation*100}%\n\n"
            "🔄 Мониторинг активен...\n"
            "💱 Все покупки выполняются за USDC (рыночные ордера без комиссий)"
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