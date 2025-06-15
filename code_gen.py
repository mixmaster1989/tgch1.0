import autopep8
from utils import validate_code

def validate_code(code):
    errors = []
    # Проверка на наличие основных компонентов
    if "//@version=5" not in code:
        errors.append("Отсутствует версия Pine Script (//@version=5)")
    if "indicator(" not in code:
        errors.append("Отсутствует объявление индикатора (indicator)")
    # Проверка на наличие ошибок в параметрах
    for line in code.split("\n"):
        if "=" in line and "ta." in line:
            if "(" not in line or ")" not in line:
                errors.append(f"Ошибка в параметрах: {line}")
    return errors

def generate_code(blocks):
    """Генерация кода индикатора для TradingView"""
    code = []
    indent = 0
    
    # Добавляем заголовок
    code.append("//@version=5")
    code.append("indicator(\"My Indicator\", overlay=true)")
    code.append("")
    
    # Обрабатываем блоки
    for block in blocks:
        data = block.get_data()
        block_type = data["type"]
        params = data["params"]
        
        if block_type == "Индикатор":
            name = params.get("Название", "Custom Indicator")
            timeframe = params.get("Временной интервал", "1d")
            chart_type = params.get("Тип графика", "candle")
            
            code.append("// Основные настройки индикатора")
            for param_name, value in params.items():
                code.append(f"{param_name} = {value}")
            
            code.append(f"// Настройки индикатора")
            code.append(f"indicator(\"{name}\", overlay=true)")
            code.append(f"timeframe = \"{timeframe}\"")
            code.append(f"chart_type = \"{chart_type}\"")
            code.append("")
            
        elif block_type == "Скользящая средняя":
            source = params.get("Источник", "close")
            period = params.get("Период", "14")
            ma_type = params.get("Тип", "EMA")
            
            code.append("// Скользящая средняя")
            if ma_type == "SMA":
                code.append(f"ma = ta.sma({source}, {period})")
            elif ma_type == "EMA":
                code.append(f"ma = ta.ema({source}, {period})")
            elif ma_type == "WMA":
                code.append(f"ma = ta.wma({source}, {period})")
            elif ma_type == "VWMA":
                code.append(f"ma = ta.vwma({source}, {period})")
            code.append("plot(ma, color=color.blue, title=\"MA\")")
            code.append("")
            
        elif block_type == "RSI":
            period = params.get("Период", "14")
            source = params.get("Источник", "close")
            
            code.append("// RSI")
            code.append(f"rsi = ta.rsi({source}, {period})")
            code.append("plot(rsi, color=color.purple, title=\"RSI\")")
            code.append("")
            
        elif block_type == "MACD":
            fast_period = params.get("Быстрый период", "12")
            slow_period = params.get("Медленный период", "26")
            signal_period = params.get("Сигнальный период", "9")
            code.append("// MACD")
            code.append(f"macd_line = na\nsignal_line = na\nhist = na\n[macd_line, signal_line, hist] = ta.macd(close, {fast_period}, {slow_period}, {signal_period})")
            code.append("plot(macd_line, color=color.blue, title=\"MACD\")")
            code.append("plot(signal_line, color=color.red, title=\"Signal\")")
            code.append("plot(hist, color=color.green, title=\"Histogram\")")
            code.append("")
            
        elif block_type == "Bollinger Bands":
            period = params.get("Период", "20")
            multiplier = params.get("Множитель", "2.0")
            source = params.get("Источник", "close")
            code.append("// Полосы Боллинджера")
            code.append(f"middle = na\nupper = na\nlower = na\n[middle, upper, lower] = ta.bb({source}, {period}, {multiplier})")
            code.append("plot(middle, color=color.blue, title=\"Basis\")")
            code.append("plot(upper, color=color.red, title=\"Upper\")")
            code.append("plot(lower, color=color.green, title=\"Lower\")")
            code.append("")
            
        elif block_type == "Stochastic":
            k_period = params.get("Период K", "14")
            d_period = params.get("Период D", "3")
            slowing = params.get("Замедление", "3")
            
            code.append("// Стохастик")
            code.append(f"k = ta.stoch(close, high, low, {k_period})")
            code.append(f"d = ta.sma(k, {d_period})")
            code.append("plot(k, color=color.blue, title=\"%K\")")
            code.append("plot(d, color=color.red, title=\"%D\")")
            code.append("")
            
        elif block_type == "ATR":
            period = params.get("Период", "14")
            
            code.append("// ATR")
            code.append(f"atr = ta.atr({period})")
            code.append("plot(atr, color=color.blue, title=\"ATR\")")
            code.append("")
            
        elif block_type == "Импульс":
            period = params.get("Период", "14")
            source = params.get("Источник", "close")
            
            code.append("// Импульс")
            code.append(f"impulse = {source} - {source}[{period}]")
            code.append("plot(impulse, color=color.blue, title=\"Impulse\")")
            code.append("")
            
        elif block_type == "CCI":
            period = params.get("Период", "20")
            source = params.get("Источник", "hlc3")
            
            code.append("// CCI")
            code.append(f"cci = ta.cci({source}, {period})")
            code.append("plot(cci, color=color.blue, title=\"CCI\")")
            code.append("")
            
        elif block_type == "Условие":
            condition = params.get("Условие", "close > open")
            message = params.get("Сообщение", "Сигнал!")
            
            code.append("// Условие")
            code.append(f"if {condition}")
            code.append(f"    label.new(bar_index, high, \"{message}\", color=color.green)")
            code.append("")
            
        elif block_type == "Пересечение":
            line1 = params.get("Линия 1", "ma1")
            line2 = params.get("Линия 2", "ma2")
            message = params.get("Сообщение", "Пересечение!")
            
            code.append("// Пересечение")
            code.append(f"cross = ta.crossover({line1}, {line2})")
            code.append(f"if cross")
            code.append(f"    label.new(bar_index, high, \"{message}\", color=color.blue)")
            code.append("")
            
        elif block_type == "Уровень":
            value = params.get("Значение", "0")
            color = params.get("Цвет", "red")
            style = params.get("Стиль", "solid")
            
            code.append("// Уровень")
            code.append(f"hline({value}, \"Уровень {value}\", color=color.{color}, linestyle=hline.style_{style})")
            code.append("")
            
        elif block_type == "Объем":
            period = params.get("Период", "20")
            threshold = params.get("Порог", "2.0")
            
            code.append("// Объём")
            code.append(f"vol_ma = ta.sma(volume, {period})")
            code.append(f"if volume > vol_ma * {threshold}")
            code.append(f"    label.new(bar_index, high, \"Большой объём!\", color=color.purple)")
            code.append("plot(vol_ma, color=color.blue, title=\"Volume\")")
            code.append("")
            
        elif block_type == "Тренд":
            period = params.get("Период", "20")
            threshold = params.get("Порог", "2.0")
            
            code.append("// Тренд")
            code.append(f"ma = ta.sma(close, {period})")
            code.append(f"if math.abs(close - ma) > ma * {threshold} / 100")
            code.append(f"    label.new(bar_index, high, \"Сильный тренд!\", color=color.orange)")
            code.append("plot(ma, color=color.blue, title=\"Trend\")")
            code.append("")
            
        elif block_type == "Фильтр":
            condition = params.get("Условие", "volume > 0")
            message = params.get("Сообщение", "Фильтр пройден")
            
            code.append("// Фильтр")
            code.append(f"filter = {condition}")
            code.append(f"if filter")
            code.append(f"    label.new(bar_index, low, \"{message}\", color=color.gray)")
            code.append("")
            
        elif block_type == "Алерт":
            condition = params.get("Условие", "close > open")
            message = params.get("Сообщение", "Алерт!")
            frequency = params.get("Частота", "once")
            
            code.append("// Алерт")
            code.append(f"alertcondition({condition}, \"{message}\", alert.freq_{frequency})")
            code.append("")
            
        elif block_type == "Стратегия":
            name = params.get("Название", "Моя стратегия")
            initial_capital = params.get("Начальный капитал", "10000")
            commission = params.get("Комиссия", "0.1")
            
            code.append("// Стратегия")
            code.append(f"strategy(\"{name}\", overlay=true, initial_capital={initial_capital}, commission_type=strategy.commission.percent, commission_value={commission})")
            code.append("")
            
        elif block_type == "Ордер":
            order_type = params.get("Тип", "market")
            direction = params.get("Направление", "long")
            quantity = params.get("Количество", "1")
            
            code.append("// Ордер")
            if order_type == "market":
                if direction == "long":
                    code.append(f"strategy.entry(\"Long\", strategy.long, qty={quantity})")
                else:
                    code.append(f"strategy.entry(\"Short\", strategy.short, qty={quantity})")
            code.append("")
            
        elif block_type == "Риск":
            stop_loss = params.get("Стоп-лосс", "2.0")
            take_profit = params.get("Тейк-профит", "4.0")
            risk_per_trade = params.get("Риск на сделку", "1.0")
            
            code.append("// Риск")
            code.append(f"strategy.risk.max_drawdown({risk_per_trade})")
            code.append(f"strategy.risk.max_intraday_loss({stop_loss})")
            code.append(f"strategy.risk.max_intraday_filled_orders({take_profit})")
            code.append("")
            
        elif block_type == "Визуализация":
            color = params.get("Цвет линии", "blue")
            width = params.get("Толщина", "2")
            style = params.get("Стиль", "solid")
            
            code.append("// Визуализация")
            code.append(f"plot(ma, \"MA\", color=color.{color}, linewidth={width}, style=plot.style_{style})")
            code.append("")
    
    # Валидируем код
    errors = validate_code("\n".join(code))
    if errors:
        raise SyntaxError(f"Ошибка в сгенерированном коде: {errors}")
        
    # Форматируем код
    try:
        code_str = autopep8.fix_code("\n".join(code))
        # Восстанавливаем правильный формат версии
        code_str = code_str.replace("//@version = 5", "//@version=5")
    except:
        code_str = "\n".join(code)
    return code_str 