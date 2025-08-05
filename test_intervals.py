#!/usr/bin/env python3
"""
Тест интервалов MEX API
"""

from mex_api import MexAPI

def main():
    api = MexAPI()
    
    intervals = ['1m', '5m', '15m', '30m', '1h', '60m', '1H', '4h', '1d', '1D']
    
    for interval in intervals:
        try:
            result = api.get_klines('BTCUSDT', interval, 5)
            if isinstance(result, list) and len(result) > 0:
                print(f"OK {interval}: {len(result)} свечей")
            else:
                print(f"FAIL {interval}: {result}")
        except Exception as e:
            print(f"FAIL {interval}: {e}")

if __name__ == "__main__":
    main()