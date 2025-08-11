#!/usr/bin/env python3
"""
Portfolio Cleanup and Rotation
- Compute real PnL (AvgCost) per held asset
- Place LIMIT sell orders for all assets except BTC/ETH into USDT at price > average buy price
- Buy a new portfolio of top-5 alts equally with available USDT

Safety:
- Respects minQty/stepSize/pricePrecision/minNotional
- Skips assets without USDT market (tries USDC fallback)
- Skips orders below min notional

Assumptions:
- Top-5 alts after ETH by significance: BNB, SOL, XRP, ADA, DOGE
"""

import math
import time
from decimal import Decimal, ROUND_DOWN, ROUND_UP
from typing import Dict, List, Optional, Tuple

from mex_api import MexAPI
from mexc_advanced_api import MexAdvancedAPI


def _round_to_step(value: float, step: float, mode: str = 'down') -> float:
    if step <= 0:
        return value
    d_value = Decimal(str(value))
    d_step = Decimal(str(step))
    quant = (d_value / d_step).to_integral_exact(rounding=(ROUND_DOWN if mode == 'down' else ROUND_UP))
    return float((quant * d_step).normalize())


def _round_price(price: float, tick_size: float, mode: str = 'up') -> float:
    return _round_to_step(price, tick_size, mode=mode)


def _compute_avg_cost_from_trades(trades: List[Dict], base_asset: str, quote_asset: str) -> Tuple[float, float, float]:
    position_qty = 0.0
    cost_basis_total = 0.0
    realized_pnl = 0.0

    def fee_in_quote(trade: Dict) -> float:
        fee = float(trade.get('commission', 0) or 0)
        fee_asset = trade.get('commissionAsset')
        price = float(trade.get('price', 0) or 0)
        if fee <= 0:
            return 0.0
        if fee_asset == quote_asset:
            return fee
        if fee_asset == base_asset and price > 0:
            return fee * price
        return 0.0

    trades_sorted = sorted(trades, key=lambda t: t.get('time', 0))
    for t in trades_sorted:
        qty = float(t.get('qty', 0) or 0)
        price = float(t.get('price', 0) or 0)
        quote_qty = float(t.get('quoteQty', 0) or 0)
        is_buyer = bool(t.get('isBuyer', False))
        fee_q = fee_in_quote(t)

        if is_buyer:
            total_cost = quote_qty + fee_q
            new_pos = position_qty + qty
            if new_pos > 0:
                cost_basis_total += total_cost
                position_qty = new_pos
        else:
            if position_qty <= 0:
                continue
            avg_price = cost_basis_total / position_qty if position_qty > 0 else 0.0
            revenue = quote_qty - fee_q
            realized_pnl += revenue - (avg_price * qty)
            cost_basis_total -= avg_price * qty
            position_qty -= qty
            if position_qty < 1e-12:
                position_qty = 0.0
                cost_basis_total = 0.0

    avg_buy_price = (cost_basis_total / position_qty) if position_qty > 0 else 0.0
    return avg_buy_price, position_qty, realized_pnl


def _detect_symbol_for_asset(api_adv: MexAdvancedAPI, asset: str) -> Optional[Tuple[str, str, str]]:
    # Prefer USDT, fallback USDC
    for quote in ('USDT', 'USDC'):
        symbol = f"{asset}{quote}"
        rules = api_adv.get_symbol_rules(symbol)
        if rules:
            return symbol, asset, quote
    return None


def _get_best_bid_ask(api: MexAPI, symbol: str) -> Tuple[Optional[float], Optional[float]]:
    try:
        depth = api.get_depth(symbol, limit=5)
        bids = depth.get('bids', [])
        asks = depth.get('asks', [])
        best_bid = float(bids[0][0]) if bids else None
        best_ask = float(asks[0][0]) if asks else None
        return best_bid, best_ask
    except Exception:
        return None, None


