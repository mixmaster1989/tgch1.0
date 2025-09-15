#!/usr/bin/env python3
"""
Продажа всего баланса базового актива по указанной паре (например, PAXGUSDT) через MexAPI.
Использует маркет-ордер SELL.
"""

import argparse
import sys
import math
from typing import Optional, Dict, Any

from mex_api import MexAPI

try:
	from mexc_advanced_api import MexAdvancedAPI  # необязателен
except Exception:  # noqa: E722 — модуль опционален
	MexAdvancedAPI = None  # type: ignore


def get_symbol_rules(symbol: str) -> Dict[str, Any]:
	"""Попробовать получить правила символа через MexAdvancedAPI (если доступен)."""
	if MexAdvancedAPI is None:
		return {}
	try:
		adv = MexAdvancedAPI()
		return adv.get_symbol_rules(symbol) or {}
	except Exception:
		return {}


def floor_to_precision(value: float, decimals: int) -> float:
	"""Округление вниз до нужного количества знаков после запятой."""
	if decimals <= 0:
		return math.floor(value)
	factor = 10 ** decimals
	return math.floor(value * factor) / factor


def floor_to_step(value: float, step: float) -> float:
	"""Округление вниз к ближайшему шагу (step)."""
	if step and step > 0:
		return math.floor(value / step) * step
	return value


def compute_sell_quantity(free_qty: float, rules: Dict[str, Any]) -> float:
	"""Посчитать максимально возможное количество для продажи с учетом правил биржи.
	- Для SELL используем округление вниз, чтобы избежать 'insufficient balance'.
	- Если free < minQty, возвращаем 0 (нельзя выполнить ордер).
	"""
	quantity_precision = int(rules.get('quantityPrecision', 8))
	step_size = float(rules.get('stepSize', 0) or 0)
	min_qty = float(rules.get('minQty', 0) or 0)

	# Оставим малую «пылинку» для избежания ошибок с балансом
	raw = max(0.0, free_qty * 0.999)

	# Если есть минимальное количество, проверяем достижимость
	if min_qty > 0 and raw < min_qty:
		return 0.0

	q = raw
	# Применяем точность (вниз)
	q = floor_to_precision(q, quantity_precision)
	# Применяем шаг (вниз)
	q = floor_to_step(q, step_size)

	# Повторная проверка minQty
	if min_qty > 0 and q < min_qty:
		return 0.0
	return max(0.0, q)


def get_base_asset_from_symbol(symbol: str) -> Optional[str]:
	"""Вернуть базовый актив для пары с USDT, иначе None."""
	s = symbol.upper().strip()
	if s.endswith('USDT') and len(s) > 4:
		return s[:-4]
	return None


def try_place_with_scales(api: MexAPI, symbol: str, base_qty: float, preferred_decimals: Optional[int] = None) -> Dict[str, Any]:
	"""Пробуем разместить ордер, подбирая допустимое число знаков после запятой.
	Возвращает ответ API (успех или последнюю ошибку).
	"""
	# Формируем список вариантов масштаба
	decimals_options = []
	if isinstance(preferred_decimals, int) and 0 <= preferred_decimals <= 10:
		decimals_options.append(preferred_decimals)
	# Добавляем распространённые масштабы
	for d in [0,1,2,3,4,5,6,7,8]:
		if d not in decimals_options:
			decimals_options.append(d)

	last_error: Dict[str, Any] = {'error': 'NO_ATTEMPT'}
	for d in decimals_options:
		q = floor_to_precision(base_qty, d)
		if q <= 0:
			continue
		try:
			resp = api.place_order(symbol=symbol, side='SELL', quantity=q, price=None)
			# Если биржа вернула orderId — успех
			if isinstance(resp, dict) and 'orderId' in resp:
				return resp
			# Если вернулась структурированная ошибка — анализируем
			msg = ''
			if isinstance(resp, dict):
				msg = str(resp.get('message', '')).lower()
			last_error = resp
			if 'quantity scale is invalid' in msg:
				continue
			# Иная ошибка — прекращаем перебор
			return resp
		except Exception as e:
			text = str(e).lower()
			last_error = {'error': 'EXCEPTION', 'message': str(e)}
			if 'quantity scale is invalid' in text:
				continue
			return last_error
	# Если все попытки не удались, возвращаем последнюю ошибку
	return last_error


def main() -> int:
	parser = argparse.ArgumentParser(description='Продать весь баланс базового актива по паре (маркет SELL)')
	parser.add_argument('symbol', nargs='?', default='PAXGUSDT', help='Символ в формате XXXUSDT (по умолчанию PAXGUSDT)')
	parser.add_argument('--yes', action='store_true', help='Подтвердить выполнение без дополнительных вопросов')
	args = parser.parse_args()

	symbol = args.symbol.upper()
	base_asset = get_base_asset_from_symbol(symbol)
	if base_asset is None:
		print(f"❌ Неподдерживаемый символ: {symbol}. Ожидался формат XXXUSDT.")
		return 2

	api = MexAPI()

	# Получаем баланс аккаунта
	try:
		info = api.get_account_info()
	except Exception as e:
		print(f"❌ Ошибка получения аккаунта: {e}")
		return 3

	free_qty = 0.0
	for b in info.get('balances', []):
		if b.get('asset') == base_asset:
			try:
				free_qty = float(b.get('free', 0))
			except Exception:
				free_qty = 0.0
			break

	if free_qty <= 0:
		print(f"ℹ️ Свободный баланс {base_asset} отсутствует. Нечего продавать.")
		return 0

	rules = get_symbol_rules(symbol)
	qty = compute_sell_quantity(free_qty, rules)
	if qty <= 0:
		print(f"❌ Недостаточный свободный баланс {base_asset} для минимального ордера.")
		return 4

	if not args.yes:
		print(f"Вы собираетесь продать {qty} {base_asset} маркет-ордером по паре {symbol}.")
		print("Добавьте флаг --yes для подтверждения.")
		return 1

	# Размещаем маркет SELL с подбором масштаба количества
	try:
		preferred_dec = int(rules.get('quantityPrecision')) if 'quantityPrecision' in rules else None
	except Exception:
		preferred_dec = None

	resp = try_place_with_scales(api, symbol, qty, preferred_decimals=preferred_dec)
	if isinstance(resp, dict) and 'orderId' in resp:
		print("✅ Продажа выполнена успешно:")
		print(resp)
		return 0
	else:
		print("❌ Ошибка размещения ордера:")
		print(resp)
		return 5


if __name__ == '__main__':
	sys.exit(main()) 