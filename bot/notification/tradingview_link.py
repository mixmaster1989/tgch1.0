def generate_tv_url(signal):
    return (
        f"https://www.tradingview.com/chart/?symbol=BINANCE:{signal['pair']}"
        f"&interval=30"
        f"&study1=ENTRY_{signal['entry']}"
        f"&study2=STOP_{signal['stop']}"
        f"&study3=TP1_{signal['tp1']}"
        f"&study4=TP2_{signal['tp2']}"
    )