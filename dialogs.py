print('DIALOGS VERY TOP')
import sys
print('DIALOGS AFTER sys')
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                           QComboBox, QLineEdit, QTextEdit, QFrame, QWizard, QWizardPage,
                           QFileDialog, QMessageBox, QScrollArea, QWidget, QCheckBox)
print('DIALOGS AFTER PyQt5.QtWidgets')
from PyQt5.QtCore import Qt
print('DIALOGS AFTER QtCore')
from PyQt5.QtGui import QFont, QPixmap
print('DIALOGS AFTER QtGui')
from block import Block
print('DIALOGS AFTER block')
from constants import BLOCK_TYPES
print('DIALOGS AFTER constants')
from code_gen import generate_code
print('DIALOGS AFTER code_gen')
import numpy as np
print('DIALOGS AFTER numpy')
import matplotlib.pyplot as plt
print('DIALOGS AFTER plt')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
print('DIALOGS AFTER FigureCanvas')
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets

class TemplateDialog(QDialog):
    """Диалог выбора шаблона индикатора"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Шаблоны индикаторов")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        # Заголовок
        title = QLabel("Выберите шаблон индикатора")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        # Список шаблонов
        templates = [
            {"name": "EMA 14", "block_type": "Скользящая средняя", "params": {"Тип": "EMA", "Период": "14", "Источник": "close"}},
            {"name": "RSI 14", "block_type": "RSI", "params": {"Период": "14", "Источник": "close"}},
            {"name": "MACD стандарт", "block_type": "MACD", "params": {"Быстрый период": "12", "Медленный период": "26", "Сигнальный период": "9"}},
            {"name": "Bollinger Bands 20", "block_type": "Bollinger Bands", "params": {"Период": "20", "Множитель": "2.0", "Источник": "close"}},
            {"name": "Stochastic 14/3", "block_type": "Stochastic", "params": {"Период K": "14", "Период D": "3", "Замедление": "3"}},
            {"name": "ATR 14", "block_type": "ATR", "params": {"Период": "14"}},
            {"name": "CCI 20", "block_type": "CCI", "params": {"Период": "20", "Источник": "hlc3"}},
            {"name": "Объём MA 20", "block_type": "Объем", "params": {"Период": "20", "Порог": "2.0"}},
            {"name": "Тренд MA 50", "block_type": "Тренд", "params": {"Период": "50", "Порог": "2.0"}},
            {"name": "Уровень 100", "block_type": "Уровень", "params": {"Значение": "100", "Цвет": "red", "Стиль": "solid"}},
            {"name": "Алерт пересечение", "block_type": "Пересечение", "params": {"Линия 1": "close", "Линия 2": "ma", "Сообщение": "Пересечение!"}},
            {"name": "Стратегия Long", "block_type": "Стратегия", "params": {"Название": "Long Strategy", "Начальный капитал": "10000", "Комиссия": "0.1"}},
            {"name": "Риск 2%", "block_type": "Риск", "params": {"Стоп-лосс": "2.0", "Тейк-профит": "4.0", "Риск на сделку": "1.0"}},
            {"name": "Визуализация Blue", "block_type": "Визуализация", "params": {"Цвет линии": "blue", "Толщина": "2", "Стиль": "solid"}}
        ]
        for template in templates:
            btn = QPushButton(template["name"])
            btn.setFont(QFont("Arial", 12))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2b2b2b;
                    color: white;
                    border: 1px solid #3d3d3d;
                    border-radius: 5px;
                    padding: 10px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #3d3d3d;
                }
            """)
            btn.clicked.connect(lambda checked, t=template: self.select_template(t))
            layout.addWidget(btn)
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
        self.setLayout(layout)

    def select_template(self, template):
        self.selected_template = template
        self.accept()

