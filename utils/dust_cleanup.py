#!/usr/bin/env python3
"""
Очистка пылинок: докупить до минимального объёма и продать весь остаток в USDT
- Для каждого актива с ненулевым free:
  - Строим пару SYMBOLUSDT
  - Если текущий нотионал < minNotional (или 1 USDT по умолчанию), докупаем недостающее
  - Затем продаём весь объём маркетом
- Ограничение: максимум 2 USDT на докупку на один символ (safety)
"""

import time
from typing import Dict, Optional

from mex_api import MexAPI
from mexc_advanced_api import MexAdvancedAPI

SAFETY_TOPUP_USDT_LIMIT = 4.0  # максимальная докупка на символ


def get_rules(adv: MexAdvancedAPI, symbol: str) -> Dict:
    """Попробовать получить правила. Если LOT_SIZE отсутствует, взять baseSizePrecision как step."""
    rules: Dict = {}
    try:
        rules = adv.get_symbol_rules(symbol) or {}
    except Exception:
        rules = {}

    # Если нет stepSize/minQty — пробуем достать из exchangeInfo v3
    if not rules or float(rules.get('stepSize', 0) or 0) == 0:
        try:
            mex = MexAPI()
            ex = mex.get_exchange_info()
            for s in (ex.get('symbols') or []):
                if s.get('symbol') == symbol:
                    # baseSizePrecision в v3 как строка шага, например "0.1"
                    base_size_prec = s.get('baseSizePrecision')
                    if isinstance(base_size_prec, str):
                        try:
                            step = float(base_size_prec)
                            if step > 0:
                                rules.setdefault('quantityPrecision', 8)
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


def round_down(value: float, decimals: int) -> float:
	if decimals <= 0:
		return float(int(value))
	factor = 10 ** decimals
	return int(value * factor) / factor


def apply_step(value: float, step: float) -> float:
	if step and step > 0:
		return (int(value / step)) * step
	return value


def compute_sell_qty(free_qty: float, rules: Dict) -> float:
	qty_prec = int(rules.get('quantityPrecision', 8) or 8)
	step = float(rules.get('stepSize', 0) or 0)
	q = max(0.0, free_qty * 0.999)
	q = round_down(q, qty_prec)
	q = apply_step(q, step)
	return max(0.0, q)


def main():
	api = MexAPI()
	adv = MexAdvancedAPI()

	info = api.get_account_info()
	balances = info.get('balances', []) if isinstance(info, dict) else []
	if not balances:
		print('❌ Не получены балансы')
		return

	print('🔍 Поиск пылинок для очистки...')

	for b in balances:
		asset = b.get('asset')
		try:
			free = float(b.get('free', 0))
		except Exception:
			free = 0.0
		if not asset or free <= 0:
			continue
		if asset == 'USDT':
			continue

		symbol = f"{asset}USDT"
		rules = get_rules(adv, symbol)
		min_notional = float(rules.get('minNotional', 1.0) or 1.0)
		qty_prec = int(rules.get('quantityPrecision', 8) or 8)
		step = float(rules.get('stepSize', 0) or 0)

		price = get_price(api, symbol)
		if not price or price <= 0:
			print(f"{symbol}: пропуск — нет цены")
			continue

		notional = free * price
		need_topup_usdt = max(0.0, min_notional - notional)

		# Если уже >= minNotional — просто продаём
		if need_topup_usdt <= 0.0:
			sell_qty = compute_sell_qty(free, rules)
			if sell_qty <= 0:
				print(f"{symbol}: пропуск — нечего продавать после округления")
				continue
			resp = api.place_market_order(symbol=symbol, side='SELL', quantity=sell_qty)
			print(f"{symbol}: SELL {sell_qty} -> {resp}")
			time.sleep(0.2)
			continue

		# Нужна докупка, но ограничим верхним лимитом
		if need_topup_usdt > SAFETY_TOPUP_USDT_LIMIT:
			print(f"{symbol}: пропуск — требуется докупить {need_topup_usdt:.2f} USDT (> {SAFETY_TOPUP_USDT_LIMIT} USDT)")
			continue

		# Рассчитываем количество для докупки
		topup_qty = need_topup_usdt / price
		topup_qty = round_down(topup_qty, qty_prec)
		topup_qty = apply_step(topup_qty, step)
		if topup_qty <= 0:
			# минимально возможная докупка по шагу
			min_step_qty = step if step > 0 else (10 ** -qty_prec)
			topup_qty = min_step_qty
		
		print(f"{symbol}: докупка ~{need_topup_usdt:.4f} USDT ({topup_qty} {asset}) для достижения minNotional {min_notional}")
		buy_resp = api.place_market_order(symbol=symbol, side='BUY', quantity=topup_qty)
		print(f"{symbol}: BUY {topup_qty} -> {buy_resp}")
		time.sleep(0.4)

		# Повторно читаем баланс и продаём весь объём
		info2 = api.get_account_info()
		new_free = free
		for bb in info2.get('balances', []):
			if bb.get('asset') == asset:
				try:
					new_free = float(bb.get('free', 0))
				except Exception:
					new_free = new_free
				break
		sell_qty = compute_sell_qty(new_free, rules)
		if sell_qty <= 0:
			print(f"{symbol}: после докупки нечего продавать (sell_qty=0)")
			continue
		sell_resp = api.place_market_order(symbol=symbol, side='SELL', quantity=sell_qty)
		print(f"{symbol}: SELL {sell_qty} -> {sell_resp}")
		time.sleep(0.4)

	print('✅ Очистка пылинок завершена')


if __name__ == '__main__':
	main()