def analyze_portfolio_and_prepare_orders(dry_run: bool = True) -> Dict:
    mex = MexAPI()
    adv = MexAdvancedAPI()

    account = mex.get_account_info()
    balances = account.get('balances', [])

    # Whitelist to keep
    keep_assets = {'BTC', 'ETH', 'USDT', 'USDC'}

    report = {
        'sell_plan': [],
        'buy_plan': [],
        'pnl': {},
        'errors': []
    }

    # Build list of unwanted assets
    active = [b for b in balances if float(b.get('free', 0)) + float(b.get('locked', 0)) > 0]
    for b in active:
        asset = b['asset']
        if asset in keep_assets:
            continue
        total_qty = float(b['free']) + float(b['locked'])
        # Detect symbol & rules
        sym_info = _detect_symbol_for_asset(adv, asset)
        if not sym_info:
            report['errors'].append(f"No USDT/USDC market for {asset}")
            continue
        symbol, base, quote = sym_info
        rules = adv.get_symbol_rules(symbol)
        price_precision = rules.get('pricePrecision', 8)
        qty_precision = rules.get('quantityPrecision', 8)
        tick_size = float(rules.get('tickSize', 10 ** -price_precision))
        step_size = float(rules.get('stepSize', 10 ** -qty_precision))
        min_qty = float(rules.get('minQty', step_size))
        min_notional = float(rules.get('minNotional', 5.0))

        # Trades for AvgCost
        trades = adv.get_my_trades(symbol, limit=500)
        avg_buy_price, position_qty, realized_pnl = _compute_avg_cost_from_trades(trades, base, quote)

        # Current price
        price_info = mex.get_ticker_price(symbol)
        current_price = float(price_info['price']) if 'price' in price_info else 0.0

        # Unrealized PnL only for the portion we actually hold
        qty_for_pnl = min(total_qty, position_qty) if position_qty > 0 else 0.0
        unreal_pnl = (current_price - avg_buy_price) * qty_for_pnl
        total_pnl = realized_pnl + unreal_pnl
        report['pnl'][asset] = {
            'symbol': symbol,
            'avg_buy_price': avg_buy_price,
            'position_qty': position_qty,
            'portfolio_qty': total_qty,
            'current_price': current_price,
            'realized_pnl': realized_pnl,
            'unrealized_pnl': unreal_pnl,
            'total_pnl': total_pnl
        }

        # Prepare limit sell order above avg buy price
        if total_qty <= 0 or avg_buy_price <= 0:
            continue

        # Price strictly above average buy price; also not below best ask
        best_bid, best_ask = _get_best_bid_ask(mex, symbol)
        target_price = max(avg_buy_price * 1.005, (best_ask or current_price))  # +0.5%
        target_price = float(Decimal(str(target_price)).quantize(Decimal(str(tick_size)), rounding=ROUND_UP))

        # Quantity: use free amount only
        free_qty = float(b['free'])
        order_qty = _round_to_step(free_qty, step_size, mode='down')
        if order_qty < min_qty:
            continue
        notional = order_qty * target_price
        if notional < min_notional:
            continue

        report['sell_plan'].append({
            'action': 'SELL',
            'symbol': symbol,
            'asset': asset,
            'quantity': order_qty,
            'price': target_price,
            'avg_buy_price': avg_buy_price,
            'min_notional': min_notional
        })

    # Compute available USDT for buys
    usdt_free = 0.0
    for b in active:
        if b['asset'] == 'USDT':
            usdt_free = float(b['free'])
            break

    # Target top-5 alts (by significance, after ETH)
    target_alts = ['BNB', 'SOL', 'XRP', 'ADA', 'DOGE']

    if usdt_free > 0:
        per_asset_usdt = usdt_free / len(target_alts)
        for alt in target_alts:
            # Skip if already held (optional)
            # Detect market
            sym_info = _detect_symbol_for_asset(adv, alt)
            if not sym_info:
                report['errors'].append(f"No USDT/USDC market for target {alt}")
                continue
            symbol, base, quote = sym_info
            if quote != 'USDT':
                # Require USDT per requirement; skip non-USDT
                continue
            rules = adv.get_symbol_rules(symbol)
            price_precision = rules.get('pricePrecision', 8)
            qty_precision = rules.get('quantityPrecision', 8)
            tick_size = float(rules.get('tickSize', 10 ** -price_precision))
            step_size = float(rules.get('stepSize', 10 ** -qty_precision))
            min_qty = float(rules.get('minQty', step_size))
            min_notional = float(rules.get('minNotional', 5.0))

            best_bid, best_ask = _get_best_bid_ask(mex, symbol)
            ref_price = best_ask or (mex.get_ticker_price(symbol).get('price') and float(mex.get_ticker_price(symbol)['price'])) or 0.0
            if ref_price <= 0:
                continue
            # Place an aggressive limit buy slightly above best ask to ensure fill
            buy_price = float(Decimal(str(ref_price * 1.001)).quantize(Decimal(str(tick_size)), rounding=ROUND_UP))
            qty = per_asset_usdt / buy_price
            qty = _round_to_step(qty, step_size, mode='down')
            if qty < min_qty:
                continue
            notional = qty * buy_price
            if notional < min_notional:
                continue

            report['buy_plan'].append({
                'action': 'BUY',
                'symbol': symbol,
                'asset': alt,
                'quantity': qty,
                'price': buy_price,
                'per_asset_usdt': per_asset_usdt
            })

    # Execute if not dry-run
    if not dry_run:
        for sell in report['sell_plan']:
            mex.place_order(symbol=sell['symbol'], side='SELL', quantity=sell['quantity'], price=sell['price'])
            time.sleep(0.3)
        for buy in report['buy_plan']:
            mex.place_order(symbol=buy['symbol'], side='BUY', quantity=buy['quantity'], price=buy['price'])
            time.sleep(0.3)

    return report


if __name__ == '__main__':
    plan = analyze_portfolio_and_prepare_orders(dry_run=True)
    from pprint import pprint
    pprint(plan) 