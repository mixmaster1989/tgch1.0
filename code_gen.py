import logging
from utils import validate_code

def generate_code(blocks):
    """
    Генерация кода Pine Script на основе блоков
    
    Args:
        blocks (list): Список блоков
        
    Returns:
        str: Сгенерированный код
    """
    try:
        # Определяем, есть ли блоки, требующие отдельной панели
        has_separate_panel = False
        has_indicator_block = False
        indicator_name = "My Indicator"
        
        for block in blocks:
            data = block.get_data()
            block_type = data["type"]
            if block_type in ["RSI", "MACD", "Stochastic", "CCI"]:
                has_separate_panel = True
            if block_type == "Индикатор":
                has_indicator_block = True
                params = data["params"]
                if "Название" in params:
                    indicator_name = params["Название"]
        
        code = []
        
        # Добавляем заголовок
        code.append("//@version=5")
        
        # Определяем тип индикатора (overlay или нет)
        if has_separate_panel:
            code.append(f'indicator("{indicator_name}", overlay=false)')
        else:
            code.append(f'indicator("{indicator_name}", overlay=true)')
        
        code.append("")
        
        # Переменные для отслеживания панелей
        current_panel = 0
        panel_map = {}
        
        # Обрабатываем блоки
        for block in blocks:
            data = block.get_data()
            block_type = data["type"]
            params = data["params"]
            
            # Пропускаем блок индикатора, так как мы уже добавили его в заголовок
            if block_type == "Индикатор":
                # Добавляем только комментарии и настройки
                code.append("// Настройки индикатора")
                if "Временной интервал" in params:
                    timeframe = params["Временной интервал"]
                    code.append(f'timeframe = "{timeframe}"')
                if "Тип графика" in params:
                    chart_type = params["Тип графика"]
                    code.append(f'chart_type = "{chart_type}"')
                code.append("")
                continue
            
            # Определяем, нужна ли отдельная панель для этого блока
            needs_panel = block_type in ["RSI", "MACD", "Stochastic", "CCI"]
            if needs_panel and block_type not in panel_map:
                current_panel += 1
                panel_map[block_type] = current_panel
            
            # Генерируем код для блока
            if block_type == "Скользящая средняя":
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
                
                code.append(f"plot(ma, color=color.blue, title=\"MA\")")
                code.append("")
                
            elif block_type == "RSI":
                period = params.get("Период", "14")
                source = params.get("Источник", "close")
                
                code.append("// RSI")
                code.append(f"rsi = ta.rsi({source}, {period})")
                
                panel = panel_map.get(block_type, 0)
                if panel > 0:
                    code.append(f"hline(70, \"Верхний уровень\", color=color.red, linestyle=hline.style_dashed)")
                    code.append(f"hline(30, \"Нижний уровень\", color=color.green, linestyle=hline.style_dashed)")
                    code.append(f"plot(rsi, color=color.purple, title=\"RSI\")")
                else:
                    code.append(f"plot(rsi, color=color.purple, title=\"RSI\")")
                code.append("")
                
            elif block_type == "MACD":
                fast_period = params.get("Быстрый период", "12")
                slow_period = params.get("Медленный период", "26")
                signal_period = params.get("Сигнальный период", "9")
                
                code.append("// MACD")
                code.append(f"[macd_line, signal_line, hist] = ta.macd(close, {fast_period}, {slow_period}, {signal_period})")
                
                code.append(f"plot(macd_line, color=color.blue, title=\"MACD\")")
                code.append(f"plot(signal_line, color=color.red, title=\"Signal\")")
                code.append(f"plot(hist, color=color.green, title=\"Histogram\", style=plot.style_histogram)")
                code.append("")
                
            elif block_type == "Bollinger Bands":
                period = params.get("Период", "20")
                multiplier = params.get("Множитель", "2.0")
                source = params.get("Источник", "close")
                
                code.append("// Полосы Боллинджера")
                code.append(f"[middle, upper, lower] = ta.bb({source}, {period}, {multiplier})")
                code.append(f"plot(middle, color=color.blue, title=\"Basis\")")
                code.append(f"plot(upper, color=color.red, title=\"Upper\")")
                code.append(f"plot(lower, color=color.green, title=\"Lower\")")
                code.append("")
                
            elif block_type == "Stochastic":
                k_period = params.get("Период K", "14")
                d_period = params.get("Период D", "3")
                slowing = params.get("Замедление", "3")
                
                code.append("// Стохастик")
                code.append(f"k = ta.stoch(close, high, low, {k_period})")
                code.append(f"d = ta.sma(k, {d_period})")
                
                code.append(f"plot(k, color=color.blue, title=\"%K\")")
                code.append(f"plot(d, color=color.red, title=\"%D\")")
                code.append("")
                
            elif block_type == "ATR":
                period = params.get("Период", "14")
                
                code.append("// ATR")
                code.append(f"atr = ta.atr({period})")
                code.append(f"plot(atr, color=color.blue, title=\"ATR\")")
                code.append("")
                
            elif block_type == "Импульс":
                period = params.get("Период", "14")
                source = params.get("Источник", "close")
                
                code.append("// Импульс")
                code.append(f"impulse = {source} - {source}[{period}]")
                code.append(f"plot(impulse, color=color.blue, title=\"Impulse\")")
                code.append("")
                
            elif block_type == "CCI":
                period = params.get("Период", "20")
                source = params.get("Источник", "hlc3")
                
                code.append("// CCI")
                code.append(f"cci = ta.cci({source}, {period})")
                code.append(f"plot(cci, color=color.blue, title=\"CCI\")")
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
                color_val = params.get("Цвет", "red")
                style = params.get("Стиль", "solid")
                
                code.append("// Уровень")
                code.append(f"hline({value}, \"Уровень {value}\", color=color.{color_val}, linestyle=hline.style_{style})")
                code.append("")
                
            elif block_type == "Объем":
                period = params.get("Период", "20")
                threshold = params.get("Порог", "2.0")
                
                code.append("// Объём")
                code.append(f"vol_ma = ta.sma(volume, {period})")
                code.append(f"if volume > vol_ma * {threshold}")
                code.append(f"    label.new(bar_index, high, \"Большой объём!\", color=color.purple)")
                code.append(f"plot(vol_ma, color=color.blue, title=\"Volume\")")
                code.append("")
                
            elif block_type == "Тренд":
                period = params.get("Период", "20")
                threshold = params.get("Порог", "2.0")
                
                code.append("// Тренд")
                code.append(f"ma = ta.sma(close, {period})")
                code.append(f"if math.abs(close - ma) > ma * {threshold} / 100")
                code.append(f"    label.new(bar_index, high, \"Сильный тренд!\", color=color.orange)")
                code.append(f"plot(ma, color=color.blue, title=\"Trend\")")
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
                
                # Заменяем объявление индикатора на стратегию
                for i, line in enumerate(code):
                    if line.startswith("indicator("):
                        code[i] = f"strategy(\"{name}\", overlay=true, initial_capital={initial_capital}, commission_type=strategy.commission.percent, commission_value={commission})"
                        break
                
                code.append("// Стратегия")
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
                color_val = params.get("Цвет линии", "blue")
                width = params.get("Толщина", "2")
                style = params.get("Стиль", "solid")
                
                code.append("// Визуализация")
                code.append(f"plot(close, \"Price\", color=color.{color_val}, linewidth={width}, style=plot.style_{style})")
                code.append("")
        
        # Проверяем код на ошибки
        errors = validate_code("\n".join(code))
        if errors:
            logging.error(f"Ошибки в сгенерированном коде: {errors}")
            # Добавляем комментарий с ошибками в начало кода
            error_comments = ["// ВНИМАНИЕ: В коде есть ошибки:"]
            for error in errors:
                error_comments.append(f"// - {error}")
            error_comments.append("//")
            code = error_comments + code
        
        return "\n".join(code)
    
    except Exception as e:
        logging.error(f"Ошибка при генерации кода: {str(e)}")
        return f"// Ошибка при генерации кода: {str(e)}\n//@version=5\nindicator(\"Error\", overlay=true)\nplot(close, color=color.red)"