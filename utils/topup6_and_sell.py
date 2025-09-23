#!/usr/bin/env python3
"""
Докупка ~6 USDT и мгновенная продажа всего объёма для списка символов
Использует правила точности/шага из MexAdvancedAPI и exchangeInfo.
"""

import time
from typing import Dict, List, Optional

from mex_api import MexAPI
from mexc_advanced_api import MexAdvancedAPI

TARGET_TOPUP_USDT = 6.0


def round_down(value: float, decimals: int) -> float:
	if decimals <= 0:
		return float(int(value))
	factor = 10 ** decimals
	return int(value * factor) / factor


def apply_step(value: float, step: float) -> float:
	if step and step > 0:
		return (int(value / step)) * step
	return value


def get_rules(adv: MexAdvancedAPI, symbol: str) -> Dict:
	try:
		rules = adv.get_symbol_rules(symbol) or {}
	except Exception:
		rules = {}
	# дополняем из exchangeInfo baseSizePrecision
	if float(rules.get('stepSize', 0) or 0) == 0:
		try:
			mex = MexAPI()
			ex = mex.get_exchange_info()
			for s in (ex.get('symbols') or []):
				if s.get('symbol') == symbol:
					bsp = s.get('baseSizePrecision')
					if isinstance(bsp, str):
						try:
							step = float(bsp)
							if step > 0:
								rules['stepSize'] = step
						except Exception:
							pass
					break
		except Exception:
			pass
	return rules


def get_price(api: MexAPI, symbol: str) -> Optional[float]:
	data = api.get_ticker_price(symbol)
	try:
		if isinstance(data, dict) and 'price' in data:
			return float(data['price'])
	except Exception:
		return None
	return None


def place_with_scales(api: MexAPI, symbol: str, side: str, base_qty: float, preferred_decimals: Optional[int]) -> Dict:
	last_error: Dict = {'error': 'NO_ATTEMPT'}
	decimals_options: List[int] = []
	if isinstance(preferred_decimals, int) and 0 <= preferred_decimals <= 10:
		decimals_options.append(preferred_decimals)
	for d in [0,1,2,3,4,5,6,7,8]:
		if d not in decimals_options:
			decimals_options.append(d)
	for d in decimals_options:
		q = round_down(base_qty, d)
		if q <= 0:
			continue
		try:
			resp = api.place_order(symbol=symbol, side=side, quantity=q, price=None)
			if isinstance(resp, dict) and 'orderId' in resp:
				return resp
			err = ''
			if isinstance(resp, dict):
				err = str(resp.get('message', '')).lower()
			last_error = resp
			if 'quantity scale is invalid' in err:
				continue
			return resp
		except Exception as e:
			text = str(e).lower()
			last_error = {'error': 'EXCEPTION', 'message': str(e)}
			if 'quantity scale is invalid' in text:
				continue
			return last_error
	return last_error


def process_symbol(api: MexAPI, adv: MexAdvancedAPI, symbol: str) -> None:
	print(f"\n=== {symbol} ===")
	rules = get_rules(adv, symbol)
	qty_prec = int(rules.get('quantityPrecision', 8) or 8)
	step = float(rules.get('stepSize', 0) or 0)
	min_notional = float(rules.get('minNotional', 5.0) or 5.0)
	price = get_price(api, symbol)
	if not price or price <= 0:
		print('  ❌ Нет цены')
		return

	# Сначала покупаем на ~6 USDT
	buy_qty = TARGET_TOPUP_USDT / price
	buy_qty = apply_step(round_down(buy_qty, qty_prec), step)
	if buy_qty <= 0:
		# минимально допустимое по шагу
		buy_qty = step if step > 0 else (10 ** -qty_prec)

	print(f"  BUY ~{TARGET_TOPUP_USDT} USDT -> qty {buy_qty}")
	pref_dec = qty_prec
	buy_resp = place_with_scales(api, symbol, 'BUY', buy_qty, preferred_decimals=pref_dec)
	print(f"  BUY resp: {buy_resp}")
	if not (isinstance(buy_resp, dict) and 'orderId' in buy_resp):
		print('  ❌ Покупка не удалась, пропуск продажи')
		return
	time.sleep(0.5)

	# Узнаём текущий free и продаём весь объём
	info = api.get_account_info()
	base = symbol[:-4]
	free = 0.0
	for b in info.get('balances', []):
		if b.get('asset') == base:
			try:
				free = float(b.get('free', 0))
			except Exception:
				free = 0.0
			break
	sell_qty = apply_step(round_down(max(0.0, free * 0.999), qty_prec), step)
	if sell_qty <= 0:
		print('  ❌ Нечего продавать после покупки')
		return
	print(f"  SELL qty {sell_qty}")
	sell_resp = place_with_scales(api, symbol, 'SELL', sell_qty, preferred_decimals=pref_dec)
	print(f"  SELL resp: {sell_resp}")


def main():
	api = MexAPI()
	adv = MexAdvancedAPI()
	pairs = [
		'ACAUSDT', 'XLMUSDT', 'NOTUSDT', 'SAPIENUSDT', 'NEXOUSDT', 'DREYAIUSDT'
	]
	for sym in pairs:
		process_symbol(api, adv, sym)
		time.sleep(0.8)
	print('\n✅ Готово')


if __name__ == '__main__':
	main()

