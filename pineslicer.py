import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser, scrolledtext
import json
import os
import webbrowser
from datetime import datetime
from tkinter import scrolledtext
import threading
import time, colorchooser
import json
import os
import webbrowser
from datetime import datetime

# Описание параметров для каждого типа индикатора
INDICATOR_PARAMS = {
    "ma": [
        {"name": "ma_type", "label": "Вид MA", "type": "combo", "options": [("SMA (простая)", "sma"), ("EMA (экспоненциальная)", "ema")]},
        {"name": "ma_length", "label": "Период", "type": "combo", "options": [str(i) for i in range(2, 101)]}
    ],
    "rsi": [
        {"name": "rsi_length", "label": "Период", "type": "combo", "options": [str(i) for i in range(2, 51)]},
        {"name": "rsi_overbought", "label": "Overbought", "type": "combo", "options": [str(i) for i in range(50, 101, 5)]},
        {"name": "rsi_oversold", "label": "Oversold", "type": "combo", "options": [str(i) for i in range(0, 51, 5)]}
    ],
    "cross": [
        {"name": "cross_fast", "label": "Fast MA", "type": "combo", "options": [str(i) for i in range(2, 51)]},
        {"name": "cross_slow", "label": "Slow MA", "type": "combo", "options": [str(i) for i in range(2, 201)]}
    ],
    "box": [
        {"name": "box_bars", "label": "Длина (баров)", "type": "combo", "options": [str(i) for i in range(1, 51)]}
    ],
    "macd": [
        {"name": "macd_fast", "label": "Fast EMA", "type": "combo", "options": [str(i) for i in range(2, 21)]},
        {"name": "macd_slow", "label": "Slow EMA", "type": "combo", "options": [str(i) for i in range(5, 41)]},
        {"name": "macd_signal", "label": "Signal EMA", "type": "combo", "options": [str(i) for i in range(2, 21)]}
    ],
    "bb": [
        {"name": "bb_length", "label": "Период", "type": "combo", "options": [str(i) for i in range(5, 51)]},
        {"name": "bb_stddev", "label": "StdDev", "type": "combo", "options": [str(i) for i in range(1, 6)]}
    ],
    "stoch": [
        {"name": "stoch_k", "label": "K период", "type": "combo", "options": [str(i) for i in range(3, 21)]},
        {"name": "stoch_d", "label": "D период", "type": "combo", "options": [str(i) for i in range(3, 21)]}
    ],
    "volume": [
        {"name": "vol_length", "label": "SMA период", "type": "combo", "options": [str(i) for i in range(2, 101)]}
    ],
    "channel": [
        {"name": "channel_length", "label": "Период", "type": "combo", "options": [str(i) for i in range(2, 101)]}
    ],
    "ema_cross": [
        {"name": "ema_cross_fast", "label": "Fast EMA", "type": "combo", "options": [str(i) for i in range(2, 51)]},
        {"name": "ema_cross_slow", "label": "Slow EMA", "type": "combo", "options": [str(i) for i in range(2, 201)]}
    ],
    "arrow": [
        {"name": "arrow_type", "label": "Тип сигнала", "type": "combo", "options": [("Покупка (close > open)", "buy"), ("Продажа (close < open)", "sell")]} 
    ],
    "bgcolor": [
        {"name": "bgcolor_type", "label": "Тип сигнала", "type": "combo", "options": [("Покупка (close > open)", "buy"), ("Продажа (close < open)", "sell")]}
    ]
}

# Шаблоны кода для каждого типа индикатора
TEMPLATES = {
    "ma": lambda ans: (
        "//@version=5\n"
        "indicator('Moving Average', overlay=true)\n"
        f"{ans['ma_type']}_ma = ta.{ans['ma_type']}(close, {ans['ma_length']})\n"
        f"plot({ans['ma_type']}_ma, color=color.blue)"
    ),
    "rsi": lambda ans: (
        "//@version=5\n"
        "indicator('RSI', overlay=false)\n"
        f"rsi = ta.rsi(close, {ans['rsi_length']})\n"
        f"plot(rsi, color=color.blue)\n"
        f"hline({ans['rsi_overbought']}, 'Overbought', color=color.red)\n"
        f"hline({ans['rsi_oversold']}, 'Oversold', color=color.green)"
    ),
    "cross": lambda ans: (
        "//@version=5\n"
        "indicator('Crossover Alert', overlay=true)\n"
        f"fast_ma = ta.sma(close, {ans['cross_fast']})\n"
        f"slow_ma = ta.sma(close, {ans['cross_slow']})\n"
        f"plot(fast_ma, color=color.blue)\n"
        f"plot(slow_ma, color=color.orange)\n"
        f"alertcondition(ta.crossover(fast_ma, slow_ma), title='Crossover', message='Fast MA crossed above Slow MA')"
    ),
    "box": lambda ans: (
        "//@version=5\n"
        "indicator('Box Highlight', overlay=true)\n"
        f"box.new(bar_index-{ans['box_bars']}, high, bar_index, low, color=color.new(color.green, 80))"
    ),
    "macd": lambda ans: (
        "//@version=5\n"
        "indicator('MACD', overlay=false)\n"
        f"macd = ta.ema(close, {ans['macd_fast']}) - ta.ema(close, {ans['macd_slow']})\n"
        f"signal = ta.ema(macd, {ans['macd_signal']})\n"
        f"hist = macd - signal\n"
        f"plot(macd, color=color.blue, title='MACD')\n"
        f"plot(signal, color=color.orange, title='Signal')\n"
        f"plot(hist, color=color.green, style=plot.style_columns, title='Histogram')"
    ),
    "bb": lambda ans: (
        "//@version=5\n"
        "indicator('Bollinger Bands', overlay=true)\n"
        f"basis = ta.sma(close, {ans['bb_length']})\n"
        f"dev = {ans['bb_stddev']} * ta.stdev(close, {ans['bb_length']})\n"
        f"upper = basis + dev\n"
        f"lower = basis - dev\n"
        f"plot(basis, color=color.blue)\n"
        f"plot(upper, color=color.red)\n"
        f"plot(lower, color=color.green)\n"
        f"fill(plot(upper), plot(lower), color=color.new(color.gray, 90))"
    ),
    "stoch": lambda ans: (
        "//@version=5\n"
        "indicator('Stochastic', overlay=false)\n"
        f"k = ta.stoch(close, high, low, {ans['stoch_k']})\n"
        f"d = ta.sma(k, {ans['stoch_d']})\n"
        f"plot(k, color=color.blue, title='K')\n"
        f"plot(d, color=color.orange, title='D')"
    ),
    "volume": lambda ans: (
        "//@version=5\n"
        "indicator('Volume', overlay=false)\n"
        f"plot(volume, color=color.blue, style=plot.style_columns)\n"
        f"plot(ta.sma(volume, {ans['vol_length']}), color=color.red)"
    ),
    "channel": lambda ans: (
        "//@version=5\n"
        "indicator('Price Channel', overlay=true)\n"
        f"upper = ta.highest(high, {ans['channel_length']})\n"
        f"lower = ta.lowest(low, {ans['channel_length']})\n"
        f"plot(upper, color=color.red)\n"
        f"plot(lower, color=color.green)"
    ),
    "ema_cross": lambda ans: (
        "//@version=5\n"
        "indicator('EMA Crossover Alert', overlay=true)\n"
        f"fast = ta.ema(close, {ans['ema_cross_fast']})\n"
        f"slow = ta.ema(close, {ans['ema_cross_slow']})\n"
        f"plot(fast, color=color.blue)\n"
        f"plot(slow, color=color.orange)\n"
        f"alertcondition(ta.crossover(fast, slow), title='EMA Crossover', message='Fast EMA crossed above Slow EMA')"
    ),
    "arrow": lambda ans: (
        "//@version=5\n"
        "indicator('Signal Arrow', overlay=true)\n"
        + (
            "plotshape(close > open, style=shape.triangleup, location=location.belowbar, color=color.green, size=size.small, title='Buy')" if ans['arrow_type'] == "buy"
            else "plotshape(close < open, style=shape.triangledown, location=location.abovebar, color=color.red, size=size.small, title='Sell')"
        )
    ),
    "bgcolor": lambda ans: (
        "//@version=5\n"
        "indicator('Background Color Highlight', overlay=true)\n"
        + (
            "bgcolor(close > open ? color.new(color.green, 85) : na)" if ans['bgcolor_type'] == "buy"
            else "bgcolor(close < open ? color.new(color.red, 85) : na)"
        )
    ),
}

# Новый список доступных блоков (модулей)
BLOCKS = [
    {
        "key": "ema",
        "label": "EMA",
        "category": "Тренд",
        "description": "Экспоненциальная скользящая средняя - индикатор тренда с большим весом последних данных",
        "params": [
            {"name": "length", "label": "Период EMA", "type": "int", "default": 21, "min": 2, "max": 500},
            {"name": "color", "label": "Цвет", "type": "color", "default": "color.blue"},
            {"name": "show", "label": "Показывать EMA", "type": "bool", "default": True}
        ]
    },
    {
        "key": "sma",
        "label": "SMA",
        "category": "Тренд",
        "description": "Простая скользящая средняя - базовый индикатор тренда с равным весом всех данных",
        "params": [
            {"name": "sma_length", "label": "Период SMA", "type": "int", "default": 50, "min": 2, "max": 500},
            {"name": "sma_color", "label": "Цвет", "type": "color", "default": "color.purple"},
            {"name": "sma_show", "label": "Показывать SMA", "type": "bool", "default": True}
        ]
    },
    {
        "key": "rsi",
        "label": "RSI",
        "category": "Осциллятор",
        "description": "Индекс относительной силы - измеряет скорость и величину изменения цен",
        "params": [
            {"name": "length", "label": "Период RSI", "type": "int", "default": 14, "min": 2, "max": 100},
            {"name": "long_level", "label": "RSI уровень для лонга", "type": "float", "default": 25},
            {"name": "short_level", "label": "RSI уровень для шорта", "type": "float", "default": 75},
            {"name": "show", "label": "Показывать RSI", "type": "bool", "default": True}
        ]
    },
    {
        "key": "vpvr",
        "label": "Volume Profile (VPVR)",
        "category": "Объем",
        "description": "Профиль объема - показывает распределение объема по ценовым уровням",
        "params": [
            {"name": "lookback_bars", "label": "Баров для анализа", "type": "int", "default": 100, "min": 10, "max": 500},
            {"name": "profile_rows", "label": "Уровней профиля", "type": "int", "default": 50, "min": 10, "max": 100},
            {"name": "profile_width", "label": "Ширина профиля (%)", "type": "float", "default": 20.0, "min": 5.0, "max": 50.0},
            {"name": "show_poc", "label": "Показывать POC", "type": "bool", "default": True},
            {"name": "show_value_area", "label": "Показывать Value Area", "type": "bool", "default": True},
            {"name": "value_area_percent", "label": "Value Area (%)", "type": "float", "default": 70.0, "min": 50.0, "max": 90.0},
            {"name": "use_heatmap", "label": "Тепловая карта", "type": "bool", "default": True},
            {"name": "heatmap_transparency", "label": "Прозрачность тепловой карты", "type": "int", "default": 70, "min": 0, "max": 95},
            {"name": "color_low_volume", "label": "Цвет низкого объема", "type": "color", "default": "color.new(color.blue, 80)"},
            {"name": "color_high_volume", "label": "Цвет высокого объема", "type": "color", "default": "color.new(color.red, 20)"},
            {"name": "poc_color", "label": "Цвет POC линии", "type": "color", "default": "color.yellow"},
            {"name": "poc_width", "label": "Толщина POC линии", "type": "int", "default": 2, "min": 1, "max": 5},
            {"name": "va_color", "label": "Цвет Value Area", "type": "color", "default": "color.new(color.orange, 70)"}
        ]
    },
    {
        "key": "macd",
        "label": "MACD",
        "category": "Осциллятор",
        "description": "Схождение/расхождение скользящих средних - трендовый индикатор импульса",
        "params": [
            {"name": "macd_fast", "label": "Fast EMA", "type": "int", "default": 12, "min": 2, "max": 50},
            {"name": "macd_slow", "label": "Slow EMA", "type": "int", "default": 26, "min": 5, "max": 100},
            {"name": "macd_signal", "label": "Signal EMA", "type": "int", "default": 9, "min": 2, "max": 50},
            {"name": "macd_show_hist", "label": "Показывать гистограмму", "type": "bool", "default": True},
            {"name": "macd_color_up", "label": "Цвет роста", "type": "color", "default": "color.green"},
            {"name": "macd_color_down", "label": "Цвет падения", "type": "color", "default": "color.red"}
        ]
    },
    {
        "key": "bb",
        "label": "Bollinger Bands",
        "category": "Волатильность",
        "description": "Полосы Боллинджера - измеряют волатильность и потенциальные уровни перекупленности/перепроданности",
        "params": [
            {"name": "bb_length", "label": "Период", "type": "int", "default": 20, "min": 5, "max": 100},
            {"name": "bb_stddev", "label": "StdDev", "type": "float", "default": 2.0, "min": 0.5, "max": 5.0, "step": 0.1},
            {"name": "bb_fill", "label": "Заливка между полосами", "type": "bool", "default": True}
        ]
    },
    {
        "key": "stoch",
        "label": "Stochastic",
        "category": "Осциллятор",
        "description": "Стохастический осциллятор - показывает положение текущей цены относительно диапазона цен за период",
        "params": [
            {"name": "stoch_k", "label": "K период", "type": "int", "default": 14, "min": 3, "max": 50},
            {"name": "stoch_d", "label": "D период", "type": "int", "default": 3, "min": 1, "max": 30},
            {"name": "stoch_smooth", "label": "Сглаживание", "type": "int", "default": 3, "min": 1, "max": 30},
            {"name": "stoch_overbought", "label": "Уровень перекупленности", "type": "int", "default": 80, "min": 50, "max": 100},
            {"name": "stoch_oversold", "label": "Уровень перепроданности", "type": "int", "default": 20, "min": 0, "max": 50}
        ]
    },
    {
        "key": "volume",
        "label": "Volume",
        "category": "Объем",
        "description": "Объем торгов - показывает активность рынка",
        "params": [
            {"name": "vol_length", "label": "SMA период", "type": "int", "default": 20, "min": 2, "max": 100},
            {"name": "vol_ma_type", "label": "Тип MA", "type": "combo", "options": [("SMA", "sma"), ("EMA", "ema"), ("WMA", "wma")], "default": "sma"},
            {"name": "vol_up_color", "label": "Цвет повышения", "type": "color", "default": "color.green"},
            {"name": "vol_down_color", "label": "Цвет понижения", "type": "color", "default": "color.red"}
        ]
    },
    {
        "key": "channel",
        "label": "Price Channel",
        "category": "Тренд",
        "description": "Ценовой канал - отображает максимумы и минимумы цены за период",
        "params": [
            {"name": "channel_length", "label": "Период", "type": "int", "default": 20, "min": 2, "max": 200},
            {"name": "channel_upper_color", "label": "Цвет верхней линии", "type": "color", "default": "color.red"},
            {"name": "channel_lower_color", "label": "Цвет нижней линии", "type": "color", "default": "color.green"},
            {"name": "channel_fill", "label": "Заливка канала", "type": "bool", "default": False}
        ]
    },
    {
        "key": "ema_cross",
        "label": "EMA Cross",
        "category": "Сигнал",
        "description": "Пересечение EMA - генерирует сигналы на пересечении быстрой и медленной EMA",
        "params": [
            {"name": "ema_cross_fast", "label": "Fast EMA", "type": "int", "default": 9, "min": 2, "max": 50},
            {"name": "ema_cross_slow", "label": "Slow EMA", "type": "int", "default": 21, "min": 5, "max": 200},
            {"name": "ema_cross_show_lines", "label": "Показывать линии", "type": "bool", "default": True},
            {"name": "ema_cross_show_signals", "label": "Показывать сигналы", "type": "bool", "default": True}
        ]
    },
    {
        "key": "arrow",
        "label": "Signal Arrows",
        "category": "Визуализация",
        "description": "Сигнальные стрелки - отображают сигналы покупки/продажи на графике",
        "params": [
            {"name": "arrow_type", "label": "Тип сигнала", "type": "combo", "options": [("Покупка (close > open)", "buy"), ("Продажа (close < open)", "sell")], "default": "buy"},
            {"name": "arrow_size", "label": "Размер стрелок", "type": "combo", "options": [("Маленький", "size.small"), ("Средний", "size.normal"), ("Большой", "size.large")], "default": "size.normal"},
            {"name": "arrow_color", "label": "Цвет стрелок", "type": "color", "default": "color.yellow"}
        ]
    },
    {
        "key": "bgcolor",
        "label": "Background Color",
        "category": "Визуализация",
        "description": "Фоновая подсветка - выделяет определенные условия на графике",
        "params": [
            {"name": "bgcolor_type", "label": "Тип сигнала", "type": "combo", "options": [("Покупка (close > open)", "buy"), ("Продажа (close < open)", "sell")], "default": "buy"},
            {"name": "bgcolor_transparency", "label": "Прозрачность", "type": "int", "default": 85, "min": 0, "max": 100}
        ]
    },
    {
        "key": "pivot",
        "label": "Pivot Points",
        "category": "Уровни",
        "description": "Точки разворота - ключевые уровни поддержки и сопротивления",
        "params": [
            {"name": "pivot_type", "label": "Тип", "type": "combo", "options": [("Стандартный", "standard"), ("Фибоначчи", "fibonacci"), ("Вуди", "woodie"), ("Камарилла", "camarilla")], "default": "standard"},
            {"name": "pivot_timeframe", "label": "Таймфрейм", "type": "combo", "options": [("День", "day"), ("Неделя", "week"), ("Месяц", "month")], "default": "day"},
            {"name": "pivot_show_labels", "label": "Показывать метки", "type": "bool", "default": True},
            {"name": "pivot_pp_color", "label": "Цвет PP", "type": "color", "default": "color.yellow"},
            {"name": "pivot_s_color", "label": "Цвет поддержки", "type": "color", "default": "color.green"},
            {"name": "pivot_r_color", "label": "Цвет сопротивления", "type": "color", "default": "color.red"}
        ]
    },
    {
        "key": "ichimoku",
        "label": "Ichimoku Cloud",
        "category": "Тренд",
        "description": "Облако Ишимоку - комплексный индикатор для определения тренда, поддержки и сопротивления",
        "params": [
            {"name": "ichimoku_tenkan", "label": "Tenkan-sen", "type": "int", "default": 9, "min": 1, "max": 100},
            {"name": "ichimoku_kijun", "label": "Kijun-sen", "type": "int", "default": 26, "min": 1, "max": 200},
            {"name": "ichimoku_senkou", "label": "Senkou Span B", "type": "int", "default": 52, "min": 1, "max": 300},
            {"name": "ichimoku_displacement", "label": "Смещение", "type": "int", "default": 26, "min": 1, "max": 100},
            {"name": "ichimoku_show_cloud", "label": "Показывать облако", "type": "bool", "default": True},
            {"name": "ichimoku_show_lines", "label": "Показывать линии", "type": "bool", "default": True}
        ]
    },
    {
        "key": "atr",
        "label": "ATR",
        "category": "Волатильность",
        "description": "Average True Range - измеряет волатильность рынка",
        "params": [
            {"name": "atr_length", "label": "Период", "type": "int", "default": 14, "min": 1, "max": 100},
            {"name": "atr_smoothing", "label": "Сглаживание", "type": "combo", "options": [("RMA", "rma"), ("SMA", "sma"), ("EMA", "ema"), ("WMA", "wma")], "default": "rma"},
            {"name": "atr_color", "label": "Цвет", "type": "color", "default": "color.purple"}
        ]
    },
    {
        "key": "zigzag",
        "label": "ZigZag",
        "category": "Паттерны",
        "description": "ZigZag - фильтрует шум и выделяет значимые ценовые движения",
        "params": [
            {"name": "zigzag_depth", "label": "Глубина", "type": "int", "default": 10, "min": 1, "max": 100},
            {"name": "zigzag_deviation", "label": "Отклонение (%)", "type": "float", "default": 5.0, "min": 0.1, "max": 30.0, "step": 0.1},
            {"name": "zigzag_backstep", "label": "Шаг назад", "type": "int", "default": 3, "min": 1, "max": 20},
            {"name": "zigzag_color", "label": "Цвет", "type": "color", "default": "color.blue"},
            {"name": "zigzag_width", "label": "Толщина", "type": "int", "default": 2, "min": 1, "max": 5}
        ]
    },
    {
        "key": "fib_retracement",
        "label": "Fibonacci Retracement",
        "category": "Уровни",
        "description": "Уровни коррекции Фибоначчи - популярный инструмент для определения уровней коррекции",
        "params": [
            {"name": "fib_lookback", "label": "Период поиска", "type": "int", "default": 100, "min": 10, "max": 500},
            {"name": "fib_show_labels", "label": "Показывать метки", "type": "bool", "default": True},
            {"name": "fib_color", "label": "Цвет линий", "type": "color", "default": "color.orange"}
        ]
    }
]

