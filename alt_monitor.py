#!/usr/bin/env python3
"""
Alts Monitor
- Monitors all non-BTC/ETH/USDT/USDC assets
- If unrealized PnL (AvgCost) > $0.15: place a near-market limit SELL to realize profit
- With available USDT >= $5: buy from top-5 alts equally (BNB, SOL, XRP, ADA, DOGE)
"""
import time
import logging
from datetime import datetime
from decimal import Decimal, ROUND_UP
from typing import Dict, List

from mex_api import MexAPI
from mexc_advanced_api import MexAdvancedAPI
from pnl_monitor import PnLMonitor
from anti_hype_filter import AntiHypeFilter
from post_sale_balancer import PostSaleBalancer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

TOP5_ALTS = ['BNB', 'SOL', 'XRP', 'ADA', 'DOGE']
SELL_THRESHOLD_USD = 0.15  # Снижено с 0.20 до 0.15
CHECK_INTERVAL_SEC = 60
NOTIFY_INTERVAL_SEC = 300

class AltsMonitor:
    def __init__(self):
        self.mex = MexAPI()
        self.adv = MexAdvancedAPI()
        self.anti_hype_filter = AntiHypeFilter()
        self.keep_assets = {'BTC', 'ETH', 'USDT', 'USDC'}
        self.last_action_time = 0
        self.last_notify_time = 0

    def _get_balances(self) -> Dict[str, Dict]:
        info = self.mex.get_account_info()
        result = {}
        for b in info.get('balances', []):
            total = float(b.get('free', 0)) + float(b.get('locked', 0))
            if total > 0:
                result[b['asset']] = {
                    'free': float(b['free']),
                    'locked': float(b['locked']),
                    'total': total,
                }
        return result

    def _get_best_bid_ask(self, symbol: str):
        try:
            depth = self.mex.get_depth(symbol, 5)
            bids = depth.get('bids', [])
            asks = depth.get('asks', [])
            best_bid = float(bids[0][0]) if bids else None
            best_ask = float(asks[0][0]) if asks else None
            return best_bid, best_ask
        except Exception:
            return None, None

    def _avg_cost_pnl(self, symbol: str, portfolio_qty: float) -> Dict:
        base = symbol.rstrip('USDT').rstrip('USDC').replace('USDT','').replace('USDC','')
        quote = 'USDT' if symbol.endswith('USDT') else ('USDC' if symbol.endswith('USDC') else 'USDT')
        trades = self.adv.get_my_trades(symbol, limit=500) or []

        position_qty = 0.0
        cost_basis_total = 0.0
        realized = 0.0

        def fee_in_quote(t):
            fee = float(t.get('commission', 0) or 0)
            fa = t.get('commissionAsset')
            price = float(t.get('price', 0) or 0)
            if fee <= 0:
                return 0.0
            if fa == quote:
                return fee
            if fa == base and price > 0:
                return fee * price
            return 0.0

        for t in sorted(trades, key=lambda x: x.get('time', 0)):
            qty = float(t.get('qty', 0) or 0)
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
                avg = cost_basis_total / position_qty if position_qty > 0 else 0.0
                revenue = quote_qty - fee_q
                realized += revenue - (avg * qty)
                cost_basis_total -= avg * qty
                position_qty -= qty
                if position_qty < 1e-12:
                    position_qty = 0.0
                    cost_basis_total = 0.0

        avg_price = (cost_basis_total / position_qty) if position_qty > 0 else 0.0
        px_info = self.mex.get_ticker_price(symbol)
        cur_px = float(px_info['price']) if 'price' in px_info else 0.0
        qty_for_pnl = min(portfolio_qty, position_qty) if position_qty > 0 else 0.0
        unreal = (cur_px - avg_price) * qty_for_pnl
        return {
            'avg_buy_price': avg_price,
            'current_price': cur_px,
            'position_qty': position_qty,
            'unrealized_pnl': unreal,
            'realized_pnl': realized,
        }

    def _place_limit_sell_near_market(self, symbol: str, quantity: float) -> Dict:
        best_bid, best_ask = self._get_best_bid_ask(symbol)
        price = best_bid * 0.999 if best_bid else None
        if price is None:
            px_info = self.mex.get_ticker_price(symbol)
            price = float(px_info['price']) * 0.999 if 'price' in px_info else None
        if price is None:
            return {'success': False, 'error': 'no_price'}
        return self.mex.place_order(symbol=symbol, side='SELL', quantity=quantity, price=price)

    def _place_limit_buy_near_market(self, symbol: str, usdt_amount: float) -> Dict:
        best_bid, best_ask = self._get_best_bid_ask(symbol)
        price = best_ask * 1.001 if best_ask else None
        if price is None:
            px_info = self.mex.get_ticker_price(symbol)
            price = float(px_info['price']) * 1.001 if 'price' in px_info else None
        if price is None or price <= 0:
            return {'success': False, 'error': 'no_price'}
        rules = self.adv.get_symbol_rules(symbol)
        step = float(rules.get('stepSize', 1e-6)) if rules else 1e-6
        qty = usdt_amount / price
        # round down to step
        from decimal import Decimal, ROUND_DOWN
        d_qty = Decimal(str(qty))
        d_step = Decimal(str(step))
        quant = (d_qty / d_step).to_integral_exact(rounding=ROUND_DOWN)
        qty = float((quant * d_step).normalize())
        if qty <= 0:
            return {'success': False, 'error': 'qty_too_small'}
        return self.mex.place_order(symbol=symbol, side='BUY', quantity=qty, price=price)

    def _fetch_open_orders_map(self, symbols: List[str]) -> Dict[str, list]:
        result: Dict[str, list] = {}
        for s in symbols:
            try:
                lst = self.mex.get_open_orders(s)
                result[s] = lst if isinstance(lst, list) else []
            except Exception:
                result[s] = []
        return result

    def _send_telegram_report(self, alt_items: List[Dict], orders_by_symbol: Dict[str, list]):
        if not alt_items:
            return
        
        # Получаем общую стоимость альтов
        total_alts_value = sum(it['quantity'] * it['current_price'] for it in alt_items)
        total_pnl = sum(it['pnl'] for it in alt_items)
        
        lines = [
            "🧩 <b>ПОРТФЕЛЬ АЛЬТОВ</b>\n",
            f"💰 Общая стоимость: ${total_alts_value:.2f}\n",
            f"📈 Общий PnL: ${total_pnl:.4f}\n\n"
        ]
        
        for it in alt_items:
            pnl_status = "📈" if it['pnl'] > 0 else "📉" if it['pnl'] < 0 else "➡️"
            to_sell = max(0.0, SELL_THRESHOLD_USD - it['pnl'])
            lines.append(
                f"{pnl_status} <b>{it['asset']}</b>:\n"
                f"   📊 {it['quantity']:.6f} @ ${it['current_price']:.4f}\n"
                f"   💵 PnL: ${it['pnl']:.4f} (порог: $0.20)\n"
                f"   📏 До продажи: ${to_sell:.4f}\n\n"
            )
        
        # Открытые ордера
        lines.append("📋 <b>ОРДЕРА:</b>\n")
        any_orders = False
        for s, lst in orders_by_symbol.items():
            if lst:
                any_orders = True
                lines.append(f"   ✅ {s}: {len(lst)}\n")
        if not any_orders:
            lines.append("   🚫 Нет открытых\n")
        
        lines.append(f"\n⏰ {datetime.now().strftime('%H:%M:%S')}")
        PnLMonitor().send_telegram_message("".join(lines))

    def run_once(self):
        balances = self._get_balances()
        # Collect ALT status first
        alt_items: List[Dict] = []
        alt_symbols: List[str] = []
        for asset, data in balances.items():
            if asset in self.keep_assets:
                continue
            symbol = f"{asset}USDT"
            rules = self.adv.get_symbol_rules(symbol)
            if not rules:
                symbol = f"{asset}USDC"
                rules = self.adv.get_symbol_rules(symbol)
            if not rules:
                continue
            pnl = self._avg_cost_pnl(symbol, data['total'])
            alt_items.append({
                'asset': asset,
                'symbol': symbol,
                'quantity': data['total'],
                'current_price': pnl['current_price'],
                'pnl': pnl['unrealized_pnl']
            })
            alt_symbols.append(symbol)
        # SELL phase
        for it in alt_items:
            if it['pnl'] > SELL_THRESHOLD_USD and balances[it['asset']]['free'] > 0:
                logger.info(f"Selling {it['asset']}: qty={balances[it['asset']]['free']}")
                res = self._place_limit_sell_near_market(it['symbol'], balances[it['asset']]['free'])
                logger.info(f"SELL result: {res}")
                
                # Немедленное уведомление о продаже
                if res and 'orderId' in res:
                    sell_message = (
                        f"<b>💰 ПРОДАЖА АЛЬТКОИНА</b>\n\n"
                        f"💱 Актив: {it['asset']}\n"
                        f"📊 Количество: {balances[it['asset']]['free']:.6f}\n"
                        f"💵 PnL: ${it['pnl']:.4f} (порог: $0.20)\n"
                        f"🆔 Ордер: <code>{res['orderId']}</code>\n"
                        f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    PnLMonitor().send_telegram_message(sell_message)
                    
                    # Триггер пост-продажного балансировщика 50/50
                    try:
                        balancer = PostSaleBalancer()
                        balance_result = balancer.rebalance_on_freed_funds()
                        logger.info(f"⚖️ PostSaleBalancer: {balance_result}")
                    except Exception as e:
                        logger.error(f"Ошибка PostSaleBalancer: {e}")
                
                time.sleep(0.5)
        # BUY phase с анти-хайп фильтром
        balances = self._get_balances()
        usdt = balances.get('USDT', {}).get('free', 0.0)
        if usdt >= 5.0:
            per = usdt / len(TOP5_ALTS)
            for alt in TOP5_ALTS:
                if alt in balances:  # already have; skip
                    continue
                sym = f"{alt}USDT"
                if not self.adv.get_symbol_rules(sym):
                    continue
                
                # Проверяем анти-хайп фильтр для альта
                alt_filter = self.anti_hype_filter.check_buy_permission(sym)
                
                if not alt_filter['allowed']:
                    logger.warning(f"🚫 {alt} покупка заблокирована: {alt_filter['reason']}")
                    continue
                
                # Применяем множитель фильтра
                adjusted_amount = per * alt_filter['multiplier']
                multiplier_text = f" (×{alt_filter['multiplier']})" if alt_filter['multiplier'] != 1.0 else ""
                
                logger.info(f"Buying {alt}{multiplier_text} for ${adjusted_amount:.2f} [{alt_filter['reason']}]")
                res = self._place_limit_buy_near_market(sym, adjusted_amount)
                logger.info(f"BUY result: {res}")
                
                # Немедленное уведомление о покупке
                if res and 'orderId' in res:
                    buy_message = (
                        f"<b>🛍️ ПОКУПКА АЛЬТКОИНА</b>\n\n"
                        f"💱 Актив: {alt}\n"
                        f"💵 Сумма: ${adjusted_amount:.2f}\n"
                        f"🛡️ Фильтр: {alt_filter['reason']} ×{alt_filter['multiplier']}\n"
                        f"🆔 Ордер: <code>{res['orderId']}</code>\n"
                        f"⏰ Время: {datetime.now().strftime('%H:%M:%S')}"
                    )
                    PnLMonitor().send_telegram_message(buy_message)
                
                time.sleep(0.5)
        # Notify periodically (каждые 5 минут)
        now = time.time()
        if now - self.last_notify_time >= NOTIFY_INTERVAL_SEC and alt_items:
            orders_map = self._fetch_open_orders_map(alt_symbols)
            self._send_telegram_report(alt_items, orders_map)
            self.last_notify_time = now

    def send_status_report_once(self):
        """Send one Telegram status report for alts without trading."""
        balances = self._get_balances()
        alt_items: List[Dict] = []
        alt_symbols: List[str] = []
        for asset, data in balances.items():
            if asset in self.keep_assets:
                continue
            symbol = f"{asset}USDT"
            rules = self.adv.get_symbol_rules(symbol)
            if not rules:
                symbol = f"{asset}USDC"
                rules = self.adv.get_symbol_rules(symbol)
            if not rules:
                continue
            pnl = self._avg_cost_pnl(symbol, data['total'])
            alt_items.append({
                'asset': asset,
                'symbol': symbol,
                'quantity': data['total'],
                'current_price': pnl['current_price'],
                'pnl': pnl['unrealized_pnl']
            })
            alt_symbols.append(symbol)
        orders_map = self._fetch_open_orders_map(alt_symbols)
        self._send_telegram_report(alt_items, orders_map)

    def start(self):
        logger.info("🚀 Starting AltsMonitor")
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.error(f"AltsMonitor error: {e}")
            time.sleep(CHECK_INTERVAL_SEC)


if __name__ == '__main__':
    AltsMonitor().start() 