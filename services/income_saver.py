#!/usr/bin/env python3
"""
IncomeSaver — «парковка» лишнего USDT в USDP при превышении порога.

Параметры по умолчанию:
- threshold_usdt = 395.0
- unit_amount_usdt = 1.0
- min_reserve_usdt = 20.0
- cooldown_sec = 300
- symbol = 'USDPUSDT'
"""

import time
import logging
from typing import Optional, Dict

from mex_api import MexAPI
from mexc_advanced_api import MexAdvancedAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests

logger = logging.getLogger(__name__)


class IncomeSaver:
    def __init__(self,
                 threshold_usdt: float = 395.0,
                 unit_amount_usdt: float = 1.0,
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
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID

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

    def get_usdc_balance(self) -> float:
        try:
            account_info = self.mex_api.get_account_info()
            if not isinstance(account_info, dict):
                return 0.0
            for b in account_info.get('balances', []):
                if b.get('asset') == 'USDC':
                    return float(b.get('free', 0))
            return 0.0
        except Exception as e:
            logger.warning(f"IncomeSaver: ошибка чтения баланса USDC: {e}")
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

    def get_symbol_price(self, symbol: str) -> Optional[float]:
        try:
            t = self.mex_api.get_ticker_price(symbol)
            if isinstance(t, dict) and 'price' in t:
                return float(t['price'])
            return None
        except Exception:
            return None

    def get_portfolio_value_usdt_excluding_usdp(self) -> float:
        """Рассчитать общую стоимость портфеля в USDT, исключая USDP."""
        try:
            account_info = self.mex_api.get_account_info()
            if not isinstance(account_info, dict):
                return 0.0
            total_usdt_value = 0.0
            balances = account_info.get('balances', []) or []
            # Курс USDCUSDT для конвертации USDC→USDT
            usdc_usdt = self.get_symbol_price('USDCUSDT') or 1.0
            for b in balances:
                try:
                    asset = b.get('asset')
                    free_amt = float(b.get('free', 0) or 0)
                    locked_amt = float(b.get('locked', 0) or 0)
                    total_amt = free_amt + locked_amt
                    if total_amt <= 0:
                        continue
                    if asset == 'USDP':
                        # Парковочная валюта исключается
                        continue
                    if asset == 'USDT':
                        total_usdt_value += total_amt
                    elif asset == 'USDC':
                        total_usdt_value += total_amt * usdc_usdt
                    else:
                        price = self.get_symbol_price(f"{asset}USDT")
                        if price:
                            total_usdt_value += total_amt * price
                except Exception:
                    continue
            return total_usdt_value
        except Exception as e:
            logger.warning(f"IncomeSaver: не удалось рассчитать стоимость портфеля: {e}")
            return 0.0

    def ensure_usdt_liquidity(self, required_usdt: float) -> bool:
        """Обеспечить наличие свободного USDT. При нехватке — продать USDC за USDT (USDCUSDT SELL)."""
        try:
            if required_usdt <= 0:
                return True
            usdt_free = self.get_usdt_balance()
            if usdt_free >= required_usdt:
                return True
            deficit = required_usdt - usdt_free
            usdc_free = self.get_usdc_balance()
            if usdc_free <= 0:
                return False
            price = self.get_symbol_price('USDCUSDT') or 1.0
            # Сколько USDC нужно продать, чтобы получить требуемый USDT
            qty_usdc = deficit / max(price, 1e-8)
            # Округлим до 2 знаков (типично для стейблов) и добавим небольшой запас
            qty_usdc = round(qty_usdc * 1.01, 2)
            if qty_usdc > usdc_free:
                qty_usdc = round(usdc_free, 2)
            if qty_usdc <= 0:
                return False
            order = self.mex_api.place_market_order('USDCUSDT', 'SELL', qty_usdc)
            return bool(order and isinstance(order, dict) and order.get('orderId'))
        except Exception as e:
            logger.warning(f"IncomeSaver: не удалось обеспечить USDT ликвидность: {e}")
            return False

    # ==== telegram ====
    def _send_telegram(self, text: str) -> None:
        try:
            if not self.bot_token or not self.chat_id:
                return
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = { 'chat_id': self.chat_id, 'text': text, 'parse_mode': 'HTML' }
            requests.post(url, data=data, timeout=10)
        except Exception:
            pass

    # ==== core ====
    def _eligible_now(self, amount: float) -> bool:
        if (time.time() - self._last_action_ts) < self.cooldown_sec:
            return False
        portfolio_value = self.get_portfolio_value_usdt_excluding_usdp()
        # Порог по общей стоимости портфеля (исключая USDP)
        if portfolio_value < (self.threshold_usdt + amount):
            return False
        return True

    def try_park_usdt_to_usdp(self, unit_amount_usdt: Optional[float] = None) -> Dict:
        """Попытаться «спрятать» unit_amount_usdt в USDP (через USDPUSDT BUY).

        Возвращает dict с success, либо ошибкой и причиной.
        """
        amount = unit_amount_usdt if unit_amount_usdt is not None else self.unit_amount_usdt

        if amount <= 0:
            return {'success': False, 'error': 'amount_must_be_positive'}

        if not self._eligible_now(amount):
            msg = (
                f"<b>💤 PARK SKIPPED</b> — условие не выполнено\n"
                f"Порог: ${self.threshold_usdt:.2f}, попытка спрятать: ${amount:.2f}"
            )
            self._send_telegram(msg)
            return {'success': False, 'error': 'not_eligible_now'}

        # Обеспечим наличие свободного USDT на сумму парковки (при нехватке продадим USDC→USDT)
        if not self.ensure_usdt_liquidity(amount):
            msg = (
                f"<b>❌ PARK FAIL</b> — нет ликвидности USDT для ${amount:.2f}\n"
                f"Попробуйте конвертацию USDC→USDT вручную или увеличьте баланс"
            )
            self._send_telegram(msg)
            return {'success': False, 'error': 'insufficient_liquidity_usdt'}

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
            msg = (
                f"<b>✅ PARK OK</b> — USDT→USDP\n"
                f"Сумма: ${amount:.2f}\n"
                f"Qty: {qty:.4f} USDP @ ~${price:.4f}\n"
                f"Notional: ${notional:.2f}\n"
                f"OrderId: <code>{order['orderId']}</code>"
            )
            self._send_telegram(msg)
            return {
                'success': True,
                'symbol': self.symbol,
                'order_id': order['orderId'],
                'qty': qty,
                'price_snapshot': price,
                'notional': notional,
                'note': 'placed_market_buy_usdpusdt'
            }
        msg = (
            f"<b>❌ PARK FAIL</b> — ошибка ордера\n"
            f"Сумма: ${amount:.2f}\n"
            f"Причина: {order}"
        )
        self._send_telegram(msg)
        return {'success': False, 'error': f'order_failed: {order}'}


