#!/usr/bin/env python3
"""
IncomeSaver — «парковка» лишнего USDT в USDP при превышении порога.

Параметры по умолчанию:
- threshold_usdt = 395.0
- unit_amount_usdt = 5.0 (биржевой minNotional часто >= $5; тест на $1 возможен, но может быть отклонён)
- min_reserve_usdt = 20.0
- cooldown_sec = 300
- symbol = 'USDPUSDT'
"""

import time
import logging
from typing import Optional, Dict

from mex_api import MexAPI
from mexc_advanced_api import MexAdvancedAPI

logger = logging.getLogger(__name__)


class IncomeSaver:
    def __init__(self,
                 threshold_usdt: float = 395.0,
                 unit_amount_usdt: float = 5.0,
                 min_reserve_usdt: float = 20.0,
                 cooldown_sec: int = 300,
                 symbol: str = 'USDPUSDT'):
        self.mex_api = MexAPI()
        self.mex_adv = MexAdvancedAPI()
        self.threshold_usdt = threshold_usdt
        self.unit_amount_usdt = unit_amount_usdt
        self.min_reserve_usdt = min_reserve_usdt
        self.cooldown_sec = cooldown_sec
        self.symbol = symbol
        self._last_action_ts = 0

    # ==== balances ====
    def get_usdt_balance(self) -> float:
        try:
            account_info = self.mex_api.get_account_info()
            if not isinstance(account_info, dict):
                return 0.0
            for b in account_info.get('balances', []):
                if b.get('asset') == 'USDT':
                    return float(b.get('free', 0))
            return 0.0
        except Exception as e:
            logger.warning(f"IncomeSaver: ошибка чтения баланса USDT: {e}")
            return 0.0

    # ==== rules and rounding ====
    @staticmethod
    def _round_to_step(value: float, step: float) -> float:
        if step <= 0:
            return value
        return (int(value / step)) * step

    def _load_symbol_rules(self) -> Dict:
        try:
            rules = self.mex_adv.get_symbol_rules(self.symbol)
            return rules or {}
        except Exception as e:
            logger.warning(f"IncomeSaver: не удалось получить правила для {self.symbol}: {e}")
            return {}

    # ==== price ====
    def get_price(self) -> Optional[float]:
        try:
            ticker = self.mex_api.get_ticker_price(self.symbol)
            p = float(ticker.get('price')) if isinstance(ticker, dict) and 'price' in ticker else None
            return p
        except Exception as e:
            logger.warning(f"IncomeSaver: не удалось получить цену {self.symbol}: {e}")
            return None

    # ==== core ====
    def _eligible_now(self) -> bool:
        if (time.time() - self._last_action_ts) < self.cooldown_sec:
            return False
        usdt = self.get_usdt_balance()
        if usdt < (self.threshold_usdt + self.unit_amount_usdt):
            return False
        # не трогаем резерв
        if (usdt - self.unit_amount_usdt) < self.min_reserve_usdt:
            return False
        return True

    def try_park_usdt_to_usdp(self, unit_amount_usdt: Optional[float] = None) -> Dict:
        """Попытаться «спрятать» unit_amount_usdt в USDP (через USDPUSDT BUY).

        Возвращает dict с success, либо ошибкой и причиной.
        """
        amount = unit_amount_usdt if unit_amount_usdt is not None else self.unit_amount_usdt

        if amount <= 0:
            return {'success': False, 'error': 'amount_must_be_positive'}

        if not self._eligible_now():
            return {'success': False, 'error': 'not_eligible_now'}

        rules = self._load_symbol_rules()
        price = self.get_price()
        if not price or price <= 0:
            return {'success': False, 'error': 'no_price'}

        step_size = rules.get('stepSize', 0.0) or 0.0
        tick_size = rules.get('tickSize', 0.0) or 0.0
        min_notional = rules.get('minNotional', 5.0) or 5.0

        # Проверка минимального нотионала
        if amount < min_notional:
            # Всё равно позволим тест, но пометим как вероятно отклонённый биржей
            pass

        # Расчёт количества USDP: qty = amount / price
        raw_qty = amount / price
        qty = raw_qty
        if step_size > 0:
            qty = self._round_to_step(raw_qty, step_size)
            if qty <= 0:
                qty = step_size

        # Контроль нотионала после округления
        notional = qty * price
        if notional < min_notional and amount >= min_notional:
            # Попробуем поднять qty до минимума
            needed_qty = min_notional / price
            if step_size > 0:
                # округляем вниз до сетки шага, но не ниже исходного qty
                k = int(needed_qty / step_size)
                qty2 = max(qty, k * step_size)
            else:
                qty2 = max(qty, needed_qty)
            qty = qty2
            notional = qty * price

        # Ограничение на цену (tickSize) – торговля маркетом, так что не критично
        # Размещаем маркет BUY (через MexAPI.place_market_order)
        order = self.mex_api.place_market_order(self.symbol, 'BUY', qty)

        if order and isinstance(order, dict) and order.get('orderId'):
            self._last_action_ts = time.time()
            return {
                'success': True,
                'symbol': self.symbol,
                'order_id': order['orderId'],
                'qty': qty,
                'price_snapshot': price,
                'notional': notional,
                'note': 'placed_market_buy_usdpusdt'
            }
        return {'success': False, 'error': f'order_failed: {order}'}


