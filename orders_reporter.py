#!/usr/bin/env python3
"""
Orders Reporter
- Собирает последние 10 FILLED ордеров (BUY/SELL) по всему аккаунту
- Для SELL-ордеров считает приблизительный реализованный PnL по сделкам
- Раз в 10 минут отправляет отчет в Telegram
"""

import time
import logging
from datetime import datetime
from typing import Dict, List

from mex_api import MexAPI
from mexc_advanced_api import MexAdvancedAPI
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
import requests

logger = logging.getLogger(__name__)


class OrdersReporter:
	def __init__(self):
		self.mex_api = MexAPI()
		self.mex_adv = MexAdvancedAPI()
		self.bot_token = TELEGRAM_BOT_TOKEN
		self.chat_id = TELEGRAM_CHAT_ID
		self.report_interval_sec = 600  # 10 минут

	def _send_telegram(self, message: str):
		if not self.bot_token or not self.chat_id:
			return
		try:
			url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
			requests.post(url, data={'chat_id': self.chat_id, 'text': message, 'parse_mode': 'HTML'})
		except Exception:
			pass

	def _get_candidate_symbols(self) -> List[str]:
		"""Сформировать список символов для опроса ордеров на основе балансов и основных пар."""
		try:
			info = self.mex_api.get_account_info() or {}
			assets: List[str] = []
			for b in info.get('balances', []) or []:
				asset = b.get('asset')
				total = float(b.get('free', 0) or 0) + float(b.get('locked', 0) or 0)
				if total > 0 and asset not in {'USDT','USDC'}:
					assets.append(asset)
			# Формируем символы USDT/USDC
			symbols: List[str] = []
			for a in assets:
				for quote in ('USDT','USDC'):
					sym = f"{a}{quote}"
					# проверим, есть ли правила (символ существует)
					try:
						rules = self.mex_adv.get_symbol_rules(sym)
						if rules:
							symbols.append(sym)
					except Exception:
						continue
			# Добавим ключевые пары на всякий случай
			for s in ('BTCUSDT','ETHUSDT','BTCUSDC','ETHUSDC'):
				if s not in symbols:
					try:
						rules = self.mex_adv.get_symbol_rules(s)
						if rules:
							symbols.append(s)
					except Exception:
						pass
			# Ограничим до разумного количества
			return symbols[:40]
		except Exception:
			return []

	def _get_recent_orders(self, limit: int = 10) -> List[Dict]:
		try:
			symbols = self._get_candidate_symbols()
			all_orders: List[Dict] = []
			for sym in symbols:
				try:
					partial = self.mex_api.get_order_history(symbol=sym, limit=50)
					if isinstance(partial, list):
						for o in partial:
							o['symbol'] = sym  # убеждаемся, что символ есть
						all_orders.extend(partial)
				except Exception:
					continue
			# Фильтруем по статусу
			filled = [o for o in all_orders if str(o.get('status','')).upper() in {'FILLED','PARTIALLY_FILLED'}]
			# Сортируем по времени (updateTime / time)
			def _ot(o: Dict):
				return o.get('updateTime') or o.get('time') or 0
			filled.sort(key=_ot, reverse=True)
			return filled[:limit]
		except Exception as e:
			logger.error(f"Ошибка получения ордеров: {e}")
			return []

	def _compute_sell_order_realized_pnl(self, symbol: str, order_id: int) -> float:
		"""Реализованный PnL для SELL-ордера по сделкам: revenue - cost_basis на проданное количество.
		Сканируем сделки по символу, считаем среднюю стоимость и в момент сделок данного orderId считаем доход.
		"""
		try:
			trades = self.mex_adv.get_my_trades(symbol, limit=1000) or []
			trades = sorted(trades, key=lambda x: x.get('time', 0))
			position_qty = 0.0
			cost_basis_total = 0.0
			realized = 0.0
			for t in trades:
				qty = float(t.get('qty') or 0)
				quote_qty = float(t.get('quoteQty') or 0)
				is_buyer = bool(t.get('isBuyer'))
				# комиссия в котируемой валюте
				fee = float(t.get('commission') or 0)
				fa = t.get('commissionAsset')
				price = float(t.get('price') or 0)
				fee_q = fee if fa and fa.upper().endswith('USDT') else (fee * price if fa and not fa.upper().endswith('USDT') else 0.0)
				if is_buyer:
					total_cost = quote_qty + fee_q
					new_pos = position_qty + qty
					if new_pos > 0:
						cost_basis_total += total_cost
						position_qty = new_pos
				else:
					if position_qty <= 0:
						continue
					avg = cost_basis_total/position_qty if position_qty>0 else 0.0
					revenue = quote_qty - fee_q
					# засчитываем realized только для ордера с orderId
					if str(t.get('orderId')) == str(order_id):
						realized += revenue - (avg * qty)
					# обновляем позицию и базу
					cost_basis_total -= avg * qty
					position_qty -= qty
					if position_qty < 1e-12:
						position_qty = 0.0
						cost_basis_total = 0.0
			return realized
		except Exception as e:
			logger.error(f"Ошибка расчета PnL для ордера {order_id} {symbol}: {e}")
			return 0.0

	def build_report(self) -> str:
		orders = self._get_recent_orders(limit=10)
		if not orders:
			return (
				f"🧾 <b>ОРДЕРА (последние 10)</b>\n"
				f"⏰ {datetime.now().strftime('%H:%M:%S')}\n"
				f"🚫 Нет данных"
			)
		lines = [
			"🧾 <b>ОРДЕРА (последние 10)</b>\n",
			f"⏰ {datetime.now().strftime('%H:%M:%S')}\n\n"
		]
		total_realized = 0.0
		for i, o in enumerate(orders, 1):
			symbol = o.get('symbol')
			side = (o.get('side') or '').upper()
			status = (o.get('status') or '').upper()
			order_id = o.get('orderId')
			price = float(o.get('price') or 0)
			avg_price = float(o.get('avgPrice') or o.get('price') or 0)
			qty = float(o.get('executedQty') or o.get('origQty') or 0)
			# если есть cumulativeAmount/avgPrice в иных форматах
			if avg_price <= 0 and o.get('cumulativeAmount') and o.get('cumulativeQuantity'):
				try:
					cum_amt = float(o.get('cumulativeAmount'))
					cum_qty = float(o.get('cumulativeQuantity'))
					avg_price = cum_amt / cum_qty if cum_qty > 0 else avg_price
				except Exception:
					pass
			pnl_text = ""
			if side == 'SELL' and status in {'FILLED','PARTIALLY_FILLED'} and qty > 0:
				realized = self._compute_sell_order_realized_pnl(symbol, order_id)
				total_realized += realized
				pnl_text = f"\n   💵 PnL: <code>${realized:.4f}</code>"
			lines.append(
				f"{i}. <b>{symbol}</b> / {side}\n"
				f"   🆔 {order_id}\n"
				f"   📊 Qty: {qty:.6f}\n"
				f"   💵 Price(avg): ${avg_price:.6f}{pnl_text}\n\n"
			)
		if total_realized != 0.0:
			lines.append(f"🏁 <b>ИТОГО PnL (SELL)</b>: <code>${total_realized:.4f}</code>")
		return "".join(lines)

	def start(self):
		logger.info("🚀 Запуск OrdersReporter")
		while True:
			try:
				message = self.build_report()
				self._send_telegram(message)
			except Exception as e:
				logger.error(f"Ошибка отправки отчета по ордерам: {e}")
			time.sleep(self.report_interval_sec) 