# Новый шаблон генерации кода: собирает input, переменные, функции, plot, alertcondition
def generate_full_pine_script(selected_blocks):
    code = ["//@version=5"]
    code.append('indicator("Custom Combo", overlay=true, max_boxes_count=500, max_lines_count=500)')
    # INPUTS
    for block in selected_blocks:
        for p in block["params"]:
            v = p["value"]
            if p["type"] == "int":
                code.append(f"{p['name']} = input.int({v}, '{p['label']}', minval={p.get('min', 1)}, maxval={p.get('max', 9999)})")
            elif p["type"] == "float":
                code.append(f"{p['name']} = input.float({v}, '{p['label']}')")
            elif p["type"] == "bool":
                code.append(f"{p['name']} = input.bool({str(v).lower()}, '{p['label']}')")
            elif p["type"] == "color":
                code.append(f"{p['name']} = input.color({v}, '{p['label']}')")

    # Переменные, функции и plot для каждого блока (расширено)
    for block in selected_blocks:
        if block["key"] == "ema":
            code.append(f"ema_val = ta.ema(close, length)")
            code.append(f"plot(show ? ema_val : na, color=color, title='EMA')")
        elif block["key"] == "rsi":
            code.append(f"rsi_val = ta.rsi(close, length)")
            code.append(f"plot(show ? rsi_val : na, color=color.blue, title='RSI')")
            code.append(f"long_signal = rsi_val <= long_level")
            code.append(f"short_signal = rsi_val >= short_level")
            code.append(f"plotshape(long_signal, title='RSI Лонг', style=shape.labelup, location=location.belowbar, color=color.green)")
            code.append(f"plotshape(short_signal, title='RSI Шорт', style=shape.labeldown, location=location.abovebar, color=color.red)")
            code.append(f"alertcondition(long_signal, title='RSI Лонг сигнал', message='RSI достиг уровня лонга')")
            code.append(f"alertcondition(short_signal, title='RSI Шорт сигнал', message='RSI достиг уровня шорта')")
        elif block["key"] == "vpvr":
            # Реальная реализация VPVR
            code.append("// VPVR (Volume Profile Visible Range)")
            code.append("// Расчет диапазона цен")
            code.append(f"var float price_high = high[0]")
            code.append(f"var float price_low = low[0]")
            code.append(f"for i = 0 to lookback_bars - 1")
            code.append(f"    price_high := math.max(price_high, high[i])")
            code.append(f"    price_low := math.min(price_low, low[i])")
            code.append(f"float price_range = price_high - price_low")
            code.append(f"float row_height = price_range / profile_rows")
            
            # Расчет объемов для каждого ценового уровня
            code.append(f"var volumes = array.new_float(profile_rows, 0.0)")
            code.append(f"for i = 0 to lookback_bars - 1")
            code.append(f"    float candle_high = high[i]")
            code.append(f"    float candle_low = low[i]")
            code.append(f"    float candle_vol = volume[i]")
            code.append(f"    for j = 0 to profile_rows - 1")
            code.append(f"        float row_low = price_low + j * row_height")
            code.append(f"        float row_high = row_low + row_height")
            code.append(f"        if (candle_high >= row_low and candle_low <= row_high)")
            code.append(f"            array.set(volumes, j, array.get(volumes, j) + candle_vol)")
            
            # Нахождение POC (Point of Control) - уровень с максимальным объемом
            code.append(f"float max_volume = 0.0")
            code.append(f"int poc_index = 0")
            code.append(f"for i = 0 to profile_rows - 1")
            code.append(f"    if array.get(volumes, i) > max_volume")
            code.append(f"        max_volume := array.get(volumes, i)")
            code.append(f"        poc_index := i")
            
            # Расчет Value Area
            code.append(f"float total_volume = 0.0")
            code.append(f"for i = 0 to profile_rows - 1")
            code.append(f"    total_volume := total_volume + array.get(volumes, i)")
            code.append(f"float target_va_volume = total_volume * value_area_percent / 100")
            code.append(f"float current_va_volume = array.get(volumes, poc_index)")
            code.append(f"int va_upper = poc_index")
            code.append(f"int va_lower = poc_index")
            code.append(f"while current_va_volume < target_va_volume and (va_upper < profile_rows - 1 or va_lower > 0)")
            code.append(f"    float vol_above = va_upper < profile_rows - 1 ? array.get(volumes, va_upper + 1) : 0")
            code.append(f"    float vol_below = va_lower > 0 ? array.get(volumes, va_lower - 1) : 0")
            code.append(f"    if vol_above >= vol_below and va_upper < profile_rows - 1")
            code.append(f"        va_upper := va_upper + 1")
            code.append(f"        current_va_volume := current_va_volume + vol_above")
            code.append(f"    else if va_lower > 0")
            code.append(f"        va_lower := va_lower - 1")
            code.append(f"        current_va_volume := current_va_volume + vol_below")
            
            # Отрисовка профиля объема
            code.append(f"if barstate.islast")
            code.append(f"    float bar_width = profile_width / 100 * (time - time[1])")
            code.append(f"    float x_loc = time + bar_width / 2")
            
            # Отрисовка тепловой карты объемов
            code.append(f"    if use_heatmap")
            code.append(f"        for i = 0 to profile_rows - 1")
            code.append(f"            float vol_ratio = array.get(volumes, i) / max_volume")
            code.append(f"            float row_low = price_low + i * row_height")
            code.append(f"            float row_high = row_low + row_height")
            code.append(f"            float row_mid = (row_low + row_high) / 2")
            code.append(f"            color vol_color = color.from_gradient(vol_ratio, 0, 1, color_low_volume, color_high_volume)")
            code.append(f"            box.new(time, row_high, x_loc, row_low, border_color=na, bgcolor=vol_color)")
            
            # Отрисовка POC и Value Area
            code.append(f"    if show_poc")
            code.append(f"        float poc_price = price_low + (poc_index + 0.5) * row_height")
            code.append(f"        line.new(time - bar_width, poc_price, x_loc, poc_price, color=poc_color, width=poc_width)")
            
            code.append(f"    if show_value_area")
            code.append(f"        float va_high = price_low + (va_upper + 1) * row_height")
            code.append(f"        float va_low = price_low + va_lower * row_height")
            code.append(f"        box.new(time - bar_width, va_high, x_loc, va_low, border_color=na, bgcolor=va_color)")
        elif block["key"] == "macd":
            code.append(f"macd = ta.ema(close, macd_fast) - ta.ema(close, macd_slow)")
            code.append(f"signal = ta.ema(macd, macd_signal)")
            code.append(f"hist = macd - signal")
            code.append(f"plot(macd, color=color.blue, title='MACD')")
            code.append(f"plot(signal, color=color.orange, title='Signal')")
            code.append(f"plot(hist, color=color.green, style=plot.style_columns, title='Histogram')")
        elif block["key"] == "bb":
            code.append(f"basis = ta.sma(close, bb_length)")
            code.append(f"dev = bb_stddev * ta.stdev(close, bb_length)")
            code.append(f"upper = basis + dev")
            code.append(f"lower = basis - dev")
            code.append(f"plot(basis, color=color.blue)")
            code.append(f"plot(upper, color=color.red)")
            code.append(f"plot(lower, color=color.green)")
            code.append(f"fill(plot(upper), plot(lower), color=color.new(color.gray, 90))")
        elif block["key"] == "stoch":
            code.append(f"k = ta.stoch(close, high, low, stoch_k)")
            code.append(f"d = ta.sma(k, stoch_d)")
            code.append(f"plot(k, color=color.blue, title='K')")
            code.append(f"plot(d, color=color.orange, title='D')")
        elif block["key"] == "volume":
            code.append(f"plot(volume, color=color.blue, style=plot.style_columns)")
            code.append(f"plot(ta.sma(volume, vol_length), color=color.red)")
        elif block["key"] == "channel":
            code.append(f"upper = ta.highest(high, channel_length)")
            code.append(f"lower = ta.lowest(low, channel_length)")
            code.append(f"plot(upper, color=color.red)")
            code.append(f"plot(lower, color=color.green)")
        elif block["key"] == "ema_cross":
            code.append(f"fast = ta.ema(close, ema_cross_fast)")
            code.append(f"slow = ta.ema(close, ema_cross_slow)")
            code.append(f"plot(fast, color=color.blue)")
            code.append(f"plot(slow, color=color.orange)")
            code.append(f"alertcondition(ta.crossover(fast, slow), title='EMA Crossover', message='Fast EMA crossed above Slow EMA')")
        elif block["key"] == "arrow":
            code.append(
                "plotshape(close > open, style=shape.triangleup, location=location.belowbar, color=color.green, size=size.small, title='Buy')"
                if block["params"][0]["value"] == "buy"
                else "plotshape(close < open, style=shape.triangledown, location=location.abovebar, color=color.red, size=size.small, title='Sell')"
            )
        elif block["key"] == "bgcolor":
            code.append(
                "bgcolor(close > open ? color.new(color.green, 85) : na)"
                if block["params"][0]["value"] == "buy"
                else "bgcolor(close < open ? color.new(color.red, 85) : na)"
            )
        elif block["key"] == "box":
            code.append(f"box.new(bar_index-{block['params'][0]['value']}, high, bar_index, low, color=color.new(color.green, 80))")
        elif block["key"] == "cross":
            code.append(f"fast_ma = ta.sma(close, cross_fast)")
            code.append(f"slow_ma = ta.sma(close, cross_slow)")
            code.append(f"plot(fast_ma, color=color.blue)")
            code.append(f"plot(slow_ma, color=color.orange)")
            code.append(f"alertcondition(ta.crossover(fast_ma, slow_ma), title='Crossover', message='Fast MA crossed above Slow MA')")

    # Объединение сигналов (пример)
    if any(b["key"] == "rsi" for b in selected_blocks) and any(b["key"] == "ema" for b in selected_blocks):
        code.append("combo_long = long_signal and ema_val > close")
        code.append("combo_short = short_signal and ema_val < close")
        code.append("plotshape(combo_long, title='COMBO Лонг', style=shape.triangleup, location=location.belowbar, color=color.purple)")
        code.append("plotshape(combo_short, title='COMBO Шорт', style=shape.triangledown, location=location.abovebar, color=color.purple)")
        code.append("alertcondition(combo_long, title='COMBO Лонг', message='Совпадение RSI и EMA для лонга')")
        code.append("alertcondition(combo_short, title='COMBO Шорт', message='Совпадение RSI и EMA для шорта')")

    # Можно добавить объединение других сигналов, паттерны, фон, алерты и т.д.
    code.append("// ...дальнейшее развитие: объединение сигналов, сложные паттерны, пользовательские функции ...")
    return "\n".join(code)

class PineSlicerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PineSlicer – Pine Script Builder")
        self.geometry("1200x800")
        self.configure(bg="#f8f8f8")
        self.option_add("*Font", ("Segoe UI", 10))
        self.resizable(True, True)
        
        # Создаем стиль
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Используем тему clam для лучшего вида
        self.style.configure('TButton', background='#4a86e8', foreground='white', borderwidth=1)
        self.style.configure('TCheckbutton', background='#f8f8f8')
        self.style.configure('TFrame', background='#f8f8f8')
        self.style.configure('Category.TFrame', background='#e6e6e6')
        self.style.configure('Category.TLabel', background='#e6e6e6', font=('Segoe UI', 10, 'bold'))
        
        # Переменные для хранения состояния
        self.block_vars = {}
        self.block_param_vars = {}
        self.param_widgets = []
        self.current_preset = None
        self.presets = self.load_presets()
        self.categories = self.get_categories()
        self.selected_category = tk.StringVar(value="Все")
        
        # Создаем главный контейнер с вкладками
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Вкладка конструктора
        self.builder_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.builder_frame, text="Конструктор")
        
        # Вкладка предпросмотра
        self.preview_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.preview_frame, text="Предпросмотр")
        
        # Вкладка настроек
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Настройки")
        
        # Вкладка справки
        self.help_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.help_frame, text="Справка")
        
        # Настраиваем вкладку конструктора
        self.setup_builder_tab()
        
        # Настраиваем вкладку предпросмотра
        self.setup_preview_tab()
        
        # Настраиваем вкладку настроек
        self.setup_settings_tab()
        
        # Настраиваем вкладку справки
        self.setup_help_tab()
        
        # Статусбар
        self.status_var = tk.StringVar(value="Готов к работе")
        self.statusbar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.statusbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Загружаем последний использованный пресет, если есть
        self.load_last_session()
    
    def setup_builder_tab(self):
        # Создаем фреймы для вкладки конструктора
        left_panel = ttk.Frame(self.builder_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        right_panel = ttk.Frame(self.builder_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Левая панель - выбор блоков
        self.blocks_frame = ttk.LabelFrame(left_panel, text="Доступные модули")
        self.blocks_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Фильтр по категориям
        filter_frame = ttk.Frame(self.blocks_frame)
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(filter_frame, text="Категория:").pack(side=tk.LEFT, padx=5)
        category_combo = ttk.Combobox(filter_frame, textvariable=self.selected_category, 
                                      values=["Все"] + self.categories, state="readonly", width=15)
        category_combo.pack(side=tk.LEFT, padx=5)
        category_combo.bind("<<ComboboxSelected>>", self.filter_blocks_by_category)
        
        # Поиск
        search_frame = ttk.Frame(self.blocks_frame)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.search_blocks)
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=5)
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Создаем канвас с прокруткой для блоков
        blocks_canvas_frame = ttk.Frame(self.blocks_frame)
        blocks_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.blocks_canvas = tk.Canvas(blocks_canvas_frame, bg="#f8f8f8", highlightthickness=0)
        scrollbar = ttk.Scrollbar(blocks_canvas_frame, orient="vertical", command=self.blocks_canvas.yview)
        self.blocks_frame_inner = ttk.Frame(self.blocks_canvas)
        
        self.blocks_canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.blocks_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.blocks_canvas_window = self.blocks_canvas.create_window((0, 0), window=self.blocks_frame_inner, anchor="nw")
        
        self.blocks_frame_inner.bind("<Configure>", lambda e: self.blocks_canvas.configure(scrollregion=self.blocks_canvas.bbox("all")))
        self.blocks_canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Заполняем блоки
        self.render_blocks()
        
        # Пресеты
        presets_frame = ttk.LabelFrame(left_panel, text="Пресеты")
        presets_frame.pack(fill=tk.X, padx=5, pady=5)
        
        presets_buttons = ttk.Frame(presets_frame)
        presets_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        self.preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(presets_buttons, textvariable=self.preset_var, 
                                        values=list(self.presets.keys()), width=20)
        self.preset_combo.pack(side=tk.LEFT, padx=2, pady=2, fill=tk.X, expand=True)
        
        load_btn = ttk.Button(presets_buttons, text="Загрузить", command=self.load_preset, width=10)
        load_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        save_btn = ttk.Button(presets_buttons, text="Сохранить", command=self.save_preset, width=10)
        save_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Правая панель - параметры и редактор
        # Параметры выбранных блоков
        self.param_frame = ttk.LabelFrame(right_panel, text="Параметры")
        self.param_frame.pack(fill=tk.BOTH, expand=False, padx=5, pady=5)
        
        # Канвас с прокруткой для параметров
        param_canvas_frame = ttk.Frame(self.param_frame)
        param_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.param_canvas = tk.Canvas(param_canvas_frame, bg="#f8f8f8", highlightthickness=0, height=200)
        param_scrollbar = ttk.Scrollbar(param_canvas_frame, orient="vertical", command=self.param_canvas.yview)
        self.param_frame_inner = ttk.Frame(self.param_canvas)
        
        self.param_canvas.configure(yscrollcommand=param_scrollbar.set)
        param_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.param_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.param_canvas_window = self.param_canvas.create_window((0, 0), window=self.param_frame_inner, anchor="nw")
        
        self.param_frame_inner.bind("<Configure>", lambda e: self.param_canvas.configure(scrollregion=self.param_canvas.bbox("all")))
        self.param_canvas.bind("<Configure>", self.on_param_canvas_configure)
        
        # Кнопки действий
        button_frame = ttk.Frame(right_panel)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.gen_btn = ttk.Button(button_frame, text="Сгенерировать", command=self.generate_and_test, width=15)
        self.gen_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        self.save_btn = ttk.Button(button_frame, text="Сохранить в файл", command=self.save_script, width=15)
        self.save_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        self.copy_btn = ttk.Button(button_frame, text="Копировать", command=self.copy_to_clipboard, width=15)
        self.copy_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        self.clear_btn = ttk.Button(button_frame, text="Очистить", command=self.clear_script, width=15)
        self.clear_btn.pack(side=tk.LEFT, padx=2, pady=2)
        
        # Редактор кода
        editor_frame = ttk.LabelFrame(right_panel, text="Pine Script")
        editor_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_editor = scrolledtext.ScrolledText(editor_frame, wrap=tk.NONE, font=("Consolas", 10))
        self.text_editor.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Добавляем стандартное контекстное меню для правой кнопки мыши
        self.context_menu = tk.Menu(self.text_editor, tearoff=0)
        self.context_menu.add_command(label="Вырезать", command=lambda: self.text_editor.event_generate("<<Cut>>"))
        self.context_menu.add_command(label="Копировать", command=lambda: self.text_editor.event_generate("<<Copy>>"))
        self.context_menu.add_command(label="Вставить", command=lambda: self.text_editor.event_generate("<<Paste>>"))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Выделить всё", command=lambda: self.text_editor.tag_add("sel", "1.0", "end"))
        
        # Привязываем событие правой кнопки мыши к показу контекстного меню
        self.text_editor.bind("<Button-3>", self.show_context_menu)
        
        # Подсветка синтаксиса
        self.setup_syntax_highlighting()
    
    def setup_preview_tab(self):
        # Фрейм для предпросмотра
        preview_container = ttk.Frame(self.preview_frame)
        preview_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Верхняя панель с кнопками
        top_panel = ttk.Frame(preview_container)
        top_panel.pack(fill=tk.X, pady=5)
        
        ttk.Button(top_panel, text="Обновить предпросмотр", command=self.update_preview).pack(side=tk.LEFT, padx=5)
        ttk.Label(top_panel, text="Примечание: Предпросмотр показывает примерный вид индикатора").pack(side=tk.LEFT, padx=20)
        
        # Канвас для предпросмотра
        self.preview_canvas = tk.Canvas(preview_container, bg="white", highlightthickness=1, highlightbackground="#cccccc")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Добавляем сообщение о том, что предпросмотр недоступен
        self.preview_canvas.create_text(400, 200, text="Нажмите 'Обновить предпросмотр' для визуализации индикатора", font=("Segoe UI", 12))
    
    def setup_settings_tab(self):
        # Фрейм для настроек
        settings_container = ttk.Frame(self.settings_frame)
        settings_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Настройки редактора
        editor_settings = ttk.LabelFrame(settings_container, text="Настройки редактора")
        editor_settings.pack(fill=tk.X, pady=5)
        
        # Шрифт
        font_frame = ttk.Frame(editor_settings)
        font_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(font_frame, text="Шрифт редактора:").pack(side=tk.LEFT, padx=5)
        
        self.font_size_var = tk.StringVar(value="10")
        font_size = ttk.Spinbox(font_frame, from_=8, to=24, textvariable=self.font_size_var, width=5)
        font_size.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(font_frame, text="Применить", command=self.change_font_size).pack(side=tk.LEFT, padx=5)
        
        # Тема
        theme_frame = ttk.Frame(editor_settings)
        theme_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(theme_frame, text="Тема:").pack(side=tk.LEFT, padx=5)
        
        self.theme_var = tk.StringVar(value="Светлая")
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, values=["Светлая", "Тёмная"], state="readonly", width=10)
        theme_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(theme_frame, text="Применить", command=self.change_theme).pack(side=tk.LEFT, padx=5)
        
        # Настройки генерации кода
        code_settings = ttk.LabelFrame(settings_container, text="Настройки генерации кода")
        code_settings.pack(fill=tk.X, pady=10)
        
        # Формат кода
        format_frame = ttk.Frame(code_settings)
        format_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.format_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(format_frame, text="Форматировать код", variable=self.format_var).pack(side=tk.LEFT, padx=5)
        
        self.comments_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(format_frame, text="Добавлять комментарии", variable=self.comments_var).pack(side=tk.LEFT, padx=20)
        
        # Версия Pine Script
        version_frame = ttk.Frame(code_settings)
        version_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(version_frame, text="Версия Pine Script:").pack(side=tk.LEFT, padx=5)
        
        self.version_var = tk.StringVar(value="5")
        version_combo = ttk.Combobox(version_frame, textvariable=self.version_var, values=["5", "4"], state="readonly", width=5)
        version_combo.pack(side=tk.LEFT, padx=5)
        
        # Настройки автосохранения
        autosave_settings = ttk.LabelFrame(settings_container, text="Автосохранение")
        autosave_settings.pack(fill=tk.X, pady=10)
        
        autosave_frame = ttk.Frame(autosave_settings)
        autosave_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.autosave_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(autosave_frame, text="Автосохранение сессии", variable=self.autosave_var).pack(side=tk.LEFT, padx=5)
        
        # Кнопки
        buttons_frame = ttk.Frame(settings_container)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="Сохранить настройки", command=self.save_settings).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Сбросить настройки", command=self.reset_settings).pack(side=tk.LEFT, padx=5)
    
    def setup_help_tab(self):
        # Фрейм для справки
        help_container = ttk.Frame(self.help_frame)
        help_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Вкладки справки
        help_notebook = ttk.Notebook(help_container)
        help_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка "О программе"
        about_frame = ttk.Frame(help_notebook)
        help_notebook.add(about_frame, text="О программе")
        
        about_text = """
        PineSlicer - Конструктор индикаторов для TradingView
        
        Версия: 1.0
        
        Это инструмент для создания индикаторов на языке Pine Script без необходимости
        писать код вручную. Выберите нужные модули, настройте параметры и получите
        готовый код для TradingView.
        
        © 2023 PineSlicer
        """
        
        about_label = ttk.Label(about_frame, text=about_text, justify=tk.LEFT, wraplength=600)
        about_label.pack(padx=20, pady=20)
        
        # Вкладка "Руководство"
        guide_frame = ttk.Frame(help_notebook)
        help_notebook.add(guide_frame, text="Руководство")
        
        guide_text = scrolledtext.ScrolledText(guide_frame, wrap=tk.WORD, font=("Segoe UI", 10))
        guide_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        guide_content = """
        # Руководство пользователя PineSlicer
        
        ## Начало работы
        
        1. Выберите нужные модули из списка слева
        2. Настройте параметры для каждого модуля
        3. Нажмите "Сгенерировать" для создания кода
        4. Скопируйте код или сохраните его в файл
        5. Вставьте код в редактор Pine Script на TradingView
        
        ## Работа с модулями
        
        Каждый модуль представляет собой отдельный индикатор или функцию.
        Вы можете комбинировать несколько модулей для создания комплексных индикаторов.
        
        ## Пресеты
        
        Пресеты позволяют сохранять и загружать настройки индикаторов.
        Для сохранения пресета:
        1. Настройте индикатор
        2. Введите имя пресета в поле
        3. Нажмите "Сохранить"
        
        Для загрузки пресета:
        1. Выберите пресет из списка
        2. Нажмите "Загрузить"
        
        ## Предпросмотр
        
        Вкладка "Предпросмотр" позволяет увидеть примерный вид индикатора
        без необходимости загружать его на TradingView.
        
        ## Настройки
        
        Во вкладке "Настройки" вы можете изменить:
        - Внешний вид редактора
        - Параметры генерации кода
        - Настройки автосохранения
        
        ## Советы
        
        - Используйте поиск для быстрого нахождения нужных модулей
        - Фильтруйте модули по категориям
        - Сохраняйте часто используемые комбинации как пресеты
        - Проверяйте сгенерированный код перед использованием
        """
        
        guide_text.insert(tk.END, guide_content)
        guide_text.configure(state="disabled")
        
        # Вкладка "Pine Script"
        pine_frame = ttk.Frame(help_notebook)
        help_notebook.add(pine_frame, text="Pine Script")
        
        pine_text = scrolledtext.ScrolledText(pine_frame, wrap=tk.WORD, font=("Segoe UI", 10))
        pine_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        pine_content = """
        # Основы Pine Script
        
        Pine Script - это язык программирования, разработанный специально для создания
        пользовательских индикаторов и стратегий на платформе TradingView.
        
        ## Структура скрипта
        
        Базовая структура Pine Script:
        
        ```
        //@version=5
        indicator("Имя индикатора", overlay=true)
        
        // Расчеты
        sma = ta.sma(close, 14)
        
        // Отображение
        plot(sma, color=color.blue)
        ```
        
        ## Основные функции
        
        - `indicator()` - объявляет скрипт как индикатор
        - `plot()` - отображает линию на графике
        - `plotshape()` - отображает символы на графике
        - `bgcolor()` - изменяет цвет фона
        - `alertcondition()` - создает условие для оповещений
        
        ## Встроенные индикаторы
        
        Pine Script предоставляет множество встроенных индикаторов:
        
        - `ta.sma()` - простая скользящая средняя
        - `ta.ema()` - экспоненциальная скользящая средняя
        - `ta.rsi()` - индекс относительной силы
        - `ta.macd()` - MACD
        - `ta.bbands()` - полосы Боллинджера
        
        ## Дополнительные ресурсы
        
        - [Документация Pine Script](https://www.tradingview.com/pine-script-docs/en/v5/index.html)
        - [Справочник Pine Script](https://www.tradingview.com/pine-script-reference/v5/)
        - [Учебник Pine Script](https://www.tradingview.com/pine-script-docs/en/v5/Tutorial.html)
        """
        
        pine_text.insert(tk.END, pine_content)
        pine_text.configure(state="disabled")
        
        # Кнопки
        buttons_frame = ttk.Frame(help_container)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="Документация Pine Script", 
                  command=lambda: webbrowser.open("https://www.tradingview.com/pine-script-docs/en/v5/index.html")).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(buttons_frame, text="Сообщить о проблеме", 
                  command=lambda: webbrowser.open("https://github.com/yourusername/pineslicer/issues")).pack(side=tk.LEFT, padx=5)

    def show_context_menu(self, event):
        # Показываем контекстное меню в позиции курсора мыши
        self.context_menu.tk_popup(event.x_root, event.y_root)
        return "break"  # Предотвращаем стандартное поведение
    
    def get_categories(self):
        """Получает список всех категорий из блоков"""
        categories = set()
        for block in BLOCKS:
            if "category" in block:
                categories.add(block["category"])
        return sorted(list(categories))
    
    def filter_blocks_by_category(self, event=None):
        """Фильтрует блоки по выбранной категории"""
        self.render_blocks()
    
    def search_blocks(self, *args):
        """Поиск блоков по введенному тексту"""
        self.render_blocks()
    
    def on_canvas_configure(self, event):
        """Обработчик изменения размера канваса блоков"""
        self.blocks_canvas.itemconfig(self.blocks_canvas_window, width=event.width)
    
    def on_param_canvas_configure(self, event):
        """Обработчик изменения размера канваса параметров"""
        self.param_canvas.itemconfig(self.param_canvas_window, width=event.width)
    
    def render_blocks(self):
        """Отображает блоки с учетом фильтра категории и поиска"""
        # Очищаем фрейм
        for widget in self.blocks_frame_inner.winfo_children():
            widget.destroy()
        
        # Получаем текст поиска и выбранную категорию
        search_text = self.search_var.get().lower()
        selected_category = self.selected_category.get()
        
        # Группируем блоки по категориям
        categories = {}
        for block in BLOCKS:
            category = block.get("category", "Другое")
            
            # Проверяем соответствие фильтру категории
            if selected_category != "Все" and category != selected_category:
                continue
            
            # Проверяем соответствие поиску
            if search_text and search_text not in block["label"].lower() and search_text not in block.get("description", "").lower():
                continue
            
            if category not in categories:
                categories[category] = []
            categories[category].append(block)
        
        # Отображаем блоки по категориям
        row = 0
        for category, blocks in sorted(categories.items()):
            # Заголовок категории
            category_frame = ttk.Frame(self.blocks_frame_inner, style="Category.TFrame")
            category_frame.grid(row=row, column=0, sticky="ew", pady=(5, 0))
            self.blocks_frame_inner.columnconfigure(0, weight=1)
            
            ttk.Label(category_frame, text=category, style="Category.TLabel").pack(anchor="w", padx=5, pady=2)
            row += 1
            
            # Блоки в категории
            for block in blocks:
                block_frame = ttk.Frame(self.blocks_frame_inner)
                block_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=2)
                
                var = tk.BooleanVar(value=False)
                if block["key"] in self.block_vars:
                    var.set(self.block_vars[block["key"]].get())
                
                chk = ttk.Checkbutton(block_frame, text=block["label"], variable=var, 
                                     command=lambda k=block["key"], v=var: self.toggle_block(k, v))
                chk.pack(side=tk.LEFT, padx=2)
                
                if "description" in block:
                    info_btn = ttk.Button(block_frame, text="?", width=2, 
                                         command=lambda desc=block["description"], label=block["label"]: 
                                         self.show_block_info(label, desc))
                    info_btn.pack(side=tk.RIGHT, padx=2)
                
                self.block_vars[block["key"]] = var
                row += 1
    
    def toggle_block(self, key, var):
        """Обработчик переключения блока"""
        self.block_vars[key] = var
        self.render_param_fields()
    
    def show_block_info(self, title, description):
        """Показывает информацию о блоке"""
        info_window = tk.Toplevel(self)
        info_window.title(f"Информация: {title}")
        info_window.geometry("400x200")
        info_window.resizable(False, False)
        info_window.transient(self)
        info_window.grab_set()
        
        ttk.Label(info_window, text=title, font=("Segoe UI", 12, "bold")).pack(pady=(10, 5))
        ttk.Label(info_window, text=description, wraplength=380).pack(pady=5, padx=10)
        
        ttk.Button(info_window, text="Закрыть", command=info_window.destroy).pack(pady=10)
    
    def render_param_fields(self):
        """Отображает параметры выбранных блоков"""
        # Удалить старые параметры
        for widget in self.param_frame_inner.winfo_children():
            widget.destroy()
        
        self.param_widgets.clear()
        self.block_param_vars.clear()
        
        # Проверяем, есть ли выбранные блоки
        has_selected = any(self.block_vars[block["key"]].get() for block in BLOCKS)
        
        if not has_selected:
            ttk.Label(self.param_frame_inner, text="Выберите модули слева для настройки параметров").grid(
                row=0, column=0, padx=10, pady=10)
            return
        
        # Отображаем параметры для каждого выбранного блока
        row = 0
        for block in BLOCKS:
            if self.block_vars[block["key"]].get():
                # Заголовок блока
                block_header = ttk.Frame(self.param_frame_inner)
                block_header.grid(row=row, column=0, columnspan=3, sticky="ew", pady=(10, 5))
                
                ttk.Label(block_header, text=block["label"], font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
                
                if "description" in block:
                    ttk.Button(block_header, text="?", width=2, 
                              command=lambda desc=block["description"], label=block["label"]: 
                              self.show_block_info(label, desc)).pack(side=tk.RIGHT)
                
                row += 1
                
                # Параметры блока
                for param in block["params"]:
                    lbl = ttk.Label(self.param_frame_inner, text=param["label"] + ":")
                    lbl.grid(row=row, column=0, sticky="e", padx=(10, 5), pady=2)
                    
                    if param["type"] == "int":
                        var = tk.IntVar(value=param["default"])
                        spin = ttk.Spinbox(self.param_frame_inner, from_=param.get("min", 1), 
                                          to=param.get("max", 9999), textvariable=var, width=10)
                        spin.grid(row=row, column=1, sticky="w", padx=5, pady=2)
                        self.block_param_vars[(block["key"], param["name"])] = var
                        self.param_widgets.extend([lbl, spin])
                    
                    elif param["type"] == "float":
                        var = tk.DoubleVar(value=param["default"])
                        step = param.get("step", 0.1)
                        spin = ttk.Spinbox(self.param_frame_inner, from_=param.get("min", 0.0), 
                                          to=param.get("max", 100.0), increment=step,
                                          textvariable=var, width=10)
                        spin.grid(row=row, column=1, sticky="w", padx=5, pady=2)
                        self.block_param_vars[(block["key"], param["name"])] = var
                        self.param_widgets.extend([lbl, spin])
                    
                    elif param["type"] == "bool":
                        var = tk.BooleanVar(value=param["default"])
                        chk = ttk.Checkbutton(self.param_frame_inner, variable=var)
                        chk.grid(row=row, column=1, sticky="w", padx=5, pady=2)
                        self.block_param_vars[(block["key"], param["name"])] = var
                        self.param_widgets.extend([lbl, chk])
                    
                    elif param["type"] == "color":
                        var = tk.StringVar(value=param["default"])
                        color_frame = ttk.Frame(self.param_frame_inner)
                        color_frame.grid(row=row, column=1, sticky="w", padx=5, pady=2)
                        
                        entry = ttk.Entry(color_frame, textvariable=var, width=15)
                        entry.pack(side=tk.LEFT, padx=(0, 5))
                        
                        color_btn = ttk.Button(color_frame, text="...", width=2, 
                                              command=lambda v=var: self.choose_color(v))
                        color_btn.pack(side=tk.LEFT)
                        
                        self.block_param_vars[(block["key"], param["name"])] = var
                        self.param_widgets.extend([lbl, entry, color_btn])
                    
                    elif param["type"] == "combo":
                        var = tk.StringVar(value=param.get("default", param["options"][0][1]))
                        combo = ttk.Combobox(self.param_frame_inner, textvariable=var, 
                                            values=[opt[1] for opt in param["options"]], 
                                            state="readonly", width=15)
                        combo.grid(row=row, column=1, sticky="w", padx=5, pady=2)
                        self.block_param_vars[(block["key"], param["name"])] = var
                        self.param_widgets.extend([lbl, combo])
                    
                    # Добавляем кнопку сброса для каждого параметра
                    reset_btn = ttk.Button(self.param_frame_inner, text="⟲", width=2,
                                         command=lambda p=param, v=var: self.reset_param(p, v))
                    reset_btn.grid(row=row, column=2, padx=5, pady=2)
                    self.param_widgets.append(reset_btn)
                    
                    row += 1
    
    def choose_color(self, var):
        """Открывает диалог выбора цвета"""
        color = colorchooser.askcolor(title="Выберите цвет")
        if color[1]:  # Если цвет выбран
            # Преобразуем HEX в формат Pine Script
            r, g, b = [int(color[0][i]) for i in range(3)]
            var.set(f"color.rgb({r}, {g}, {b})")
    
    def reset_param(self, param, var):
        """Сбрасывает параметр к значению по умолчанию"""
        var.set(param["default"])

    def get_selected_blocks(self):
        """Получает список выбранных блоков с их параметрами"""
        selected = []
        for block in BLOCKS:
            if block["key"] in self.block_vars and self.block_vars[block["key"]].get():
                # Собираем параметры
                params = []
                for param in block["params"]:
                    var = self.block_param_vars.get((block["key"], param["name"]))
                    val = var.get() if var is not None else param.get("default")
                    param_copy = param.copy()
                    param_copy["value"] = val
                    params.append(param_copy)
                block_copy = block.copy()
                block_copy["params"] = params
                selected.append(block_copy)
        return selected
    
    def setup_syntax_highlighting(self):
        """Настраивает подсветку синтаксиса для редактора"""
        # Определяем теги для подсветки
        self.text_editor.tag_configure("keyword", foreground="#0000FF")
        self.text_editor.tag_configure("function", foreground="#7D26CD")
        self.text_editor.tag_configure("string", foreground="#008000")
        self.text_editor.tag_configure("comment", foreground="#808080", font=("Consolas", 10, "italic"))
        self.text_editor.tag_configure("number", foreground="#FF8000")
        
        # Привязываем обработчик изменения текста
        self.text_editor.bind("<KeyRelease>", self.highlight_syntax)
    
    def highlight_syntax(self, event=None):
        """Подсвечивает синтаксис в редакторе"""
        # Очищаем все теги
        for tag in ["keyword", "function", "string", "comment", "number"]:
            self.text_editor.tag_remove(tag, "1.0", "end")
        
        # Ключевые слова Pine Script
        keywords = ["var", "varip", "if", "else", "for", "to", "by", "while", "and", "or", "not", 
                   "true", "false", "na", "input", "study", "strategy", "plot", "plotshape", 
                   "plotarrow", "plotbar", "plotcandle", "fill", "bgcolor", "barcolor", "line", 
                   "hline", "vline", "box", "indicator", "overlay"]
        
        # Функции Pine Script
        functions = ["ta.sma", "ta.ema", "ta.rsi", "ta.macd", "ta.stoch", "ta.bbands", "ta.atr", 
                    "ta.crossover", "ta.crossunder", "math.abs", "math.log", "math.max", "math.min", 
                    "math.round", "math.sign", "math.sqrt", "array.new_float", "array.get", "array.set"]
        
        # Подсветка ключевых слов
        for keyword in keywords:
            start = "1.0"
            while True:
                start = self.text_editor.search(r'\y' + keyword + r'\y', start, "end", regexp=True)
                if not start:
                    break
                end = f"{start}+{len(keyword)}c"
                self.text_editor.tag_add("keyword", start, end)
                start = end
        
        # Подсветка функций
        for function in functions:
            start = "1.0"
            while True:
                start = self.text_editor.search(function, start, "end")
                if not start:
                    break
                end = f"{start}+{len(function)}c"
                self.text_editor.tag_add("function", start, end)
                start = end
        
        # Подсветка строк
        start = "1.0"
        while True:
            start = self.text_editor.search(r'"[^"]*"', start, "end", regexp=True)
            if not start:
                break
            content = self.text_editor.get(start, "end")
            match_length = content.find('"', 1) + 1
            end = f"{start}+{match_length}c"
            self.text_editor.tag_add("string", start, end)
            start = end
        
        # Подсветка комментариев
        start = "1.0"
        while True:
            start = self.text_editor.search(r'//.*

    def generate_and_test(self):
        selected_blocks = self.get_selected_blocks()
        code = self.generate_full_pine_script(selected_blocks)
        # Простая проверка синтаксиса
        errors = []
        if "//@version=5" not in code:
            errors.append("Нет //@version=5")
        if "indicator(" not in code:
            errors.append("Нет вызова indicator()")
        if "(" not in code or ")" not in code:
            errors.append("Нет скобок")
        if "plot" not in code and "box.new" not in code and "bgcolor" not in code:
            errors.append("Нет графических функций (plot, box.new, bgcolor)")
        if errors:
            messagebox.showerror("Ошибка синтаксиса", "\n".join(errors))
        else:
            messagebox.showinfo("Успех", "Скрипт успешно сгенерирован и прошёл базовую проверку!")
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("end", code)

    def generate_full_pine_script(self, selected_blocks):
        code = ["//@version=5"]
        code.append('indicator("Custom Combo", overlay=true, max_boxes_count=500, max_lines_count=500)')
        # INPUTS
        for block in selected_blocks:
            for p in block["params"]:
                v = p["value"]
                if p["type"] == "int":
                    code.append(f"{p['name']} = input.int({v}, '{p['label']}', minval={p.get('min', 1)}, maxval={p.get('max', 9999)})")
                elif p["type"] == "float":
                    code.append(f"{p['name']} = input.float({v}, '{p['label']}')")
                elif p["type"] == "bool":
                    code.append(f"{p['name']} = input.bool({str(v).lower()}, '{p['label']}')")
                elif p["type"] == "color":
                    code.append(f"{p['name']} = input.color({v}, '{p['label']}')")

        # Переменные, функции и plot для каждого блока (расширено)
        for block in selected_blocks:
            if block["key"] == "ema":
                code.append(f"ema_val = ta.ema(close, length)")
                code.append(f"plot(show ? ema_val : na, color=color, title='EMA')")
            elif block["key"] == "rsi":
                code.append(f"rsi_val = ta.rsi(close, length)")
                code.append(f"plot(show ? rsi_val : na, color=color.blue, title='RSI')")
                code.append(f"long_signal = rsi_val <= long_level")
                code.append(f"short_signal = rsi_val >= short_level")
                code.append(f"plotshape(long_signal, title='RSI Лонг', style=shape.labelup, location=location.belowbar, color=color.green)")
                code.append(f"plotshape(short_signal, title='RSI Шорт', style=shape.labeldown, location=location.abovebar, color=color.red)")
                code.append(f"alertcondition(long_signal, title='RSI Лонг сигнал', message='RSI достиг уровня лонга')")
                code.append(f"alertcondition(short_signal, title='RSI Шорт сигнал', message='RSI достиг уровня шорта')")
            elif block["key"] == "vpvr":
                code.append("// VPVR блок: для реального кода используйте готовые библиотеки или вставьте свой код VPVR")
                code.append("// Здесь только input и заглушка для VPVR")
            elif block["key"] == "macd":
                code.append(f"macd = ta.ema(close, macd_fast) - ta.ema(close, macd_slow)")
                code.append(f"signal = ta.ema(macd, macd_signal)")
                code.append(f"hist = macd - signal")
                code.append(f"plot(macd, color=color.blue, title='MACD')")
                code.append(f"plot(signal, color=color.orange, title='Signal')")
                code.append(f"plot(hist, color=color.green, style=plot.style_columns, title='Histogram')")
            elif block["key"] == "bb":
                code.append(f"basis = ta.sma(close, bb_length)")
                code.append(f"dev = bb_stddev * ta.stdev(close, bb_length)")
                code.append(f"upper = basis + dev")
                code.append(f"lower = basis - dev")
                code.append(f"plot(basis, color=color.blue)")
                code.append(f"plot(upper, color=color.red)")
                code.append(f"plot(lower, color=color.green)")
                code.append(f"fill(plot(upper), plot(lower), color=color.new(color.gray, 90))")
            elif block["key"] == "stoch":
                code.append(f"k = ta.stoch(close, high, low, stoch_k)")
                code.append(f"d = ta.sma(k, stoch_d)")
                code.append(f"plot(k, color=color.blue, title='K')")
                code.append(f"plot(d, color=color.orange, title='D')")
            elif block["key"] == "volume":
                code.append(f"plot(volume, color=color.blue, style=plot.style_columns)")
                code.append(f"plot(ta.sma(volume, vol_length), color=color.red)")
            elif block["key"] == "channel":
                code.append(f"upper = ta.highest(high, channel_length)")
                code.append(f"lower = ta.lowest(low, channel_length)")
                code.append(f"plot(upper, color=color.red)")
                code.append(f"plot(lower, color=color.green)")
            elif block["key"] == "ema_cross":
                code.append(f"fast = ta.ema(close, ema_cross_fast)")
                code.append(f"slow = ta.ema(close, ema_cross_slow)")
                code.append(f"plot(fast, color=color.blue)")
                code.append(f"plot(slow, color=color.orange)")
                code.append(f"alertcondition(ta.crossover(fast, slow), title='EMA Crossover', message='Fast EMA crossed above Slow EMA')")
            elif block["key"] == "arrow":
                code.append(
                    "plotshape(close > open, style=shape.triangleup, location=location.belowbar, color=color.green, size=size.small, title='Buy')"
                    if block["params"][0]["value"] == "buy"
                    else "plotshape(close < open, style=shape.triangledown, location=location.abovebar, color=color.red, size=size.small, title='Sell')"
                )
            elif block["key"] == "bgcolor":
                code.append(
                    "bgcolor(close > open ? color.new(color.green, 85) : na)"
                    if block["params"][0]["value"] == "buy"
                    else "bgcolor(close < open ? color.new(color.red, 85) : na)"
                )
            elif block["key"] == "box":
                code.append(f"box.new(bar_index-{block['params'][0]['value']}, high, bar_index, low, color=color.new(color.green, 80))")
            elif block["key"] == "cross":
                code.append(f"fast_ma = ta.sma(close, cross_fast)")
                code.append(f"slow_ma = ta.sma(close, cross_slow)")
                code.append(f"plot(fast_ma, color=color.blue)")
                code.append(f"plot(slow_ma, color=color.orange)")
                code.append(f"alertcondition(ta.crossover(fast_ma, slow_ma), title='Crossover', message='Fast MA crossed above Slow MA')")

        # Объединение сигналов (пример)
        if any(b["key"] == "rsi" for b in selected_blocks) and any(b["key"] == "ema" for b in selected_blocks):
            code.append("combo_long = long_signal and ema_val > close")
            code.append("combo_short = short_signal and ema_val < close")
            code.append("plotshape(combo_long, title='COMBO Лонг', style=shape.triangleup, location=location.belowbar, color=color.purple)")
            code.append("plotshape(combo_short, title='COMBO Шорт', style=shape.triangledown, location=location.abovebar, color=color.purple)")
            code.append("alertcondition(combo_long, title='COMBO Лонг', message='Совпадение RSI и EMA для лонга')")
            code.append("alertcondition(combo_short, title='COMBO Шорт', message='Совпадение RSI и EMA для шорта')")

        # Можно добавить объединение других сигналов, паттерны, фон, алерты и т.д.
        code.append("// ...дальнейшее развитие: объединение сигналов, сложные паттерны, пользовательские функции ...")
        return "\n".join(code)

    def save_script(self):
        code = self.text_editor.get("1.0", "end").strip()
        if not code:
            messagebox.showinfo("Пусто", "Нет кода для сохранения.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pine",
            filetypes=[("Pine Script", "*.pine"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)
                messagebox.showinfo("Успех", "Скрипт сохранён.")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def copy_to_clipboard(self):
        code = self.text_editor.get("1.0", "end").strip()
        if code:
            try:
                self.clipboard_clear()
                self.clipboard_append(code)
                self.update()  # Важно для Windows - обновляет буфер обмена
                messagebox.showinfo("Копирование", "Код скопирован в буфер обмена.")
            except Exception as e:
                # Альтернативный метод для Windows
                import subprocess
                subprocess.run(['clip'], input=code.encode('utf-8'), check=True)
                messagebox.showinfo("Копирование", "Код скопирован в буфер обмена.")
        else:
            messagebox.showinfo("Пусто", "Нет кода для копирования.")

    def clear_script(self):
        self.text_editor.delete("1.0", "end")

if __name__ == "__main__":
    app = PineSlicerApp()
    app.mainloop()
, start, "end", regexp=True)
            if not start:
                break
            line = int(start.split('.')[0])
            end = f"{line}.end"
            self.text_editor.tag_add("comment", start, end)
            start = f"{line+1}.0"
        
        # Подсветка чисел
        start = "1.0"
        while True:
            start = self.text_editor.search(r'\b\d+(\.\d+)?\b', start, "end", regexp=True)
            if not start:
                break
            content = self.text_editor.get(start, "end")
            match = content.split()[0]
            end = f"{start}+{len(match)}c"
            self.text_editor.tag_add("number", start, end)
            start = end
    
    def load_presets(self):
        """Загружает сохраненные пресеты"""
        presets = {}
        try:
            presets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets")
            if not os.path.exists(presets_dir):
                os.makedirs(presets_dir)
                
            for file in os.listdir(presets_dir):
                if file.endswith(".json"):
                    with open(os.path.join(presets_dir, file), "r") as f:
                        preset = json.load(f)
                        presets[preset["name"]] = preset
        except Exception as e:
            print(f"Ошибка загрузки пресетов: {e}")
        
        return presets
    
    def save_preset(self):
        """Сохраняет текущие настройки как пресет"""
        preset_name = self.preset_var.get().strip()
        if not preset_name:
            messagebox.showerror("Ошибка", "Введите имя пресета")
            return
        
        selected_blocks = self.get_selected_blocks()
        if not selected_blocks:
            messagebox.showerror("Ошибка", "Выберите хотя бы один модуль")
            return
        
        # Создаем объект пресета
        preset = {
            "name": preset_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "blocks": []
        }
        
        # Добавляем информацию о выбранных блоках
        for block in selected_blocks:
            block_data = {
                "key": block["key"],
                "params": {}
            }
            for param in block["params"]:
                block_data["params"][param["name"]] = param["value"]
            preset["blocks"].append(block_data)
        
        # Сохраняем пресет
        try:
            presets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets")
            if not os.path.exists(presets_dir):
                os.makedirs(presets_dir)
                
            filename = os.path.join(presets_dir, f"{preset_name.replace(' ', '_')}.json")
            with open(filename, "w") as f:
                json.dump(preset, f, indent=2)
            
            # Обновляем список пресетов
            self.presets[preset_name] = preset
            self.preset_combo["values"] = list(self.presets.keys())
            
            messagebox.showinfo("Успех", f"Пресет '{preset_name}' сохранен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить пресет: {e}")
    
    def load_preset(self):
        """Загружает выбранный пресет"""
        preset_name = self.preset_var.get()
        if not preset_name or preset_name not in self.presets:
            messagebox.showerror("Ошибка", "Выберите существующий пресет")
            return
        
        preset = self.presets[preset_name]
        
        # Сбрасываем все блоки
        for key in self.block_vars:
            self.block_vars[key].set(False)
        
        # Активируем блоки из пресета
        for block_data in preset["blocks"]:
            if block_data["key"] in self.block_vars:
                self.block_vars[block_data["key"]].set(True)
        
        # Обновляем параметры
        self.render_param_fields()
        
        # Устанавливаем значения параметров
        for block_data in preset["blocks"]:
            for param_name, param_value in block_data["params"].items():
                if (block_data["key"], param_name) in self.block_param_vars:
                    var = self.block_param_vars[(block_data["key"], param_name)]
                    var.set(param_value)
        
        self.status_var.set(f"Загружен пресет: {preset_name}")
        
        # Генерируем код
        self.generate_and_test()
    
    def save_last_session(self):
        """Сохраняет текущую сессию"""
        if not self.autosave_var.get():
            return
            
        selected_blocks = self.get_selected_blocks()
        if not selected_blocks:
            return
            
        # Создаем объект сессии
        session = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "blocks": []
        }
        
        # Добавляем информацию о выбранных блоках
        for block in selected_blocks:
            block_data = {
                "key": block["key"],
                "params": {}
            }
            for param in block["params"]:
                block_data["params"][param["name"]] = param["value"]
            session["blocks"].append(block_data)
        
        # Сохраняем сессию
        try:
            session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session")
            if not os.path.exists(session_dir):
                os.makedirs(session_dir)
                
            filename = os.path.join(session_dir, "last_session.json")
            with open(filename, "w") as f:
                json.dump(session, f, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения сессии: {e}")
    
    def load_last_session(self):
        """Загружает последнюю сессию"""
        try:
            session_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session", "last_session.json")
            if not os.path.exists(session_file):
                return
                
            with open(session_file, "r") as f:
                session = json.load(f)
            
            # Сбрасываем все блоки
            for key in self.block_vars:
                self.block_vars[key].set(False)
            
            # Активируем блоки из сессии
            for block_data in session["blocks"]:
                if block_data["key"] in self.block_vars:
                    self.block_vars[block_data["key"]].set(True)
            
            # Обновляем параметры
            self.render_param_fields()
            
            # Устанавливаем значения параметров
            for block_data in session["blocks"]:
                for param_name, param_value in block_data["params"].items():
                    if (block_data["key"], param_name) in self.block_param_vars:
                        var = self.block_param_vars[(block_data["key"], param_name)]
                        var.set(param_value)
            
            self.status_var.set(f"Загружена последняя сессия от {session['date']}")
            
            # Генерируем код
            self.generate_and_test()
        except Exception as e:
            print(f"Ошибка загрузки сессии: {e}")
    
    def change_font_size(self):
        """Изменяет размер шрифта в редакторе"""
        try:
            size = int(self.font_size_var.get())
            if 8 <= size <= 24:
                self.text_editor.configure(font=("Consolas", size))
        except ValueError:
            pass
    
    def change_theme(self):
        """Изменяет тему редактора"""
        theme = self.theme_var.get()
        if theme == "Тёмная":
            self.text_editor.configure(bg="#1e1e1e", fg="#d4d4d4", insertbackground="#d4d4d4")
            self.text_editor.tag_configure("keyword", foreground="#569cd6")
            self.text_editor.tag_configure("function", foreground="#dcdcaa")
            self.text_editor.tag_configure("string", foreground="#ce9178")
            self.text_editor.tag_configure("comment", foreground="#6a9955", font=("Consolas", 10, "italic"))
            self.text_editor.tag_configure("number", foreground="#b5cea8")
        else:
            self.text_editor.configure(bg="white", fg="black", insertbackground="black")
            self.text_editor.tag_configure("keyword", foreground="#0000FF")
            self.text_editor.tag_configure("function", foreground="#7D26CD")
            self.text_editor.tag_configure("string", foreground="#008000")
            self.text_editor.tag_configure("comment", foreground="#808080", font=("Consolas", 10, "italic"))
            self.text_editor.tag_configure("number", foreground="#FF8000")
    
    def save_settings(self):
        """Сохраняет настройки приложения"""
        settings = {
            "font_size": self.font_size_var.get(),
            "theme": self.theme_var.get(),
            "format_code": self.format_var.get(),
            "add_comments": self.comments_var.get(),
            "pine_version": self.version_var.get(),
            "autosave": self.autosave_var.get()
        }
        
        try:
            settings_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings")
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir)
                
            filename = os.path.join(settings_dir, "settings.json")
            with open(filename, "w") as f:
                json.dump(settings, f, indent=2)
            
            messagebox.showinfo("Успех", "Настройки сохранены")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")
    
    def reset_settings(self):
        """Сбрасывает настройки к значениям по умолчанию"""
        self.font_size_var.set("10")
        self.theme_var.set("Светлая")
        self.format_var.set(True)
        self.comments_var.set(True)
        self.version_var.set("5")
        self.autosave_var.set(True)
        
        self.change_font_size()
        self.change_theme()
        
        messagebox.showinfo("Успех", "Настройки сброшены к значениям по умолчанию")
    
    def update_preview(self):
        """Обновляет предпросмотр индикатора"""
        selected_blocks = self.get_selected_blocks()
        if not selected_blocks:
            messagebox.showinfo("Информация", "Выберите хотя бы один модуль для предпросмотра")
            return
        
        # Очищаем канвас
        self.preview_canvas.delete("all")
        
        # Рисуем базовый график
        width = self.preview_canvas.winfo_width()
        height = self.preview_canvas.winfo_height()
        
        # Если размеры еще не определены, используем значения по умолчанию
        if width < 10:
            width = 800
        if height < 10:
            height = 400
        
        # Рисуем оси
        self.preview_canvas.create_line(50, height-50, width-50, height-50, width=2)  # Ось X
        self.preview_canvas.create_line(50, 50, 50, height-50, width=2)  # Ось Y
        
        # Генерируем случайные данные для графика
        import random
        data_points = 100
        price_data = []
        volume_data = []
        
        # Начальная цена
        price = 100
        for i in range(data_points):
            # Случайное изменение цены
            change = random.uniform(-3, 3)
            price += change
            price = max(50, price)  # Цена не может быть меньше 50
            
            # Случайный объем
            volume = random.randint(100, 1000)
            
            price_data.append(price)
            volume_data.append(volume)
        
        # Находим минимум и максимум для масштабирования
        min_price = min(price_data)
        max_price = max(price_data)
        price_range = max_price - min_price
        
        # Рисуем свечи
        bar_width = (width - 100) / data_points
        for i in range(data_points):
            x = 50 + i * bar_width
            
            # Определяем, растущая или падающая свеча
            is_up = i > 0 and price_data[i] > price_data[i-1]
            
            # Высота свечи
            y = height - 50 - ((price_data[i] - min_price) / price_range) * (height - 100)
            
            # Рисуем свечу
            color = "green" if is_up else "red"
            self.preview_canvas.create_rectangle(x, y, x + bar_width - 1, height - 50, fill=color, outline="")
        
        # Рисуем индикаторы на основе выбранных блоков
        for block in selected_blocks:
            if block["key"] == "ema":
                # Рассчитываем EMA
                period = next((p["value"] for p in block["params"] if p["name"] == "length"), 21)
                ema_data = self.calculate_ema(price_data, period)
                
                # Рисуем EMA
                color = next((p["value"] for p in block["params"] if p["name"] == "color"), "blue")
                color = self.parse_pine_color(color)
                
                points = []
                for i in range(len(ema_data)):
                    x = 50 + i * bar_width + bar_width / 2
                    y = height - 50 - ((ema_data[i] - min_price) / price_range) * (height - 100)
                    points.extend([x, y])
                
                if points:
                    self.preview_canvas.create_line(points, fill=color, width=2, smooth=True)
            
            elif block["key"] == "sma":
                # Рассчитываем SMA
                period = next((p["value"] for p in block["params"] if p["name"] == "sma_length"), 50)
                sma_data = self.calculate_sma(price_data, period)
                
                # Рисуем SMA
                color = next((p["value"] for p in block["params"] if p["name"] == "sma_color"), "purple")
                color = self.parse_pine_color(color)
                
                points = []
                for i in range(len(sma_data)):
                    x = 50 + i * bar_width + bar_width / 2
                    y = height - 50 - ((sma_data[i] - min_price) / price_range) * (height - 100)
                    points.extend([x, y])
                
                if points:
                    self.preview_canvas.create_line(points, fill=color, width=2, smooth=True)
            
            elif block["key"] == "bb":
                # Рассчитываем Bollinger Bands
                period = next((p["value"] for p in block["params"] if p["name"] == "bb_length"), 20)
                stddev = next((p["value"] for p in block["params"] if p["name"] == "bb_stddev"), 2.0)
                
                sma_data = self.calculate_sma(price_data, period)
                upper_band = []
                lower_band = []
                
                for i in range(len(sma_data)):
                    if i >= period - 1:
                        # Рассчитываем стандартное отклонение
                        slice_data = price_data[i-(period-1):i+1]
                        std = self.calculate_stddev(slice_data)
                        
                        upper_band.append(sma_data[i] + stddev * std)
                        lower_band.append(sma_data[i] - stddev * std)
                    else:
                        upper_band.append(None)
                        lower_band.append(None)
                
                # Рисуем полосы Боллинджера
                upper_points = []
                middle_points = []
                lower_points = []
                
                for i in range(len(upper_band)):
                    if upper_band[i] is not None:
                        x = 50 + i * bar_width + bar_width / 2
                        
                        upper_y = height - 50 - ((upper_band[i] - min_price) / price_range) * (height - 100)
                        middle_y = height - 50 - ((sma_data[i] - min_price) / price_range) * (height - 100)
                        lower_y = height - 50 - ((lower_band[i] - min_price) / price_range) * (height - 100)
                        
                        upper_points.extend([x, upper_y])
                        middle_points.extend([x, middle_y])
                        lower_points.extend([x, lower_y])
                
                if upper_points and lower_points:
                    self.preview_canvas.create_line(upper_points, fill="red", width=2, smooth=True)
                    self.preview_canvas.create_line(middle_points, fill="blue", width=2, smooth=True)
                    self.preview_canvas.create_line(lower_points, fill="green", width=2, smooth=True)
        
        # Добавляем легенду
        legend_y = 20
        for block in selected_blocks:
            if block["key"] in ["ema", "sma", "bb"]:
                label = block["label"]
                color = "blue"
                if block["key"] == "ema":
                    color = self.parse_pine_color(next((p["value"] for p in block["params"] if p["name"] == "color"), "blue"))
                elif block["key"] == "sma":
                    color = self.parse_pine_color(next((p["value"] for p in block["params"] if p["name"] == "sma_color"), "purple"))
                
                self.preview_canvas.create_line(width-150, legend_y, width-100, legend_y, fill=color, width=2)
                self.preview_canvas.create_text(width-90, legend_y, text=label, anchor="w")
                legend_y += 20
        
        self.status_var.set("Предпросмотр обновлен")
    
    def calculate_ema(self, data, period):
        """Рассчитывает EMA для данных"""
        ema = []
        multiplier = 2 / (period + 1)
        
        # Первое значение - SMA
        sma = sum(data[:period]) / period
        ema.append(sma)
        
        # Рассчитываем EMA для остальных значений
        for i in range(1, len(data)):
            if i < period:
                ema.append(None)
            else:
                ema_value = (data[i] - ema[i-1]) * multiplier + ema[i-1]
                ema.append(ema_value)
        
        return ema
    
    def calculate_sma(self, data, period):
        """Рассчитывает SMA для данных"""
        sma = []
        
        for i in range(len(data)):
            if i < period - 1:
                sma.append(None)
            else:
                sma_value = sum(data[i-(period-1):i+1]) / period
                sma.append(sma_value)
        
        return sma
    
    def calculate_stddev(self, data):
        """Рассчитывает стандартное отклонение"""
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return variance ** 0.5
    
    def parse_pine_color(self, color_str):
        """Преобразует строку цвета Pine Script в цвет Tkinter"""
        if "color.rgb" in color_str:
            # Извлекаем RGB значения
            rgb = color_str.split("(")[1].split(")")[0].split(",")
            r, g, b = [int(x.strip()) for x in rgb]
            return f"#{r:02x}{g:02x}{b:02x}"
        elif "color.new" in color_str:
            # Извлекаем базовый цвет
            base_color = color_str.split("(")[1].split(",")[0].strip()
            return self.parse_pine_color(base_color)
        elif "color.red" in color_str:
            return "red"
        elif "color.green" in color_str:
            return "green"
        elif "color.blue" in color_str:
            return "blue"
        elif "color.yellow" in color_str:
            return "yellow"
        elif "color.orange" in color_str:
            return "orange"
        elif "color.purple" in color_str:
            return "purple"
        else:
            return "black"

    def generate_and_test(self):
        selected_blocks = self.get_selected_blocks()
        code = self.generate_full_pine_script(selected_blocks)
        # Простая проверка синтаксиса
        errors = []
        if "//@version=5" not in code:
            errors.append("Нет //@version=5")
        if "indicator(" not in code:
            errors.append("Нет вызова indicator()")
        if "(" not in code or ")" not in code:
            errors.append("Нет скобок")
        if "plot" not in code and "box.new" not in code and "bgcolor" not in code:
            errors.append("Нет графических функций (plot, box.new, bgcolor)")
        if errors:
            messagebox.showerror("Ошибка синтаксиса", "\n".join(errors))
        else:
            messagebox.showinfo("Успех", "Скрипт успешно сгенерирован и прошёл базовую проверку!")
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("end", code)

    def generate_full_pine_script(self, selected_blocks):
        code = ["//@version=5"]
        code.append('indicator("Custom Combo", overlay=true, max_boxes_count=500, max_lines_count=500)')
        # INPUTS
        for block in selected_blocks:
            for p in block["params"]:
                v = p["value"]
                if p["type"] == "int":
                    code.append(f"{p['name']} = input.int({v}, '{p['label']}', minval={p.get('min', 1)}, maxval={p.get('max', 9999)})")
                elif p["type"] == "float":
                    code.append(f"{p['name']} = input.float({v}, '{p['label']}')")
                elif p["type"] == "bool":
                    code.append(f"{p['name']} = input.bool({str(v).lower()}, '{p['label']}')")
                elif p["type"] == "color":
                    code.append(f"{p['name']} = input.color({v}, '{p['label']}')")

        # Переменные, функции и plot для каждого блока (расширено)
        for block in selected_blocks:
            if block["key"] == "ema":
                code.append(f"ema_val = ta.ema(close, length)")
                code.append(f"plot(show ? ema_val : na, color=color, title='EMA')")
            elif block["key"] == "rsi":
                code.append(f"rsi_val = ta.rsi(close, length)")
                code.append(f"plot(show ? rsi_val : na, color=color.blue, title='RSI')")
                code.append(f"long_signal = rsi_val <= long_level")
                code.append(f"short_signal = rsi_val >= short_level")
                code.append(f"plotshape(long_signal, title='RSI Лонг', style=shape.labelup, location=location.belowbar, color=color.green)")
                code.append(f"plotshape(short_signal, title='RSI Шорт', style=shape.labeldown, location=location.abovebar, color=color.red)")
                code.append(f"alertcondition(long_signal, title='RSI Лонг сигнал', message='RSI достиг уровня лонга')")
                code.append(f"alertcondition(short_signal, title='RSI Шорт сигнал', message='RSI достиг уровня шорта')")
            elif block["key"] == "vpvr":
                code.append("// VPVR блок: для реального кода используйте готовые библиотеки или вставьте свой код VPVR")
                code.append("// Здесь только input и заглушка для VPVR")
            elif block["key"] == "macd":
                code.append(f"macd = ta.ema(close, macd_fast) - ta.ema(close, macd_slow)")
                code.append(f"signal = ta.ema(macd, macd_signal)")
                code.append(f"hist = macd - signal")
                code.append(f"plot(macd, color=color.blue, title='MACD')")
                code.append(f"plot(signal, color=color.orange, title='Signal')")
                code.append(f"plot(hist, color=color.green, style=plot.style_columns, title='Histogram')")
            elif block["key"] == "bb":
                code.append(f"basis = ta.sma(close, bb_length)")
                code.append(f"dev = bb_stddev * ta.stdev(close, bb_length)")
                code.append(f"upper = basis + dev")
                code.append(f"lower = basis - dev")
                code.append(f"plot(basis, color=color.blue)")
                code.append(f"plot(upper, color=color.red)")
                code.append(f"plot(lower, color=color.green)")
                code.append(f"fill(plot(upper), plot(lower), color=color.new(color.gray, 90))")
            elif block["key"] == "stoch":
                code.append(f"k = ta.stoch(close, high, low, stoch_k)")
                code.append(f"d = ta.sma(k, stoch_d)")
                code.append(f"plot(k, color=color.blue, title='K')")
                code.append(f"plot(d, color=color.orange, title='D')")
            elif block["key"] == "volume":
                code.append(f"plot(volume, color=color.blue, style=plot.style_columns)")
                code.append(f"plot(ta.sma(volume, vol_length), color=color.red)")
            elif block["key"] == "channel":
                code.append(f"upper = ta.highest(high, channel_length)")
                code.append(f"lower = ta.lowest(low, channel_length)")
                code.append(f"plot(upper, color=color.red)")
                code.append(f"plot(lower, color=color.green)")
            elif block["key"] == "ema_cross":
                code.append(f"fast = ta.ema(close, ema_cross_fast)")
                code.append(f"slow = ta.ema(close, ema_cross_slow)")
                code.append(f"plot(fast, color=color.blue)")
                code.append(f"plot(slow, color=color.orange)")
                code.append(f"alertcondition(ta.crossover(fast, slow), title='EMA Crossover', message='Fast EMA crossed above Slow EMA')")
            elif block["key"] == "arrow":
                code.append(
                    "plotshape(close > open, style=shape.triangleup, location=location.belowbar, color=color.green, size=size.small, title='Buy')"
                    if block["params"][0]["value"] == "buy"
                    else "plotshape(close < open, style=shape.triangledown, location=location.abovebar, color=color.red, size=size.small, title='Sell')"
                )
            elif block["key"] == "bgcolor":
                code.append(
                    "bgcolor(close > open ? color.new(color.green, 85) : na)"
                    if block["params"][0]["value"] == "buy"
                    else "bgcolor(close < open ? color.new(color.red, 85) : na)"
                )
            elif block["key"] == "box":
                code.append(f"box.new(bar_index-{block['params'][0]['value']}, high, bar_index, low, color=color.new(color.green, 80))")
            elif block["key"] == "cross":
                code.append(f"fast_ma = ta.sma(close, cross_fast)")
                code.append(f"slow_ma = ta.sma(close, cross_slow)")
                code.append(f"plot(fast_ma, color=color.blue)")
                code.append(f"plot(slow_ma, color=color.orange)")
                code.append(f"alertcondition(ta.crossover(fast_ma, slow_ma), title='Crossover', message='Fast MA crossed above Slow MA')")

        # Объединение сигналов (пример)
        if any(b["key"] == "rsi" for b in selected_blocks) and any(b["key"] == "ema" for b in selected_blocks):
            code.append("combo_long = long_signal and ema_val > close")
            code.append("combo_short = short_signal and ema_val < close")
            code.append("plotshape(combo_long, title='COMBO Лонг', style=shape.triangleup, location=location.belowbar, color=color.purple)")
            code.append("plotshape(combo_short, title='COMBO Шорт', style=shape.triangledown, location=location.abovebar, color=color.purple)")
            code.append("alertcondition(combo_long, title='COMBO Лонг', message='Совпадение RSI и EMA для лонга')")
            code.append("alertcondition(combo_short, title='COMBO Шорт', message='Совпадение RSI и EMA для шорта')")

        # Можно добавить объединение других сигналов, паттерны, фон, алерты и т.д.
        code.append("// ...дальнейшее развитие: объединение сигналов, сложные паттерны, пользовательские функции ...")
        return "\n".join(code)

    def save_script(self):
        code = self.text_editor.get("1.0", "end").strip()
        if not code:
            messagebox.showinfo("Пусто", "Нет кода для сохранения.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pine",
            filetypes=[("Pine Script", "*.pine"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)
                messagebox.showinfo("Успех", "Скрипт сохранён.")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def copy_to_clipboard(self):
        code = self.text_editor.get("1.0", "end").strip()
        if code:
            try:
                self.clipboard_clear()
                self.clipboard_append(code)
                self.update()  # Важно для Windows - обновляет буфер обмена
                messagebox.showinfo("Копирование", "Код скопирован в буфер обмена.")
            except Exception as e:
                # Альтернативный метод для Windows
                import subprocess
                subprocess.run(['clip'], input=code.encode('utf-8'), check=True)
                messagebox.showinfo("Копирование", "Код скопирован в буфер обмена.")
        else:
            messagebox.showinfo("Пусто", "Нет кода для копирования.")

    def clear_script(self):
        self.text_editor.delete("1.0", "end")

if __name__ == "__main__":
    app = PineSlicerApp()
    app.mainloop()
, start, "end", regexp=True)
            if not start:
                break
            line = int(start.split('.')[0])
            end = f"{line}.end"
            self.text_editor.tag_add("comment", start, end)
            start = f"{line+1}.0"

    def generate_and_test(self):
        selected_blocks = self.get_selected_blocks()
        code = self.generate_full_pine_script(selected_blocks)
        # Простая проверка синтаксиса
        errors = []
        if "//@version=5" not in code:
            errors.append("Нет //@version=5")
        if "indicator(" not in code:
            errors.append("Нет вызова indicator()")
        if "(" not in code or ")" not in code:
            errors.append("Нет скобок")
        if "plot" not in code and "box.new" not in code and "bgcolor" not in code:
            errors.append("Нет графических функций (plot, box.new, bgcolor)")
        if errors:
            messagebox.showerror("Ошибка синтаксиса", "\n".join(errors))
        else:
            messagebox.showinfo("Успех", "Скрипт успешно сгенерирован и прошёл базовую проверку!")
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("end", code)

    def generate_full_pine_script(self, selected_blocks):
        code = ["//@version=5"]
        code.append('indicator("Custom Combo", overlay=true, max_boxes_count=500, max_lines_count=500)')
        # INPUTS
        for block in selected_blocks:
            for p in block["params"]:
                v = p["value"]
                if p["type"] == "int":
                    code.append(f"{p['name']} = input.int({v}, '{p['label']}', minval={p.get('min', 1)}, maxval={p.get('max', 9999)})")
                elif p["type"] == "float":
                    code.append(f"{p['name']} = input.float({v}, '{p['label']}')")
                elif p["type"] == "bool":
                    code.append(f"{p['name']} = input.bool({str(v).lower()}, '{p['label']}')")
                elif p["type"] == "color":
                    code.append(f"{p['name']} = input.color({v}, '{p['label']}')")

        # Переменные, функции и plot для каждого блока (расширено)
        for block in selected_blocks:
            if block["key"] == "ema":
                code.append(f"ema_val = ta.ema(close, length)")
                code.append(f"plot(show ? ema_val : na, color=color, title='EMA')")
            elif block["key"] == "rsi":
                code.append(f"rsi_val = ta.rsi(close, length)")
                code.append(f"plot(show ? rsi_val : na, color=color.blue, title='RSI')")
                code.append(f"long_signal = rsi_val <= long_level")
                code.append(f"short_signal = rsi_val >= short_level")
                code.append(f"plotshape(long_signal, title='RSI Лонг', style=shape.labelup, location=location.belowbar, color=color.green)")
                code.append(f"plotshape(short_signal, title='RSI Шорт', style=shape.labeldown, location=location.abovebar, color=color.red)")
                code.append(f"alertcondition(long_signal, title='RSI Лонг сигнал', message='RSI достиг уровня лонга')")
                code.append(f"alertcondition(short_signal, title='RSI Шорт сигнал', message='RSI достиг уровня шорта')")
            elif block["key"] == "vpvr":
                code.append("// VPVR блок: для реального кода используйте готовые библиотеки или вставьте свой код VPVR")
                code.append("// Здесь только input и заглушка для VPVR")
            elif block["key"] == "macd":
                code.append(f"macd = ta.ema(close, macd_fast) - ta.ema(close, macd_slow)")
                code.append(f"signal = ta.ema(macd, macd_signal)")
                code.append(f"hist = macd - signal")
                code.append(f"plot(macd, color=color.blue, title='MACD')")
                code.append(f"plot(signal, color=color.orange, title='Signal')")
                code.append(f"plot(hist, color=color.green, style=plot.style_columns, title='Histogram')")
            elif block["key"] == "bb":
                code.append(f"basis = ta.sma(close, bb_length)")
                code.append(f"dev = bb_stddev * ta.stdev(close, bb_length)")
                code.append(f"upper = basis + dev")
                code.append(f"lower = basis - dev")
                code.append(f"plot(basis, color=color.blue)")
                code.append(f"plot(upper, color=color.red)")
                code.append(f"plot(lower, color=color.green)")
                code.append(f"fill(plot(upper), plot(lower), color=color.new(color.gray, 90))")
            elif block["key"] == "stoch":
                code.append(f"k = ta.stoch(close, high, low, stoch_k)")
                code.append(f"d = ta.sma(k, stoch_d)")
                code.append(f"plot(k, color=color.blue, title='K')")
                code.append(f"plot(d, color=color.orange, title='D')")
            elif block["key"] == "volume":
                code.append(f"plot(volume, color=color.blue, style=plot.style_columns)")
                code.append(f"plot(ta.sma(volume, vol_length), color=color.red)")
            elif block["key"] == "channel":
                code.append(f"upper = ta.highest(high, channel_length)")
                code.append(f"lower = ta.lowest(low, channel_length)")
                code.append(f"plot(upper, color=color.red)")
                code.append(f"plot(lower, color=color.green)")
            elif block["key"] == "ema_cross":
                code.append(f"fast = ta.ema(close, ema_cross_fast)")
                code.append(f"slow = ta.ema(close, ema_cross_slow)")
                code.append(f"plot(fast, color=color.blue)")
                code.append(f"plot(slow, color=color.orange)")
                code.append(f"alertcondition(ta.crossover(fast, slow), title='EMA Crossover', message='Fast EMA crossed above Slow EMA')")
            elif block["key"] == "arrow":
                code.append(
                    "plotshape(close > open, style=shape.triangleup, location=location.belowbar, color=color.green, size=size.small, title='Buy')"
                    if block["params"][0]["value"] == "buy"
                    else "plotshape(close < open, style=shape.triangledown, location=location.abovebar, color=color.red, size=size.small, title='Sell')"
                )
            elif block["key"] == "bgcolor":
                code.append(
                    "bgcolor(close > open ? color.new(color.green, 85) : na)"
                    if block["params"][0]["value"] == "buy"
                    else "bgcolor(close < open ? color.new(color.red, 85) : na)"
                )
            elif block["key"] == "box":
                code.append(f"box.new(bar_index-{block['params'][0]['value']}, high, bar_index, low, color=color.new(color.green, 80))")
            elif block["key"] == "cross":
                code.append(f"fast_ma = ta.sma(close, cross_fast)")
                code.append(f"slow_ma = ta.sma(close, cross_slow)")
                code.append(f"plot(fast_ma, color=color.blue)")
                code.append(f"plot(slow_ma, color=color.orange)")
                code.append(f"alertcondition(ta.crossover(fast_ma, slow_ma), title='Crossover', message='Fast MA crossed above Slow MA')")

        # Объединение сигналов (пример)
        if any(b["key"] == "rsi" for b in selected_blocks) and any(b["key"] == "ema" for b in selected_blocks):
            code.append("combo_long = long_signal and ema_val > close")
            code.append("combo_short = short_signal and ema_val < close")
            code.append("plotshape(combo_long, title='COMBO Лонг', style=shape.triangleup, location=location.belowbar, color=color.purple)")
            code.append("plotshape(combo_short, title='COMBO Шорт', style=shape.triangledown, location=location.abovebar, color=color.purple)")
            code.append("alertcondition(combo_long, title='COMBO Лонг', message='Совпадение RSI и EMA для лонга')")
            code.append("alertcondition(combo_short, title='COMBO Шорт', message='Совпадение RSI и EMA для шорта')")

        # Можно добавить объединение других сигналов, паттерны, фон, алерты и т.д.
        code.append("// ...дальнейшее развитие: объединение сигналов, сложные паттерны, пользовательские функции ...")
        return "\n".join(code)

    def save_script(self):
        code = self.text_editor.get("1.0", "end").strip()
        if not code:
            messagebox.showinfo("Пусто", "Нет кода для сохранения.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pine",
            filetypes=[("Pine Script", "*.pine"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)
                messagebox.showinfo("Успех", "Скрипт сохранён.")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def copy_to_clipboard(self):
        code = self.text_editor.get("1.0", "end").strip()
        if code:
            try:
                self.clipboard_clear()
                self.clipboard_append(code)
                self.update()  # Важно для Windows - обновляет буфер обмена
                messagebox.showinfo("Копирование", "Код скопирован в буфер обмена.")
            except Exception as e:
                # Альтернативный метод для Windows
                import subprocess
                subprocess.run(['clip'], input=code.encode('utf-8'), check=True)
                messagebox.showinfo("Копирование", "Код скопирован в буфер обмена.")
        else:
            messagebox.showinfo("Пусто", "Нет кода для копирования.")

    def clear_script(self):
        self.text_editor.delete("1.0", "end")

if __name__ == "__main__":
    app = PineSlicerApp()
    app.mainloop()
, start, "end", regexp=True)
            if not start:
                break
            line = int(start.split('.')[0])
            end = f"{line}.end"
            self.text_editor.tag_add("comment", start, end)
            start = f"{line+1}.0"
        
        # Подсветка чисел
        start = "1.0"
        while True:
            start = self.text_editor.search(r'\b\d+(\.\d+)?\b', start, "end", regexp=True)
            if not start:
                break
            content = self.text_editor.get(start, "end")
            match = content.split()[0]
            end = f"{start}+{len(match)}c"
            self.text_editor.tag_add("number", start, end)
            start = end
    
    def load_presets(self):
        """Загружает сохраненные пресеты"""
        presets = {}
        try:
            presets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets")
            if not os.path.exists(presets_dir):
                os.makedirs(presets_dir)
                
            for file in os.listdir(presets_dir):
                if file.endswith(".json"):
                    with open(os.path.join(presets_dir, file), "r") as f:
                        preset = json.load(f)
                        presets[preset["name"]] = preset
        except Exception as e:
            print(f"Ошибка загрузки пресетов: {e}")
        
        return presets
    
    def save_preset(self):
        """Сохраняет текущие настройки как пресет"""
        preset_name = self.preset_var.get().strip()
        if not preset_name:
            messagebox.showerror("Ошибка", "Введите имя пресета")
            return
        
        selected_blocks = self.get_selected_blocks()
        if not selected_blocks:
            messagebox.showerror("Ошибка", "Выберите хотя бы один модуль")
            return
        
        # Создаем объект пресета
        preset = {
            "name": preset_name,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "blocks": []
        }
        
        # Добавляем информацию о выбранных блоках
        for block in selected_blocks:
            block_data = {
                "key": block["key"],
                "params": {}
            }
            for param in block["params"]:
                block_data["params"][param["name"]] = param["value"]
            preset["blocks"].append(block_data)
        
        # Сохраняем пресет
        try:
            presets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "presets")
            if not os.path.exists(presets_dir):
                os.makedirs(presets_dir)
                
            filename = os.path.join(presets_dir, f"{preset_name.replace(' ', '_')}.json")
            with open(filename, "w") as f:
                json.dump(preset, f, indent=2)
            
            # Обновляем список пресетов
            self.presets[preset_name] = preset
            self.preset_combo["values"] = list(self.presets.keys())
            
            messagebox.showinfo("Успех", f"Пресет '{preset_name}' сохранен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить пресет: {e}")
    
    def load_preset(self):
        """Загружает выбранный пресет"""
        preset_name = self.preset_var.get()
        if not preset_name or preset_name not in self.presets:
            messagebox.showerror("Ошибка", "Выберите существующий пресет")
            return
        
        preset = self.presets[preset_name]
        
        # Сбрасываем все блоки
        for key in self.block_vars:
            self.block_vars[key].set(False)
        
        # Активируем блоки из пресета
        for block_data in preset["blocks"]:
            if block_data["key"] in self.block_vars:
                self.block_vars[block_data["key"]].set(True)
        
        # Обновляем параметры
        self.render_param_fields()
        
        # Устанавливаем значения параметров
        for block_data in preset["blocks"]:
            for param_name, param_value in block_data["params"].items():
                if (block_data["key"], param_name) in self.block_param_vars:
                    var = self.block_param_vars[(block_data["key"], param_name)]
                    var.set(param_value)
        
        self.status_var.set(f"Загружен пресет: {preset_name}")
        
        # Генерируем код
        self.generate_and_test()
    
    def save_last_session(self):
        """Сохраняет текущую сессию"""
        if not self.autosave_var.get():
            return
            
        selected_blocks = self.get_selected_blocks()
        if not selected_blocks:
            return
            
        # Создаем объект сессии
        session = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "blocks": []
        }
        
        # Добавляем информацию о выбранных блоках
        for block in selected_blocks:
            block_data = {
                "key": block["key"],
                "params": {}
            }
            for param in block["params"]:
                block_data["params"][param["name"]] = param["value"]
            session["blocks"].append(block_data)
        
        # Сохраняем сессию
        try:
            session_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session")
            if not os.path.exists(session_dir):
                os.makedirs(session_dir)
                
            filename = os.path.join(session_dir, "last_session.json")
            with open(filename, "w") as f:
                json.dump(session, f, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения сессии: {e}")
    
    def load_last_session(self):
        """Загружает последнюю сессию"""
        try:
            session_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session", "last_session.json")
            if not os.path.exists(session_file):
                return
                
            with open(session_file, "r") as f:
                session = json.load(f)
            
            # Сбрасываем все блоки
            for key in self.block_vars:
                self.block_vars[key].set(False)
            
            # Активируем блоки из сессии
            for block_data in session["blocks"]:
                if block_data["key"] in self.block_vars:
                    self.block_vars[block_data["key"]].set(True)
            
            # Обновляем параметры
            self.render_param_fields()
            
            # Устанавливаем значения параметров
            for block_data in session["blocks"]:
                for param_name, param_value in block_data["params"].items():
                    if (block_data["key"], param_name) in self.block_param_vars:
                        var = self.block_param_vars[(block_data["key"], param_name)]
                        var.set(param_value)
            
            self.status_var.set(f"Загружена последняя сессия от {session['date']}")
            
            # Генерируем код
            self.generate_and_test()
        except Exception as e:
            print(f"Ошибка загрузки сессии: {e}")
    
    def change_font_size(self):
        """Изменяет размер шрифта в редакторе"""
        try:
            size = int(self.font_size_var.get())
            if 8 <= size <= 24:
                self.text_editor.configure(font=("Consolas", size))
        except ValueError:
            pass
    
    def change_theme(self):
        """Изменяет тему редактора"""
        theme = self.theme_var.get()
        if theme == "Тёмная":
            self.text_editor.configure(bg="#1e1e1e", fg="#d4d4d4", insertbackground="#d4d4d4")
            self.text_editor.tag_configure("keyword", foreground="#569cd6")
            self.text_editor.tag_configure("function", foreground="#dcdcaa")
            self.text_editor.tag_configure("string", foreground="#ce9178")
            self.text_editor.tag_configure("comment", foreground="#6a9955", font=("Consolas", 10, "italic"))
            self.text_editor.tag_configure("number", foreground="#b5cea8")
        else:
            self.text_editor.configure(bg="white", fg="black", insertbackground="black")
            self.text_editor.tag_configure("keyword", foreground="#0000FF")
            self.text_editor.tag_configure("function", foreground="#7D26CD")
            self.text_editor.tag_configure("string", foreground="#008000")
            self.text_editor.tag_configure("comment", foreground="#808080", font=("Consolas", 10, "italic"))
            self.text_editor.tag_configure("number", foreground="#FF8000")
    
    def save_settings(self):
        """Сохраняет настройки приложения"""
        settings = {
            "font_size": self.font_size_var.get(),
            "theme": self.theme_var.get(),
            "format_code": self.format_var.get(),
            "add_comments": self.comments_var.get(),
            "pine_version": self.version_var.get(),
            "autosave": self.autosave_var.get()
        }
        
        try:
            settings_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings")
            if not os.path.exists(settings_dir):
                os.makedirs(settings_dir)
                
            filename = os.path.join(settings_dir, "settings.json")
            with open(filename, "w") as f:
                json.dump(settings, f, indent=2)
            
            messagebox.showinfo("Успех", "Настройки сохранены")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")
    
    def reset_settings(self):
        """Сбрасывает настройки к значениям по умолчанию"""
        self.font_size_var.set("10")
        self.theme_var.set("Светлая")
        self.format_var.set(True)
        self.comments_var.set(True)
        self.version_var.set("5")
        self.autosave_var.set(True)
        
        self.change_font_size()
        self.change_theme()
        
        messagebox.showinfo("Успех", "Настройки сброшены к значениям по умолчанию")
    
    def update_preview(self):
        """Обновляет предпросмотр индикатора"""
        selected_blocks = self.get_selected_blocks()
        if not selected_blocks:
            messagebox.showinfo("Информация", "Выберите хотя бы один модуль для предпросмотра")
            return
        
        # Очищаем канвас
        self.preview_canvas.delete("all")
        
        # Рисуем базовый график
        width = self.preview_canvas.winfo_width()
        height = self.preview_canvas.winfo_height()
        
        # Если размеры еще не определены, используем значения по умолчанию
        if width < 10:
            width = 800
        if height < 10:
            height = 400
        
        # Рисуем оси
        self.preview_canvas.create_line(50, height-50, width-50, height-50, width=2)  # Ось X
        self.preview_canvas.create_line(50, 50, 50, height-50, width=2)  # Ось Y
        
        # Генерируем случайные данные для графика
        import random
        data_points = 100
        price_data = []
        volume_data = []
        
        # Начальная цена
        price = 100
        for i in range(data_points):
            # Случайное изменение цены
            change = random.uniform(-3, 3)
            price += change
            price = max(50, price)  # Цена не может быть меньше 50
            
            # Случайный объем
            volume = random.randint(100, 1000)
            
            price_data.append(price)
            volume_data.append(volume)
        
        # Находим минимум и максимум для масштабирования
        min_price = min(price_data)
        max_price = max(price_data)
        price_range = max_price - min_price
        
        # Рисуем свечи
        bar_width = (width - 100) / data_points
        for i in range(data_points):
            x = 50 + i * bar_width
            
            # Определяем, растущая или падающая свеча
            is_up = i > 0 and price_data[i] > price_data[i-1]
            
            # Высота свечи
            y = height - 50 - ((price_data[i] - min_price) / price_range) * (height - 100)
            
            # Рисуем свечу
            color = "green" if is_up else "red"
            self.preview_canvas.create_rectangle(x, y, x + bar_width - 1, height - 50, fill=color, outline="")
        
        # Рисуем индикаторы на основе выбранных блоков
        for block in selected_blocks:
            if block["key"] == "ema":
                # Рассчитываем EMA
                period = next((p["value"] for p in block["params"] if p["name"] == "length"), 21)
                ema_data = self.calculate_ema(price_data, period)
                
                # Рисуем EMA
                color = next((p["value"] for p in block["params"] if p["name"] == "color"), "blue")
                color = self.parse_pine_color(color)
                
                points = []
                for i in range(len(ema_data)):
                    x = 50 + i * bar_width + bar_width / 2
                    y = height - 50 - ((ema_data[i] - min_price) / price_range) * (height - 100)
                    points.extend([x, y])
                
                if points:
                    self.preview_canvas.create_line(points, fill=color, width=2, smooth=True)
            
            elif block["key"] == "sma":
                # Рассчитываем SMA
                period = next((p["value"] for p in block["params"] if p["name"] == "sma_length"), 50)
                sma_data = self.calculate_sma(price_data, period)
                
                # Рисуем SMA
                color = next((p["value"] for p in block["params"] if p["name"] == "sma_color"), "purple")
                color = self.parse_pine_color(color)
                
                points = []
                for i in range(len(sma_data)):
                    x = 50 + i * bar_width + bar_width / 2
                    y = height - 50 - ((sma_data[i] - min_price) / price_range) * (height - 100)
                    points.extend([x, y])
                
                if points:
                    self.preview_canvas.create_line(points, fill=color, width=2, smooth=True)
            
            elif block["key"] == "bb":
                # Рассчитываем Bollinger Bands
                period = next((p["value"] for p in block["params"] if p["name"] == "bb_length"), 20)
                stddev = next((p["value"] for p in block["params"] if p["name"] == "bb_stddev"), 2.0)
                
                sma_data = self.calculate_sma(price_data, period)
                upper_band = []
                lower_band = []
                
                for i in range(len(sma_data)):
                    if i >= period - 1:
                        # Рассчитываем стандартное отклонение
                        slice_data = price_data[i-(period-1):i+1]
                        std = self.calculate_stddev(slice_data)
                        
                        upper_band.append(sma_data[i] + stddev * std)
                        lower_band.append(sma_data[i] - stddev * std)
                    else:
                        upper_band.append(None)
                        lower_band.append(None)
                
                # Рисуем полосы Боллинджера
                upper_points = []
                middle_points = []
                lower_points = []
                
                for i in range(len(upper_band)):
                    if upper_band[i] is not None:
                        x = 50 + i * bar_width + bar_width / 2
                        
                        upper_y = height - 50 - ((upper_band[i] - min_price) / price_range) * (height - 100)
                        middle_y = height - 50 - ((sma_data[i] - min_price) / price_range) * (height - 100)
                        lower_y = height - 50 - ((lower_band[i] - min_price) / price_range) * (height - 100)
                        
                        upper_points.extend([x, upper_y])
                        middle_points.extend([x, middle_y])
                        lower_points.extend([x, lower_y])
                
                if upper_points and lower_points:
                    self.preview_canvas.create_line(upper_points, fill="red", width=2, smooth=True)
                    self.preview_canvas.create_line(middle_points, fill="blue", width=2, smooth=True)
                    self.preview_canvas.create_line(lower_points, fill="green", width=2, smooth=True)
        
        # Добавляем легенду
        legend_y = 20
        for block in selected_blocks:
            if block["key"] in ["ema", "sma", "bb"]:
                label = block["label"]
                color = "blue"
                if block["key"] == "ema":
                    color = self.parse_pine_color(next((p["value"] for p in block["params"] if p["name"] == "color"), "blue"))
                elif block["key"] == "sma":
                    color = self.parse_pine_color(next((p["value"] for p in block["params"] if p["name"] == "sma_color"), "purple"))
                
                self.preview_canvas.create_line(width-150, legend_y, width-100, legend_y, fill=color, width=2)
                self.preview_canvas.create_text(width-90, legend_y, text=label, anchor="w")
                legend_y += 20
        
        self.status_var.set("Предпросмотр обновлен")
    
    def calculate_ema(self, data, period):
        """Рассчитывает EMA для данных"""
        ema = []
        multiplier = 2 / (period + 1)
        
        # Первое значение - SMA
        sma = sum(data[:period]) / period
        ema.append(sma)
        
        # Рассчитываем EMA для остальных значений
        for i in range(1, len(data)):
            if i < period:
                ema.append(None)
            else:
                ema_value = (data[i] - ema[i-1]) * multiplier + ema[i-1]
                ema.append(ema_value)
        
        return ema
    
    def calculate_sma(self, data, period):
        """Рассчитывает SMA для данных"""
        sma = []
        
        for i in range(len(data)):
            if i < period - 1:
                sma.append(None)
            else:
                sma_value = sum(data[i-(period-1):i+1]) / period
                sma.append(sma_value)
        
        return sma
    
    def calculate_stddev(self, data):
        """Рассчитывает стандартное отклонение"""
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return variance ** 0.5
    
    def parse_pine_color(self, color_str):
        """Преобразует строку цвета Pine Script в цвет Tkinter"""
        if "color.rgb" in color_str:
            # Извлекаем RGB значения
            rgb = color_str.split("(")[1].split(")")[0].split(",")
            r, g, b = [int(x.strip()) for x in rgb]
            return f"#{r:02x}{g:02x}{b:02x}"
        elif "color.new" in color_str:
            # Извлекаем базовый цвет
            base_color = color_str.split("(")[1].split(",")[0].strip()
            return self.parse_pine_color(base_color)
        elif "color.red" in color_str:
            return "red"
        elif "color.green" in color_str:
            return "green"
        elif "color.blue" in color_str:
            return "blue"
        elif "color.yellow" in color_str:
            return "yellow"
        elif "color.orange" in color_str:
            return "orange"
        elif "color.purple" in color_str:
            return "purple"
        else:
            return "black"

    def generate_and_test(self):
        selected_blocks = self.get_selected_blocks()
        code = self.generate_full_pine_script(selected_blocks)
        # Простая проверка синтаксиса
        errors = []
        if "//@version=5" not in code:
            errors.append("Нет //@version=5")
        if "indicator(" not in code:
            errors.append("Нет вызова indicator()")
        if "(" not in code or ")" not in code:
            errors.append("Нет скобок")
        if "plot" not in code and "box.new" not in code and "bgcolor" not in code:
            errors.append("Нет графических функций (plot, box.new, bgcolor)")
        if errors:
            messagebox.showerror("Ошибка синтаксиса", "\n".join(errors))
        else:
            messagebox.showinfo("Успех", "Скрипт успешно сгенерирован и прошёл базовую проверку!")
        self.text_editor.delete("1.0", "end")
        self.text_editor.insert("end", code)

    def generate_full_pine_script(self, selected_blocks):
        code = ["//@version=5"]
        code.append('indicator("Custom Combo", overlay=true, max_boxes_count=500, max_lines_count=500)')
        # INPUTS
        for block in selected_blocks:
            for p in block["params"]:
                v = p["value"]
                if p["type"] == "int":
                    code.append(f"{p['name']} = input.int({v}, '{p['label']}', minval={p.get('min', 1)}, maxval={p.get('max', 9999)})")
                elif p["type"] == "float":
                    code.append(f"{p['name']} = input.float({v}, '{p['label']}')")
                elif p["type"] == "bool":
                    code.append(f"{p['name']} = input.bool({str(v).lower()}, '{p['label']}')")
                elif p["type"] == "color":
                    code.append(f"{p['name']} = input.color({v}, '{p['label']}')")

        # Переменные, функции и plot для каждого блока (расширено)
        for block in selected_blocks:
            if block["key"] == "ema":
                code.append(f"ema_val = ta.ema(close, length)")
                code.append(f"plot(show ? ema_val : na, color=color, title='EMA')")
            elif block["key"] == "rsi":
                code.append(f"rsi_val = ta.rsi(close, length)")
                code.append(f"plot(show ? rsi_val : na, color=color.blue, title='RSI')")
                code.append(f"long_signal = rsi_val <= long_level")
                code.append(f"short_signal = rsi_val >= short_level")
                code.append(f"plotshape(long_signal, title='RSI Лонг', style=shape.labelup, location=location.belowbar, color=color.green)")
                code.append(f"plotshape(short_signal, title='RSI Шорт', style=shape.labeldown, location=location.abovebar, color=color.red)")
                code.append(f"alertcondition(long_signal, title='RSI Лонг сигнал', message='RSI достиг уровня лонга')")
                code.append(f"alertcondition(short_signal, title='RSI Шорт сигнал', message='RSI достиг уровня шорта')")
            elif block["key"] == "vpvr":
                code.append("// VPVR блок: для реального кода используйте готовые библиотеки или вставьте свой код VPVR")
                code.append("// Здесь только input и заглушка для VPVR")
            elif block["key"] == "macd":
                code.append(f"macd = ta.ema(close, macd_fast) - ta.ema(close, macd_slow)")
                code.append(f"signal = ta.ema(macd, macd_signal)")
                code.append(f"hist = macd - signal")
                code.append(f"plot(macd, color=color.blue, title='MACD')")
                code.append(f"plot(signal, color=color.orange, title='Signal')")
                code.append(f"plot(hist, color=color.green, style=plot.style_columns, title='Histogram')")
            elif block["key"] == "bb":
                code.append(f"basis = ta.sma(close, bb_length)")
                code.append(f"dev = bb_stddev * ta.stdev(close, bb_length)")
                code.append(f"upper = basis + dev")
                code.append(f"lower = basis - dev")
                code.append(f"plot(basis, color=color.blue)")
                code.append(f"plot(upper, color=color.red)")
                code.append(f"plot(lower, color=color.green)")
                code.append(f"fill(plot(upper), plot(lower), color=color.new(color.gray, 90))")
            elif block["key"] == "stoch":
                code.append(f"k = ta.stoch(close, high, low, stoch_k)")
                code.append(f"d = ta.sma(k, stoch_d)")
                code.append(f"plot(k, color=color.blue, title='K')")
                code.append(f"plot(d, color=color.orange, title='D')")
            elif block["key"] == "volume":
                code.append(f"plot(volume, color=color.blue, style=plot.style_columns)")
                code.append(f"plot(ta.sma(volume, vol_length), color=color.red)")
            elif block["key"] == "channel":
                code.append(f"upper = ta.highest(high, channel_length)")
                code.append(f"lower = ta.lowest(low, channel_length)")
                code.append(f"plot(upper, color=color.red)")
                code.append(f"plot(lower, color=color.green)")
            elif block["key"] == "ema_cross":
                code.append(f"fast = ta.ema(close, ema_cross_fast)")
                code.append(f"slow = ta.ema(close, ema_cross_slow)")
                code.append(f"plot(fast, color=color.blue)")
                code.append(f"plot(slow, color=color.orange)")
                code.append(f"alertcondition(ta.crossover(fast, slow), title='EMA Crossover', message='Fast EMA crossed above Slow EMA')")
            elif block["key"] == "arrow":
                code.append(
                    "plotshape(close > open, style=shape.triangleup, location=location.belowbar, color=color.green, size=size.small, title='Buy')"
                    if block["params"][0]["value"] == "buy"
                    else "plotshape(close < open, style=shape.triangledown, location=location.abovebar, color=color.red, size=size.small, title='Sell')"
                )
            elif block["key"] == "bgcolor":
                code.append(
                    "bgcolor(close > open ? color.new(color.green, 85) : na)"
                    if block["params"][0]["value"] == "buy"
                    else "bgcolor(close < open ? color.new(color.red, 85) : na)"
                )
            elif block["key"] == "box":
                code.append(f"box.new(bar_index-{block['params'][0]['value']}, high, bar_index, low, color=color.new(color.green, 80))")
            elif block["key"] == "cross":
                code.append(f"fast_ma = ta.sma(close, cross_fast)")
                code.append(f"slow_ma = ta.sma(close, cross_slow)")
                code.append(f"plot(fast_ma, color=color.blue)")
                code.append(f"plot(slow_ma, color=color.orange)")
                code.append(f"alertcondition(ta.crossover(fast_ma, slow_ma), title='Crossover', message='Fast MA crossed above Slow MA')")

        # Объединение сигналов (пример)
        if any(b["key"] == "rsi" for b in selected_blocks) and any(b["key"] == "ema" for b in selected_blocks):
            code.append("combo_long = long_signal and ema_val > close")
            code.append("combo_short = short_signal and ema_val < close")
            code.append("plotshape(combo_long, title='COMBO Лонг', style=shape.triangleup, location=location.belowbar, color=color.purple)")
            code.append("plotshape(combo_short, title='COMBO Шорт', style=shape.triangledown, location=location.abovebar, color=color.purple)")
            code.append("alertcondition(combo_long, title='COMBO Лонг', message='Совпадение RSI и EMA для лонга')")
            code.append("alertcondition(combo_short, title='COMBO Шорт', message='Совпадение RSI и EMA для шорта')")

        # Можно добавить объединение других сигналов, паттерны, фон, алерты и т.д.
        code.append("// ...дальнейшее развитие: объединение сигналов, сложные паттерны, пользовательские функции ...")
        return "\n".join(code)

    def save_script(self):
        code = self.text_editor.get("1.0", "end").strip()
        if not code:
            messagebox.showinfo("Пусто", "Нет кода для сохранения.")
            return
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pine",
            filetypes=[("Pine Script", "*.pine"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(code)
                messagebox.showinfo("Успех", "Скрипт сохранён.")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def copy_to_clipboard(self):
        code = self.text_editor.get("1.0", "end").strip()
        if code:
            try:
                self.clipboard_clear()
                self.clipboard_append(code)
                self.update()  # Важно для Windows - обновляет буфер обмена
                messagebox.showinfo("Копирование", "Код скопирован в буфер обмена.")
            except Exception as e:
                # Альтернативный метод для Windows
                import subprocess
                subprocess.run(['clip'], input=code.encode('utf-8'), check=True)
                messagebox.showinfo("Копирование", "Код скопирован в буфер обмена.")
        else:
            messagebox.showinfo("Пусто", "Нет кода для копирования.")

    def clear_script(self):
        self.text_editor.delete("1.0", "end")

if __name__ == "__main__":
    app = PineSlicerApp()
    app.mainloop()
