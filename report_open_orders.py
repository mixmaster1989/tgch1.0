#!/usr/bin/env python3
import json
from datetime import datetime
from typing import List, Dict

from mex_api import MexAPI
from pnl_monitor import PnLMonitor

# Symbols to verify (sell orders for alts)
SYMBOLS: List[str] = [
    "ARUSDT",
    "MANEKIUSDT",
    "HBARUSDT",
    "BAKEUSDT",
    "PYTHUSDT",
]


def fetch_open_orders_by_symbol(api: MexAPI, symbols: List[str]) -> Dict[str, list]:
    result: Dict[str, list] = {}
    for s in symbols:
        try:
            lst = api.get_open_orders(s)
            if isinstance(lst, list):
                result[s] = lst
            else:
                result[s] = []
        except Exception:
            result[s] = []
    return result


def build_report(orders_by_symbol: Dict[str, list]) -> str:
    lines = ["📋 ОТКРЫТЫЕ ОРДЕРА (проверка через API)\n\n"]
    for s in SYMBOLS:
        lst = orders_by_symbol.get(s, [])
        if lst:
            lines.append(f"✅ {s}: {len(lst)} ордера\n")
            for o in lst[:5]:
                side = o.get('side', '')
                price = o.get('price') or o.get('stopPrice') or 'N/A'
                qty = o.get('origQty') or o.get('executedQty') or 'N/A'
                status = o.get('status', '')
                oid = o.get('orderId', '')
                lines.append(f"   • {side} {qty} @ ${price}  [{status}]  id:{oid}\n")
        else:
            lines.append(f"🚫 {s}: нет открытых ордеров\n")
    lines.append(f"\n⏰ Время: {datetime.now().strftime('%H:%M:%S')}\n")
    return "".join(lines)


def main():
    api = MexAPI()
    orders_by_symbol = fetch_open_orders_by_symbol(api, SYMBOLS)
    message = build_report(orders_by_symbol)
    # Send via Telegram
    monitor = PnLMonitor()
    monitor.send_telegram_message(message)
    # Print JSON for CLI
    print(json.dumps(orders_by_symbol, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main() 