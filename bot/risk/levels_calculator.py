def calculate_levels(clusters, atr, direction):
    entry = clusters['price_mode']
    tp1 = entry + (atr * 1.5) if direction == 'long' else entry - (atr * 1.5)
    tp2 = entry + (atr * 3) if direction == 'long' else entry - (atr * 3)
    stop = entry - (atr * 1) if direction == 'long' else entry + (atr * 1)
    return entry, stop, tp1, tp2