class BlockSelectDialog(QDialog):
    """Диалог выбора типа блока"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выберите тип блока")
        self.setMinimumWidth(500)
        self.selected_type = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        title = QLabel("Выберите тип блока")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)

        # Кнопка шаблонов
        template_btn = QPushButton("📚 Шаблоны популярных индикаторов")
        template_btn.setStyleSheet("background-color: #444; color: #fff; border-radius: 5px; padding: 8px; font-size: 14px;")
        template_btn.clicked.connect(self.show_templates)
        layout.addWidget(template_btn)

        # --- Добавляем QScrollArea для прокрутки ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        # Список карточек блоков
        for block_type, info in BLOCK_TYPES.items():
            card = QFrame()
            card.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
            card.setStyleSheet(f"""
                QFrame {{
                    background-color: #23272e;
                    border: 2px solid #3d3d3d;
                    border-radius: 12px;
                    margin-bottom: 10px;
                }}
                QFrame:hover {{
                    border: 2px solid #4a90e2;
                    background-color: #2c313c;
                }}
            """)
            card_layout = QHBoxLayout()
            icon = QLabel(info.get("icon", "❔"))
            icon.setFont(QFont("Arial", 32))
            icon.setStyleSheet("margin-right: 18px;")
            card_layout.addWidget(icon)
            text_layout = QVBoxLayout()
            name = QLabel(block_type)
            name.setFont(QFont("Arial", 16, QFont.Bold))
            name.setStyleSheet("color: #fff;")
            desc = QLabel(info.get("description", ""))
            desc.setStyleSheet("color: #aaa; font-size: 13px;")
            desc.setWordWrap(True)
            text_layout.addWidget(name)
            text_layout.addWidget(desc)
            card_layout.addLayout(text_layout)
            card_layout.addStretch()
            card.setLayout(card_layout)
            card.mousePressEvent = lambda e, t=block_type: self.select_type(t)
            scroll_layout.addWidget(card)

        scroll_content.setLayout(scroll_layout)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        self.setLayout(layout)

    def select_type(self, block_type):
        self.selected_type = block_type
        self.accept()

    def show_templates(self):
        dialog = TemplateDialog(self)
        if dialog.exec_() == QDialog.Accepted and hasattr(dialog, 'selected_template'):
            self.selected_type = dialog.selected_template["block_type"]
            self.selected_params = dialog.selected_template["params"]
            self.accept()

class WizardDialog(QWizard):
    """Пошаговый мастер создания индикатора (иерархия этапов, подсказки, все блоки)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Пошаговый мастер создания индикатора")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.setStyleSheet("""
            QWizard {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QWizardPage {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QComboBox, QLineEdit {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #4a4a4a;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.addPage(IndicatorBasePage())
        self.addPage(IndicatorParamsPage())
        self.addPage(IndicatorFiltersPage())
        self.addPage(IndicatorVisualPage())
        self.addPage(IndicatorAlertsPage())
        self.addPage(IndicatorResultPage())

from constants import BLOCK_TYPES

class IndicatorBasePage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Шаг 1: Выберите основу индикатора")
        layout = QVBoxLayout()
        self.combo = QComboBox()
        self.help_label = QLabel()
        self.help_label.setWordWrap(True)
        for block_type, info in BLOCK_TYPES.items():
            if block_type in ["Индикатор", "Параметр пользователя"]:
                continue
            self.combo.addItem(f"{info.get('icon','')} {block_type}", block_type)
        layout.addWidget(QLabel("Какой индикатор вы хотите создать?"))
        layout.addWidget(self.combo)
        layout.addWidget(self.help_label)
        self.setLayout(layout)
        self.combo.currentIndexChanged.connect(self.update_help)
        self.registerField("base_type", self.combo, "currentData")
        self.update_help()
    def update_help(self):
        block_type = self.combo.currentData()
        info = BLOCK_TYPES.get(block_type, {})
        self.help_label.setText(info.get("description", ""))

class IndicatorParamsPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Шаг 2: Настройте параметры индикатора")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        # Подсказки по значениям для ключевых параметров
        self.value_hints = {
            "RSI": {
                "Период": {
                    "7": "Очень чувствительный, подходит для скальпинга, много ложных сигналов",
                    "14": "<b>Золотой стандарт</b>, сбалансирован для большинства стратегий",
                    "21": "Более сглаженный, меньше сигналов, подходит для долгосрочных трендов",
                    "50": "Очень медленный, только для крупных трендов"
                }
            },
            "Скользящая средняя": {
                "Период": {
                    "14": "Краткосрок, быстрые сигналы",
                    "50": "<b>Золотой стандарт</b> для среднесрока",
                    "100": "Долгосрок, фильтрация крупных трендов",
                    "200": "Классика для долгосрочного анализа"
                },
                "Тип": {
                    "EMA": "Экспоненциальная, быстрее реагирует на цену (золотой стандарт)",
                    "SMA": "Простая, равномерно сглаживает",
                    "WMA": "Взвешенная, больше вес последним барам",
                    "VWMA": "Объемно-взвешенная, учитывает объем"
                }
            },
            # Можно добавить для других блоков и параметров
        }
    def initializePage(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        block_type = self.field("base_type")
        info = BLOCK_TYPES.get(block_type, {})
        self.param_widgets = {}
        self.hint_labels = {}
        # Автоматически строим value_hints для всех параметров с values
        auto_value_hints = {}
        for param in info.get("params", []):
            if "values" in param:
                auto_value_hints.setdefault(block_type, {})[param["name"]] = {}
                # Универсальный парсер help-строки для значений вида 'ключ - описание'
                def parse_value_help(help_str):
                    result = {}
                    for part in help_str.split(','):
                        if '-' in part:
                            key, val = part.split('-', 1)
                            result[key.strip()] = val.strip()
                    return result
                value_help_map = {}
                if param["name"].lower() == "источник" and "help" in param:
                    value_help_map = parse_value_help(param["help"])
                elif "help" in param and all('-' in s for s in param["help"].split(',')):
                    value_help_map = parse_value_help(param["help"])
                for v in param["values"]:
                    if value_help_map:
                        hint = value_help_map.get(str(v), param.get("description", ""))
                    else:
                        # Старый механизм для других параметров
                        if param["name"].lower() == "период":
                            if str(v) in ["14", "50", "200"]:
                                hint = f"<b>Золотой стандарт</b> для {v}"
                            else:
                                hint = f"Период {v}: {'быстрый' if int(v)<20 else 'медленный' if int(v)>50 else 'средний'}"
                        elif param["name"].lower() == "тип":
                            if v == "EMA":
                                hint = "Экспоненциальная, быстрее реагирует на цену (золотой стандарт)"
                            elif v == "SMA":
                                hint = "Простая, равномерно сглаживает"
                            elif v == "WMA":
                                hint = "Взвешенная, больше вес последним барам"
                            elif v == "VWMA":
                                hint = "Объемно-взвешенная, учитывает объем"
                            else:
                                hint = param.get("help", param.get("description", ""))
                        elif param["name"].lower() == "цвет" or param["name"].lower() == "цвет линии":
                            if v == "blue":
                                hint = "Стандарт для большинства индикаторов"
                            elif v == "red":
                                hint = "Часто используется для сигналов продажи"
                            elif v == "green":
                                hint = "Часто используется для сигналов покупки"
                            else:
                                hint = param.get("help", param.get("description", ""))
                        elif param["name"].lower() == "стиль":
                            if v == "solid":
                                hint = "Сплошная линия — стандарт"
                            elif v == "dashed":
                                hint = "Пунктирная линия — для второстепенных уровней"
                            elif v == "dotted":
                                hint = "Точечная линия — для слабых уровней"
                            else:
                                hint = param.get("help", param.get("description", ""))
                        elif param["name"].lower() == "частота":
                            if v == "once":
                                hint = "Один раз при первом выполнении условия"
                            elif v == "once_per_bar":
                                hint = "Один раз за бар"
                            elif v == "always":
                                hint = "Всегда, когда выполняется условие"
                            else:
                                hint = param.get("help", param.get("description", ""))
                        else:
                            hint = param.get("help", param.get("description", ""))
                    auto_value_hints[block_type][param["name"]][str(v)] = hint
        # Объединяем с ручными value_hints
        value_hints = getattr(self, "value_hints", {})
        for bt in auto_value_hints:
            value_hints.setdefault(bt, {}).update(auto_value_hints[bt])
        self.value_hints = value_hints
        for param in info.get("params", []):
            row = QHBoxLayout()
            name_label = QLabel(param["name"])
            name_label.setMinimumWidth(150)
            help_label = QLabel(param.get("help", param.get("description", "")))
            help_label.setStyleSheet("color: #aaa; font-size: 12px;")
            help_label.setWordWrap(True)
            if "values" in param:
                input_widget = QComboBox()
                for v in param["values"]:
                    input_widget.addItem(str(v))
            else:
                input_widget = QComboBox()
                if "placeholder" in param:
                    input_widget.addItem(str(param["placeholder"]))
                input_widget.addItem("5")
                input_widget.addItem("7")
                input_widget.addItem("10")
                input_widget.addItem("14")
                input_widget.addItem("21")
                input_widget.addItem("50")
                input_widget.addItem("100")
                input_widget.addItem("200")
            row.addWidget(name_label)
            row.addWidget(input_widget)
            row.addWidget(help_label)
            self.layout.addLayout(row)
            value_hint = QLabel()
            value_hint.setStyleSheet("color: #ffb300; font-size: 12px;")
            value_hint.setWordWrap(True)
            self.layout.addWidget(value_hint)
            self.hint_labels[param["name"]] = value_hint
            def update_hint(idx, p=param["name"], bt=block_type, w=input_widget, l=value_hint):
                val = w.currentText()
                hint = self.value_hints.get(bt, {}).get(p, {}).get(val, "")
                l.setText(hint)
            input_widget.currentIndexChanged.connect(update_hint)
            update_hint(0)
            self.param_widgets[param["name"]] = input_widget
            self.registerField(f"param_{param['name']}", input_widget, "currentText")

class IndicatorFiltersPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Шаг 3: Фильтры и дополнительные условия")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
    def initializePage(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        # Пример: фильтр по объему, свечной паттерн, условие
        self.filter_checkboxes = []
        for block_type, info in BLOCK_TYPES.items():
            if block_type in ["Индикатор", "Параметр пользователя"]:
                continue
            if "фильтр" in info.get("description", "").lower() or "паттерн" in info.get("description", "").lower() or block_type in ["Условие", "Фильтр"]:
                cb = QCheckBox(f"{info.get('icon','')} {block_type}")
                cb.setToolTip(info.get("description", ""))
                self.layout.addWidget(cb)
                self.filter_checkboxes.append(cb)
                # Добавим подробное описание и пример
                desc = QLabel(f'<span style="color:#ffb300">{info.get("description", "")}</span>')
                desc.setWordWrap(True)
                desc.setStyleSheet("font-size: 13px; margin-left: 30px;")
                self.layout.addWidget(desc)
                # Пример использования (если есть help у первого параметра)
                params = info.get("params", [])
                if params and params[0].get("help"):
                    example = QLabel(f'<span style="color:#aaa">Пример: {params[0]["help"]}</span>')
                    example.setWordWrap(True)
                    example.setStyleSheet("font-size: 12px; margin-left: 30px;")
                    self.layout.addWidget(example)
    def validatePage(self):
        self.selected_filters = [cb.text().strip().split(' ',1)[-1] for cb in self.filter_checkboxes if cb.isChecked()]
        return True

class IndicatorVisualPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Шаг 4: Визуализация и сигналы")
        layout = QVBoxLayout()
        self.signal_checkbox = QCheckBox("Показывать сигналы на графике")
        self.signal_checkbox.setChecked(True)
        self.color_combo = QComboBox()
        self.color_combo.addItems(["Синий", "Зеленый", "Красный", "Фиолетовый", "Оранжевый"])
        layout.addWidget(self.signal_checkbox)
        layout.addWidget(QLabel("Цвет линии/сигнала:"))
        layout.addWidget(self.color_combo)
        self.setLayout(layout)
        self.registerField("show_signals", self.signal_checkbox)
        self.registerField("color", self.color_combo, "currentText")

class IndicatorAlertsPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Шаг 5: Алерты и уведомления")
        layout = QVBoxLayout()
        self.alert_checkbox = QCheckBox("Добавить алерт при сигнале")
        self.alert_checkbox.setChecked(True)
        layout.addWidget(self.alert_checkbox)
        self.setLayout(layout)
        self.registerField("add_alert", self.alert_checkbox)

class IndicatorResultPage(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Шаг 6: Готовый код индикатора и предпросмотр")
        layout = QVBoxLayout()
        self.code_area = QTextEdit()
        self.code_area.setReadOnly(True)
        self.code_area.setFont(QFont("Consolas", 12))
        self.code_area.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 10px;
                font-family: Consolas;
            }
        """)
        layout.addWidget(self.code_area)
        # pyqtgraph widget для предпросмотра
        self.pg_widget = pg.GraphicsLayoutWidget()
        layout.addWidget(self.pg_widget)
        self.setLayout(layout)
    def initializePage(self):
        from block import Block
        from code_gen import generate_code
        blocks = []
        indicator_name = self.wizard().field("base_type")
        blocks.append(Block("Индикатор", {"Название": indicator_name}))
        params = {}
        for param in ["Тип", "Период", "Источник", "Множитель", "Период K", "Период D", "Замедление"]:
            try:
                params[param] = self.wizard().field(f"param_{param}")
            except Exception:
                pass
        blocks.append(Block(indicator_name, params))
        if hasattr(self.wizard(), "selected_filters") and "Фильтр" in self.wizard().selected_filters:
            params_f = {"Условие": self.wizard().field("param_Условие"), "Сообщение": "Фильтр пройден"}
            blocks.append(Block("Фильтр", params_f))
        if hasattr(self.wizard(), "selected_filters") and "Условие" in self.wizard().selected_filters:
            params_u = {"Условие": self.wizard().field("param_Условие"), "Сообщение": "Сигнал!"}
            blocks.append(Block("Условие", params_u))
        code = generate_code(blocks)
        self.code_area.setText(code)
        # --- pyqtgraph preview ---
        self.pg_widget.clear()
        n = 200
        np.random.seed(42)
        price = np.cumsum(np.random.randn(n)) + 100
        if indicator_name in ["RSI", "MACD", "Stochastic", "ATR", "CCI"]:
            p1 = self.pg_widget.addPlot(row=0, col=0, title="Цена")
            p2 = self.pg_widget.addPlot(row=1, col=0, title=indicator_name)
            p1.plot(price, pen=pg.mkPen('#888', width=1), name='Цена')
        else:
            p1 = self.pg_widget.addPlot(row=0, col=0, title="Цена + Индикатор")
            p1.plot(price, pen=pg.mkPen('#888', width=1), name='Цена')
            p2 = None
        # MA
        if indicator_name == "Скользящая средняя":
            period = int(params.get("Период", 14))
            ma_type = params.get("Тип", "EMA")
            if ma_type == "EMA":
                ma = np.zeros_like(price)
                alpha = 2/(period+1)
                ma[0] = price[0]
                for i in range(1, n):
                    ma[i] = alpha*price[i] + (1-alpha)*ma[i-1]
            elif ma_type == "SMA":
                ma = np.convolve(price, np.ones(period)/period, mode='valid')
                ma = np.concatenate([np.full(period-1, np.nan), ma])
            elif ma_type == "WMA":
                weights = np.arange(1, period+1)
                ma = np.array([np.dot(price[i-period+1:i+1], weights)/weights.sum() if i >= period-1 else np.nan for i in range(n)])
            elif ma_type == "VWMA":
                ma = np.convolve(price, np.ones(period)/period, mode='valid')
                ma = np.concatenate([np.full(period-1, np.nan), ma])
            else:
                ma = np.convolve(price, np.ones(period)/period, mode='valid')
                ma = np.concatenate([np.full(period-1, np.nan), ma])
            p1.plot(ma, pen=pg.mkPen('b', width=2), name=f'{ma_type}({period})')
        # RSI
        elif indicator_name == "RSI":
            period = int(params.get("Период", 14))
            rsi = np.zeros_like(price)
            delta = np.diff(price, prepend=price[0])
            up = np.where(delta > 0, delta, 0)
            down = np.where(delta < 0, -delta, 0)
            roll_up = np.zeros_like(price)
            roll_down = np.zeros_like(price)
            roll_up[0] = up[0]
            roll_down[0] = down[0]
            for i in range(1, n):
                roll_up[i] = (roll_up[i-1]*(period-1) + up[i])/period
                roll_down[i] = (roll_down[i-1]*(period-1) + down[i])/period
                rs = roll_up[i]/roll_down[i] if roll_down[i] != 0 else 0
                rsi[i] = 100 - 100/(1+rs) if roll_down[i] != 0 else 100
            p2.plot(rsi, pen=pg.mkPen('m', width=2), name='RSI')
            p2.addLine(y=70, pen=pg.mkPen('r', style=pg.QtCore.Qt.DashLine))
            p2.addLine(y=30, pen=pg.mkPen('g', style=pg.QtCore.Qt.DashLine))
            p2.setYRange(0, 100)
        # MACD
        elif indicator_name == "MACD":
            fast = int(params.get("Быстрый период", 12))
            slow = int(params.get("Медленный период", 26))
            signal = int(params.get("Сигнальный период", 9))
            def ema(arr, p):
                a = 2/(p+1)
                res = np.zeros_like(arr)
                res[0] = arr[0]
                for i in range(1, len(arr)):
                    res[i] = a*arr[i] + (1-a)*res[i-1]
                return res
            macd_line = ema(price, fast) - ema(price, slow)
            signal_line = ema(macd_line, signal)
            hist = macd_line - signal_line
            p2.plot(macd_line, pen=pg.mkPen('b', width=2), name='MACD')
            p2.plot(signal_line, pen=pg.mkPen('r', width=2), name='Signal')
            bg = pg.BarGraphItem(x=np.arange(n), height=hist, width=0.8, brush='g')
            p2.addItem(bg)
        # Bollinger Bands
        elif indicator_name == "Bollinger Bands":
            period = int(params.get("Период", 20))
            mult = float(params.get("Множитель", 2.0))
            sma = np.convolve(price, np.ones(period)/period, mode='valid')
            sma = np.concatenate([np.full(period-1, np.nan), sma])
            std = np.array([np.std(price[max(0,i-period+1):i+1]) if i >= period-1 else np.nan for i in range(n)])
            upper = sma + mult*std
            lower = sma - mult*std
            p1.plot(sma, pen=pg.mkPen('b', width=2), name='Basis')
            p1.plot(upper, pen=pg.mkPen('r', width=2), name='Upper')
            p1.plot(lower, pen=pg.mkPen('g', width=2), name='Lower')
        # Stochastic
        elif indicator_name == "Stochastic":
            k_period = int(params.get("Период K", 14))
            d_period = int(params.get("Период D", 3))
            k = np.zeros_like(price)
            for i in range(k_period-1, n):
                low = np.min(price[i-k_period+1:i+1])
                high = np.max(price[i-k_period+1:i+1])
                k[i] = 100*(price[i]-low)/(high-low) if high != low else 0
            d = np.convolve(k, np.ones(d_period)/d_period, mode='valid')
            d = np.concatenate([np.full(d_period-1, np.nan), d])
            p2.plot(k, pen=pg.mkPen('b', width=2), name='%K')
            p2.plot(d, pen=pg.mkPen('r', width=2), name='%D')
            p2.addLine(y=80, pen=pg.mkPen('r', style=pg.QtCore.Qt.DashLine))
            p2.addLine(y=20, pen=pg.mkPen('g', style=pg.QtCore.Qt.DashLine))
            p2.setYRange(0, 100)
        # ATR
        elif indicator_name == "ATR":
            period = int(params.get("Период", 14))
            tr = np.zeros_like(price)
            tr[0] = 0
            for i in range(1, n):
                tr[i] = max(price[i]-price[i-1], abs(price[i]-np.min(price[max(0,i-1):i+1])), abs(price[i]-np.max(price[max(0,i-1):i+1])))
            atr = np.zeros_like(price)
            atr[0] = tr[0]
            for i in range(1, n):
                atr[i] = (atr[i-1]*(period-1) + tr[i])/period
            p2.plot(atr, pen=pg.mkPen('b', width=2), name='ATR')
        # CCI
        elif indicator_name == "CCI":
            period = int(params.get("Период", 20))
            tp = price
            sma = np.convolve(tp, np.ones(period)/period, mode='valid')
            sma = np.concatenate([np.full(period-1, np.nan), sma])
            mad = np.array([np.mean(np.abs(tp[max(0,i-period+1):i+1]-sma[i])) if i >= period-1 else np.nan for i in range(n)])
            cci = (tp-sma)/(0.015*mad)
            p2.plot(cci, pen=pg.mkPen('b', width=2), name='CCI')
            p2.addLine(y=100, pen=pg.mkPen('r', style=pg.QtCore.Qt.DashLine))
            p2.addLine(y=-100, pen=pg.mkPen('g', style=pg.QtCore.Qt.DashLine))
        # Импульс
        elif indicator_name == "Импульс":
            period = int(params.get("Период", 14))
            impulse = price - np.concatenate([np.full(period, np.nan), price[:-period]])
            p1.plot(impulse, pen=pg.mkPen('b', width=2), name='Impulse')
        # else: только цена уже нарисована

class ExampleDialog(QDialog):
    """Диалог с примерами индикаторов"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Примеры индикаторов")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        # Заголовок
        title = QLabel("Примеры индикаторов на графике TradingView")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        # Список примеров
        examples = [
            {
                "name": "EMA 14",
                "description": "Экспоненциальная скользящая средняя с периодом 14. Показывает тренд и уровни поддержки/сопротивления.",
                "image": "examples/ema14.png"
            },
            {
                "name": "RSI 14",
                "description": "Индекс относительной силы с периодом 14. Показывает перекупленность/перепроданность рынка.",
                "image": "examples/rsi14.png"
            },
            {
                "name": "MACD стандарт",
                "description": "Схождение/расхождение скользящих средних. Показывает тренд и моментум рынка.",
                "image": "examples/macd.png"
            },
            {
                "name": "Bollinger Bands 20",
                "description": "Полосы Боллинджера с периодом 20. Показывают волатильность и уровни поддержки/сопротивления.",
                "image": "examples/bb20.png"
            },
            {
                "name": "Stochastic 14/3",
                "description": "Стохастический осциллятор с периодами 14 и 3. Показывает моментум и развороты тренда.",
                "image": "examples/stoch.png"
            }
        ]
        for example in examples:
            card = QFrame()
            card.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
            card.setStyleSheet("""
                QFrame {
                    background-color: #23272e;
                    border: 2px solid #3d3d3d;
                    border-radius: 12px;
                    margin-bottom: 10px;
                }
                QFrame:hover {
                    border: 2px solid #4a90e2;
                    background-color: #2c313c;
                }
            """)
            card_layout = QVBoxLayout()
            name = QLabel(example["name"])
            name.setFont(QFont("Arial", 16, QFont.Bold))
            name.setStyleSheet("color: #fff;")
            desc = QLabel(example["description"])
            desc.setStyleSheet("color: #aaa; font-size: 13px;")
            desc.setWordWrap(True)
            image = QLabel()
            pixmap = QPixmap(example["image"])
            if not pixmap.isNull():
                image.setPixmap(pixmap.scaled(400, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                image.setText("Изображение не найдено")
                image.setStyleSheet("color: #ff0000;")
            card_layout.addWidget(name)
            card_layout.addWidget(desc)
            card_layout.addWidget(image)
            card.setLayout(card_layout)
            layout.addWidget(card)
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
        self.setLayout(layout)

class HelpDialog(QDialog):
    """Диалог справки"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Справка")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel("Справка по использованию")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Текст справки
        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml("""
        <h2>Справка по использованию</h2>
        <h3>Основные действия:</h3>
        <ul>
            <li><b>Добавить блок</b> - добавляет новый блок индикатора</li>
            <li><b>Сгенерировать код</b> - создает код Pine Script для TradingView</li>
            <li><b>Пошаговый мастер</b> - помогает создать индикатор шаг за шагом</li>
            <li><b>Показать пример</b> - показывает примеры готовых индикаторов</li>
        </ul>
        <h3>Горячие клавиши:</h3>
        <ul>
            <li><b>Ctrl+N</b> - новый проект</li>
            <li><b>Ctrl+O</b> - открыть проект</li>
            <li><b>Ctrl+S</b> - сохранить проект</li>
            <li><b>Ctrl+B</b> - добавить блок</li>
            <li><b>F5</b> - сгенерировать код</li>
            <li><b>F1</b> - показать справку</li>
        </ul>
        <p>Для перемещения блоков используйте перетаскивание мышью.</p>
        
        <h3>Работа с блоками:</h3>
        <p>Каждый блок представляет собой часть индикатора. Блоки можно добавлять, удалять, дублировать и перемещать.</p>
        <p>Для добавления блока нажмите кнопку "Добавить блок" и выберите нужный тип блока.</p>
        <p>Для удаления блока нажмите кнопку "❌" в правом верхнем углу блока.</p>
        <p>Для дублирования блока нажмите кнопку "📋" в правом верхнем углу блока.</p>
        <p>Для перемещения блока перетащите его мышью в нужное место.</p>
        
        <h3>Генерация кода:</h3>
        <p>После добавления и настройки блоков нажмите кнопку "Сгенерировать код" для создания кода Pine Script.</p>
        <p>Сгенерированный код можно скопировать и вставить в редактор TradingView.</p>
        
        <h3>Сохранение и загрузка:</h3>
        <p>Для сохранения проекта нажмите "Файл" -> "Сохранить" или используйте сочетание клавиш Ctrl+S.</p>
        <p>Для загрузки проекта нажмите "Файл" -> "Открыть" или используйте сочетание клавиш Ctrl+O.</p>
        """)
        help_text.setStyleSheet("""
            QTextEdit {
                background-color: #2b2b2b;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        layout.addWidget(help_text)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class AboutDialog(QDialog):
    """Диалог "О программе" """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        self.setMinimumWidth(400)
        self.setMinimumHeight(300)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel("Конструктор индикаторов TradingView")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setStyleSheet("color: #ffffff; margin-bottom: 10px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Версия
        version = QLabel("Версия 1.0")
        version.setFont(QFont("Arial", 12))
        version.setStyleSheet("color: #aaaaaa;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)
        
        # Описание
        description = QLabel("Визуальный конструктор индикаторов для TradingView.\nСоздавайте сложные индикаторы без знания программирования!")
        description.setFont(QFont("Arial", 12))
        description.setStyleSheet("color: #ffffff; margin: 20px 0;")
        description.setAlignment(Qt.AlignCenter)
        layout.addWidget(description)
        
        # Копирайт
        copyright = QLabel("© 2023-2025 Все права защищены")
        copyright.setFont(QFont("Arial", 10))
        copyright.setStyleSheet("color: #aaaaaa;")
        copyright.setAlignment(Qt.AlignCenter)
        layout.addWidget(copyright)
        
        # Кнопка закрытия
        close_btn = QPushButton("Закрыть")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)