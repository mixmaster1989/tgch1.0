#!/usr/bin/env python3
"""
Post-sale 50/50 Balancer
- Поддерживает баланс 50/50 между:
  - Альтами (все активы, кроме BTC/ETH/USDT/USDC) — считается в USDT
  - BTC и ETH — считается в USDC
- Выполняет только конвертацию свободных средств между USDT и USDC после продажи
- Не продаёт позиции ради ребаланса; ждёт, пока появятся свободные средства
"""

import logging
from typing import Dict, Tuple

from mex_api import MexAPI
from mexc_advanced_api import MexAdvancedAPI
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)


class PostSaleBalancer:
	"""Балансировщик, запускаемый после продажи, который стремится к 50/50."""

	def __init__(self):
		self.mex = MexAPI()
		self.adv = MexAdvancedAPI()
		self.keep_assets = {'BTC', 'ETH', 'USDT', 'USDC'}
		self.bot_token = TELEGRAM_BOT_TOKEN
		self.chat_id = TELEGRAM_CHAT_ID

	def _send_telegram_message(self, message: str):
		if not self.bot_token or not self.chat_id:
			return
		try:
			url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
			requests.post(url, data={'chat_id': self.chat_id, 'text': message, 'parse_mode': 'HTML'})
		except Exception:
			pass

	def _get_usdc_usdt_price(self) -> float:
		try:
			info = self.mex.get_ticker_price('USDCUSDT')
			return float(info['price']) if 'price' in info else 1.0
		except Exception:
			return 1.0

	def _get_price(self, symbol: str) -> float:
		try:
			info = self.mex.get_ticker_price(symbol)
			return float(info['price']) if 'price' in info else 0.0
		except Exception:
			return 0.0

	def _get_symbol_rules(self, symbol: str) -> Dict:
		try:
			return self.adv.get_symbol_rules(symbol) or {}
		except Exception:
			return {}

	def _round_to_step(self, quantity: float, step: float) -> float:
		from decimal import Decimal, ROUND_DOWN
		if step <= 0:
			return quantity
		d_q = Decimal(str(quantity))
		d_s = Decimal(str(step))
		q = (d_q / d_s).to_integral_exact(rounding=ROUND_DOWN)
		return float((q * d_s).normalize())

	def _collect_balances(self) -> Dict[str, Dict]:
		info = self.mex.get_account_info() or {}
		result: Dict[str, Dict] = {}
		for b in info.get('balances', []) or []:
			try:
				free = float(b.get('free', 0) or 0)
				locked = float(b.get('locked', 0) or 0)
				total = free + locked
				if free > 0 or locked > 0:
					result[b['asset']] = {'free': free, 'locked': locked, 'total': total}
			except Exception:
				continue
		return result

	def _compute_portfolios_value(self) -> Tuple[float, float, float, float]:
		"""Возвращает:
		alts_value_usdt, btceth_value_usdc, free_usdt, free_usdc
		"""
		balances = self._collect_balances()
		alts_value_usdt = 0.0
		btceth_value_usdc = 0.0
		free_usdt = float(balances.get('USDT', {}).get('free', 0.0))
		free_usdc = float(balances.get('USDC', {}).get('free', 0.0))

		usdc_usdt = self._get_usdc_usdt_price()

		btc_qty = balances.get('BTC', {}).get('total', 0.0)
		eth_qty = balances.get('ETH', {}).get('total', 0.0)
		if btc_qty > 0:
			btc_px_usdc = self._get_price('BTCUSDC')
			btceth_value_usdc += btc_qty * btc_px_usdc
		if eth_qty > 0:
			eth_px_usdc = self._get_price('ETHUSDC')
			btceth_value_usdc += eth_qty * eth_px_usdc

		for asset, data in balances.items():
			if asset in self.keep_assets:
				continue
			total_qty = float(data.get('total', 0.0))
			if total_qty <= 0:
				continue
			symbol_usdt = f"{asset}USDT"
			symbol_usdc = f"{asset}USDC"
			price_usdt = self._get_price(symbol_usdt)
			if price_usdt > 0:
				alts_value_usdt += total_qty * price_usdt
				continue
			price_usdc = self._get_price(symbol_usdc)
			if price_usdc > 0:
				alts_value_usdt += total_qty * price_usdc * usdc_usdt

		return alts_value_usdt, btceth_value_usdc, free_usdt, free_usdc

	def _convert_usdt_to_usdc(self, usdt_amount: float) -> Dict:
		if usdt_amount <= 0:
			return {'success': False, 'reason': 'zero_amount'}
		price = self._get_usdc_usdt_price()
		rules = self._get_symbol_rules('USDCUSDT')
		step = float(rules.get('stepSize', 1e-6) or 1e-6)
		usdc_qty = self._round_to_step(usdt_amount / price, step)
		if usdc_qty <= 0:
			return {'success': False, 'reason': 'qty_too_small'}
		order = self.mex.place_order(symbol='USDCUSDT', side='BUY', quantity=usdc_qty, price=price)
		return {'success': bool(order and 'orderId' in order), 'order': order, 'side': 'BUY', 'symbol': 'USDCUSDT', 'qty': usdc_qty, 'price': price}

	def _convert_usdc_to_usdt(self, usdc_amount: float) -> Dict:
		if usdc_amount <= 0:
			return {'success': False, 'reason': 'zero_amount'}
		price = self._get_usdc_usdt_price()
		rules = self._get_symbol_rules('USDCUSDT')
		step = float(rules.get('stepSize', 1e-6) or 1e-6)
		usdc_qty = self._round_to_step(usdc_amount, step)
		if usdc_qty <= 0:
			return {'success': False, 'reason': 'qty_too_small'}
		order = self.mex.place_order(symbol='USDCUSDT', side='SELL', quantity=usdc_qty, price=price)
		return {'success': bool(order and 'orderId' in order), 'order': order, 'side': 'SELL', 'symbol': 'USDCUSDT', 'qty': usdc_qty, 'price': price}

	def rebalance_on_freed_funds(self) -> Dict:
		"""Основная точка входа. Делает один шаг в сторону 50/50 только свободными средствами."""
		try:
			alts_value_usdt, btceth_value_usdc, free_usdt, free_usdc = self._compute_portfolios_value()
			usdc_usdt = self._get_usdc_usdt_price()
			btceth_value_usdt = btceth_value_usdc * usdc_usdt

			total_usd = alts_value_usdt + btceth_value_usdt
			if total_usd <= 0:
				return {'success': False, 'action': 'noop', 'reason': 'zero_portfolio'}

			target_each = total_usd / 2.0

			if alts_value_usdt > target_each:
				over_usdt = alts_value_usdt - target_each
				amount_to_convert_usdt = min(free_usdt, over_usdt)
				if amount_to_convert_usdt > 0:
					logger.info(f"⚖️ Конвертация USDT→USDC на ${amount_to_convert_usdt:.2f} для выравнивания к 50/50")
					result = self._convert_usdt_to_usdc(amount_to_convert_usdt)
					if result.get('success'):
						order = result.get('order', {}) or {}
						msg = (
							"⚖️ <b>Балансировка 50/50</b>\n\n"
							f"Действие: USDT → USDC (BUY)\n"
							f"Сумма: ${amount_to_convert_usdt:.2f} ≈ {result.get('qty', 0):.6f} USDC @ {result.get('price', usdc_usdt):.6f}\n"
							f"Портфель: Альты=${alts_value_usdt:.2f} | BTC/ETH=${btceth_value_usdt:.2f} | Цель на сторону=${target_each:.2f}\n"
							f"Свободные: USDT=${free_usdt:.2f} | USDC=${free_usdc:.2f}\n"
							f"Ордер: <code>{order.get('orderId', 'n/a')}</code>"
						)
						self._send_telegram_message(msg)
					return result
				msg = (
					"⚖️ <b>Балансировка 50/50</b>\n\n"
					f"Нет свободного USDT для выравнивания\n"
					f"Портфель: Альты=${alts_value_usdt:.2f} | BTC/ETH=${btceth_value_usdt:.2f} | Цель на сторону=${target_each:.2f}\n"
					f"Свободные: USDT=${free_usdt:.2f} | USDC=${free_usdc:.2f}"
				)
				self._send_telegram_message(msg)
				return {'success': False, 'action': 'noop', 'reason': 'no_free_usdt'}

			if btceth_value_usdt > target_each:
				over_usdt_equiv = btceth_value_usdt - target_each
				usdc_needed = over_usdt_equiv / usdc_usdt
				amount_to_convert_usdc = min(free_usdc, usdc_needed)
				if amount_to_convert_usdc > 0:
					logger.info(f"⚖️ Конвертация USDC→USDT на {amount_to_convert_usdc:.6f} для выравнивания к 50/50")
					result = self._convert_usdc_to_usdt(amount_to_convert_usdc)
					if result.get('success'):
						order = result.get('order', {}) or {}
						msg = (
							"⚖️ <b>Балансировка 50/50</b>\n\n"
							f"Действие: USDC → USDT (SELL)\n"
							f"Количество: {result.get('qty', 0):.6f} USDC @ {result.get('price', usdc_usdt):.6f}\n"
							f"Портфель: Альты=${alts_value_usdt:.2f} | BTC/ETH=${btceth_value_usdt:.2f} | Цель на сторону=${target_each:.2f}\n"
							f"Свободные: USDT=${free_usdt:.2f} | USDC=${free_usdc:.2f}\n"
							f"Ордер: <code>{order.get('orderId', 'n/a')}</code>"
						)
						self._send_telegram_message(msg)
					return result
				msg = (
					"⚖️ <b>Балансировка 50/50</b>\n\n"
					f"Нет свободного USDC для выравнивания\n"
					f"Портфель: Альты=${alts_value_usdt:.2f} | BTC/ETH=${btceth_value_usdt:.2f} | Цель на сторону=${target_each:.2f}\n"
					f"Свободные: USDT=${free_usdt:.2f} | USDC=${free_usdc:.2f}"
				)
				self._send_telegram_message(msg)
				return {'success': False, 'action': 'noop', 'reason': 'no_free_usdc'}

			msg = (
				"⚖️ <b>Балансировка 50/50</b>\n\n"
				f"Уже сбалансировано (50/50)\n"
				f"Портфель: Альты=${alts_value_usdt:.2f} | BTC/ETH=${btceth_value_usdt:.2f} | Цель на сторону=${target_each:.2f}\n"
				f"Свободные: USDT=${free_usdt:.2f} | USDC=${free_usdc:.2f}"
			)
			self._send_telegram_message(msg)
			return {'success': True, 'action': 'balanced', 'reason': 'already_50_50'}
		except Exception as e:
			logger.error(f"Ошибка балансировки 50/50: {e}")
			return {'success': False, 'action': 'error', 'reason': str(e)} 