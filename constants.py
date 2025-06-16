"""
Константы для проекта
"""

# Типы блоков
BLOCK_TYPES = {
    "Индикатор": {
        "icon": "📊",
        "description": "Основные настройки индикатора",
        "params": [
            {
                "name": "Название",
                "description": "Название индикатора, которое будет отображаться в TradingView",
                "placeholder": "Мой индикатор",
                "help": "Например: 'Мой первый индикатор'"
            },
            {
                "name": "Временной интервал",
                "description": "Временной интервал для расчета индикатора",
                "values": ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1W", "1M"],
                "help": "Например: '1d' для дневного графика"
            },
            {
                "name": "Тип графика",
                "description": "Тип графика для отображения",
                "values": ["candle", "bar", "line", "area"],
                "help": "Например: 'candle' для свечного графика"
            }
        ],
        "default_values": {
            "Название": "Мой индикатор",
            "Временной интервал": "1d",
            "Тип графика": "candle"
        }
    },
    "Скользящая средняя": {
        "icon": "📈",
        "description": "Скользящая средняя (Moving Average) - индикатор тренда, показывающий среднее значение цены за определенный период",
        "params": [
            {
                "name": "Тип",
                "description": "Тип скользящей средней",
                "values": ["SMA", "EMA", "WMA", "VWMA"],
                "help": "SMA - простая, EMA - экспоненциальная, WMA - взвешенная, VWMA - объемно-взвешенная"
            },
            {
                "name": "Период",
                "description": "Количество баров для расчета",
                "placeholder": "14",
                "help": "Например: 14, 50, 200"
            },
            {
                "name": "Источник",
                "description": "Источник данных для расчета",
                "values": ["close", "open", "high", "low", "hl2", "hlc3", "ohlc4"],
                "help": "close - цена закрытия, open - цена открытия, hl2 - (high+low)/2, hlc3 - (high+low+close)/3"
            }
        ],
        "default_values": {
            "Тип": "EMA",
            "Период": "14",
            "Источник": "close"
        }
    },
    "RSI": {
        "icon": "📊",
        "description": "Индекс относительной силы (Relative Strength Index) - осциллятор, показывающий силу тренда и вероятность его смены",
        "params": [
            {
                "name": "Период",
                "description": "Количество баров для расчета",
                "placeholder": "14",
                "help": "Например: 14, 21, 28"
            },
            {
                "name": "Источник",
                "description": "Источник данных для расчета",
                "values": ["close", "open", "high", "low", "hl2", "hlc3", "ohlc4"],
                "help": "close - цена закрытия, open - цена открытия, hl2 - (high+low)/2, hlc3 - (high+low+close)/3"
            }
        ],
        "default_values": {
            "Период": "14",
            "Источник": "close"
        }
    },
    "MACD": {
        "icon": "📊",
        "description": "Схождение/расхождение скользящих средних (Moving Average Convergence/Divergence) - индикатор тренда и моментума",
        "params": [
            {
                "name": "Быстрый период",
                "description": "Период быстрой скользящей средней",
                "placeholder": "12",
                "help": "Например: 12"
            },
            {
                "name": "Медленный период",
                "description": "Период медленной скользящей средней",
                "placeholder": "26",
                "help": "Например: 26"
            },
            {
                "name": "Сигнальный период",
                "description": "Период сигнальной линии",
                "placeholder": "9",
                "help": "Например: 9"
            }
        ],
        "default_values": {
            "Быстрый период": "12",
            "Медленный период": "26",
            "Сигнальный период": "9"
        }
    },
    "Bollinger Bands": {
        "icon": "📊",
        "description": "Полосы Боллинджера (Bollinger Bands) - индикатор волатильности, показывающий отклонение цены от скользящей средней",
        "params": [
            {
                "name": "Период",
                "description": "Количество баров для расчета",
                "placeholder": "20",
                "help": "Например: 20"
            },
            {
                "name": "Множитель",
                "description": "Множитель стандартного отклонения",
                "placeholder": "2.0",
                "help": "Например: 2.0"
            },
            {
                "name": "Источник",
                "description": "Источник данных для расчета",
                "values": ["close", "open", "high", "low", "hl2", "hlc3", "ohlc4"],
                "help": "close - цена закрытия, open - цена открытия, hl2 - (high+low)/2, hlc3 - (high+low+close)/3"
            }
        ],
        "default_values": {
            "Период": "20",
            "Множитель": "2.0",
            "Источник": "close"
        }
    },
    "Stochastic": {
        "icon": "📊",
        "description": "Стохастический осциллятор (Stochastic) - индикатор моментума, показывающий положение текущей цены относительно диапазона цен за определенный период",
        "params": [
            {
                "name": "Период K",
                "description": "Период %K линии",
                "placeholder": "14",
                "help": "Например: 14"
            },
            {
                "name": "Период D",
                "description": "Период %D линии",
                "placeholder": "3",
                "help": "Например: 3"
            },
            {
                "name": "Замедление",
                "description": "Период замедления",
                "placeholder": "3",
                "help": "Например: 3"
            }
        ],
        "default_values": {
            "Период K": "14",
            "Период D": "3",
            "Замедление": "3"
        }
    },
    "ATR": {
        "icon": "📊",
        "description": "Средний истинный диапазон (Average True Range) - индикатор волатильности",
        "params": [
            {
                "name": "Период",
                "description": "Количество баров для расчета",
                "placeholder": "14",
                "help": "Например: 14"
            }
        ],
        "default_values": {
            "Период": "14"
        }
    },
    "Импульс": {
        "icon": "📊",
        "description": "Импульс (Momentum) - индикатор, показывающий скорость изменения цены",
        "params": [
            {
                "name": "Период",
                "description": "Количество баров для расчета",
                "placeholder": "14",
                "help": "Например: 14"
            },
            {
                "name": "Источник",
                "description": "Источник данных для расчета",
                "values": ["close", "open", "high", "low", "hl2", "hlc3", "ohlc4"],
                "help": "close - цена закрытия, open - цена открытия, hl2 - (high+low)/2, hlc3 - (high+low+close)/3"
            }
        ],
        "default_values": {
            "Период": "14",
            "Источник": "close"
        }
    },
    "CCI": {
        "icon": "📊",
        "description": "Индекс товарного канала (Commodity Channel Index) - индикатор, показывающий отклонение цены от скользящей средней",
        "params": [
            {
                "name": "Период",
                "description": "Количество баров для расчета",
                "placeholder": "20",
                "help": "Например: 20"
            },
            {
                "name": "Источник",
                "description": "Источник данных для расчета",
                "values": ["close", "open", "high", "low", "hl2", "hlc3", "ohlc4"],
                "help": "close - цена закрытия, open - цена открытия, hl2 - (high+low)/2, hlc3 - (high+low+close)/3"
            }
        ],
        "default_values": {
            "Период": "20",
            "Источник": "hlc3"
        }
    },
    "Условие": {
        "icon": "⚡",
        "description": "Условие для генерации сигналов",
        "params": [
            {
                "name": "Условие",
                "description": "Условие для генерации сигнала",
                "placeholder": "close > open",
                "help": "Например: close > open, rsi > 70, macd > signal"
            },
            {
                "name": "Сообщение",
                "description": "Сообщение для отображения при выполнении условия",
                "placeholder": "Сигнал!",
                "help": "Например: Покупка!, Продажа!, Сигнал!"
            }
        ],
        "default_values": {
            "Условие": "close > open",
            "Сообщение": "Сигнал!"
        }
    },
    "Пересечение": {
        "icon": "⚡",
        "description": "Пересечение двух линий для генерации сигналов",
        "params": [
            {
                "name": "Линия 1",
                "description": "Первая линия для пересечения",
                "placeholder": "ma1",
                "help": "Например: close, ma, rsi"
            },
            {
                "name": "Линия 2",
                "description": "Вторая линия для пересечения",
                "placeholder": "ma2",
                "help": "Например: open, ma2, 70"
            },
            {
                "name": "Сообщение",
                "description": "Сообщение для отображения при пересечении",
                "placeholder": "Пересечение!",
                "help": "Например: Покупка!, Продажа!, Пересечение!"
            }
        ],
        "default_values": {
            "Линия 1": "close",
            "Линия 2": "ma",
            "Сообщение": "Пересечение!"
        }
    },
    "Уровень": {
        "icon": "📏",
        "description": "Горизонтальная линия на заданном уровне",
        "params": [
            {
                "name": "Значение",
                "description": "Значение уровня",
                "placeholder": "0",
                "help": "Например: 100, 200, 0"
            },
            {
                "name": "Цвет",
                "description": "Цвет линии",
                "values": ["red", "green", "blue", "yellow", "purple", "orange", "gray"],
                "help": "Например: red, green, blue"
            },
            {
                "name": "Стиль",
                "description": "Стиль линии",
                "values": ["solid", "dashed", "dotted"],
                "help": "Например: solid, dashed, dotted"
            }
        ],
        "default_values": {
            "Значение": "0",
            "Цвет": "red",
            "Стиль": "solid"
        }
    },
    "Объем": {
        "icon": "📊",
        "description": "Анализ объема торгов",
        "params": [
            {
                "name": "Период",
                "description": "Количество баров для расчета",
                "placeholder": "20",
                "help": "Например: 20"
            },
            {
                "name": "Порог",
                "description": "Порог для определения большого объема",
                "placeholder": "2.0",
                "help": "Например: 2.0 (в 2 раза больше среднего)"
            }
        ],
        "default_values": {
            "Период": "20",
            "Порог": "2.0"
        }
    },
    "Тренд": {
        "icon": "📈",
        "description": "Определение тренда",
        "params": [
            {
                "name": "Период",
                "description": "Количество баров для расчета",
                "placeholder": "50",
                "help": "Например: 50, 100, 200"
            },
            {
                "name": "Порог",
                "description": "Порог для определения сильного тренда (в %)",
                "placeholder": "2.0",
                "help": "Например: 2.0 (2%)"
            }
        ],
        "default_values": {
            "Период": "50",
            "Порог": "2.0"
        }
    },
    "Фильтр": {
        "icon": "🔍",
        "description": "Фильтр для сигналов",
        "params": [
            {
                "name": "Условие",
                "description": "Условие для фильтрации",
                "placeholder": "volume > 0",
                "help": "Например: volume > 0, atr > 1, rsi < 50"
            },
            {
                "name": "Сообщение",
                "description": "Сообщение для отображения при выполнении условия",
                "placeholder": "Фильтр пройден",
                "help": "Например: Фильтр пройден, Объем достаточный"
            }
        ],
        "default_values": {
            "Условие": "volume > 0",
            "Сообщение": "Фильтр пройден"
        }
    },
    "Алерт": {
        "icon": "🔔",
        "description": "Уведомление при выполнении условия",
        "params": [
            {
                "name": "Условие",
                "description": "Условие для генерации уведомления",
                "placeholder": "close > open",
                "help": "Например: close > open, rsi > 70, macd > signal"
            },
            {
                "name": "Сообщение",
                "description": "Сообщение для отображения в уведомлении",
                "placeholder": "Алерт!",
                "help": "Например: Покупка!, Продажа!, Алерт!"
            },
            {
                "name": "Частота",
                "description": "Частота уведомлений",
                "values": ["once", "once_per_bar", "once_per_bar_close", "always"],
                "help": "once - один раз, once_per_bar - один раз за бар, always - всегда"
            }
        ],
        "default_values": {
            "Условие": "close > open",
            "Сообщение": "Алерт!",
            "Частота": "once"
        }
    },
    "Стратегия": {
        "icon": "💰",
        "description": "Настройки торговой стратегии",
        "params": [
            {
                "name": "Название",
                "description": "Название стратегии",
                "placeholder": "Моя стратегия",
                "help": "Например: 'Моя первая стратегия'"
            },
            {
                "name": "Начальный капитал",
                "description": "Начальный капитал для тестирования",
                "placeholder": "10000",
                "help": "Например: 10000"
            },
            {
                "name": "Комиссия",
                "description": "Комиссия в процентах",
                "placeholder": "0.1",
                "help": "Например: 0.1 (0.1%)"
            }
        ],
        "default_values": {
            "Название": "Моя стратегия",
            "Начальный капитал": "10000",
            "Комиссия": "0.1"
        }
    },
    "Ордер": {
        "icon": "📝",
        "description": "Настройки ордера",
        "params": [
            {
                "name": "Тип",
                "description": "Тип ордера",
                "values": ["market", "limit", "stop"],
                "help": "market - рыночный, limit - лимитный, stop - стоп-ордер"
            },
            {
                "name": "Направление",
                "description": "Направление ордера",
                "values": ["long", "short"],
                "help": "long - покупка, short - продажа"
            },
            {
                "name": "Количество",
                "description": "Количество единиц",
                "placeholder": "1",
                "help": "Например: 1, 10, 100"
            }
        ],
        "default_values": {
            "Тип": "market",
            "Направление": "long",
            "Количество": "1"
        }
    },
    "Риск": {
        "icon": "⚠️",
        "description": "Управление рисками",
        "params": [
            {
                "name": "Стоп-лосс",
                "description": "Стоп-лосс в процентах",
                "placeholder": "2.0",
                "help": "Например: 2.0 (2%)"
            },
            {
                "name": "Тейк-профит",
                "description": "Тейк-профит в процентах",
                "placeholder": "4.0",
                "help": "Например: 4.0 (4%)"
            },
            {
                "name": "Риск на сделку",
                "description": "Риск на одну сделку в процентах от капитала",
                "placeholder": "1.0",
                "help": "Например: 1.0 (1%)"
            }
        ],
        "default_values": {
            "Стоп-лосс": "2.0",
            "Тейк-профит": "4.0",
            "Риск на сделку": "1.0"
        }
    },
    "Визуализация": {
        "icon": "🎨",
        "description": "Настройки отображения",
        "params": [
            {
                "name": "Цвет линии",
                "description": "Цвет линии",
                "values": ["red", "green", "blue", "yellow", "purple", "orange", "gray"],
                "help": "Например: red, green, blue"
            },
            {
                "name": "Толщина",
                "description": "Толщина линии",
                "values": ["1", "2", "3", "4"],
                "help": "Например: 1, 2, 3, 4"
            },
            {
                "name": "Стиль",
                "description": "Стиль линии",
                "values": ["solid", "dashed", "dotted"],
                "help": "Например: solid, dashed, dotted"
            }
        ],
        "default_values": {
            "Цвет линии": "blue",
            "Толщина": "2",
            "Стиль": "solid"
        }
    }
}