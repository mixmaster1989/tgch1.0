import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QComboBox, QLineEdit, QTextEdit, QScrollArea,
                            QFrame, QMessageBox, QToolButton, QToolTip, QSizePolicy, QDialog, QDialogButtonBox, QWizard, QWizardPage, QFileDialog)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPixmap
from block import Block
from code_gen import generate_code, validate_code
from constants import BLOCK_TYPES
import traceback
import logging

# Настройка логирования ошибок
logging.basicConfig(filename='error.log', level=logging.ERROR, format='%(asctime)s %(levelname)s:%(message)s')

def show_error_dialog(parent, error):
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle("Ошибка")
    msg.setText("Произошла ошибка!")
    msg.setDetailedText(str(error))
    msg.exec_()

# Глобальный обработчик исключений
def excepthook(exc_type, exc_value, exc_tb):
    tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logging.error(tb_str)
    app = QApplication.instance()
    if app is not None and app.activeWindow() is not None:
        show_error_dialog(app.activeWindow(), tb_str)
    else:
        print(tb_str)

sys.excepthook = excepthook

class TemplateDialog(QDialog):
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
            {"name": "EMA 14", "type": "Скользящая средняя (MA)", "params": {"Тип": "EMA", "Длина": 14, "Источник": "close"}},
            {"name": "RSI 14", "type": "RSI (индекс относительной силы)", "params": {"Длина": 14}},
            {"name": "MACD стандарт", "type": "MACD (схождение/расхождение)", "params": {"Быстрая длина": 12, "Медленная длина": 26, "Сигнальная длина": 9}},
            {"name": "Bollinger Bands 20", "type": "Bollinger Bands (полосы Боллинджера)", "params": {"Длина": 20, "Множитель": 2}},
            {"name": "Stochastic 14/3", "type": "Stochastic (стохастический осциллятор)", "params": {"Длина %K": 14, "Длина %D": 3}},
            {"name": "ATR 14", "type": "ATR (средний истинный диапазон)", "params": {"Длина": 14}},
            {"name": "CCI 20", "type": "CCI (индекс товарного канала)", "params": {"Длина": 20}},
            {"name": "Объём MA 20", "type": "Объём (анализ объёма)", "params": {"Длина": 20}},
            {"name": "Тренд MA 50", "type": "Тренд (определение тренда)", "params": {"Длина": 50}},
            {"name": "Уровень 100", "type": "Уровень (горизонтальные линии)", "params": {"Уровень": 100}},
            {"name": "Алерт пересечение", "type": "Пересечение (сигналы)", "params": {"Линия 1": "close", "Линия 2": "ma"}},
            {"name": "Стратегия Long", "type": "Стратегия (торговые настройки)", "params": {"Тип стратегии": "long"}},
            {"name": "Риск 2%", "type": "Риск (управление рисками)", "params": {"Процент риска": 2}},
            {"name": "Визуализация Blue", "type": "Визуализация (настройки отображения)", "params": {"Цвет": "blue"}}
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
            layout.addWidget(card)

        self.setLayout(layout)

    def select_type(self, block_type):
        self.selected_type = block_type
        self.accept()

    def show_templates(self):
        dialog = TemplateDialog(self)
        if dialog.exec_() == QDialog.Accepted and hasattr(dialog, 'selected_template'):
            self.selected_type = dialog.selected_template["type"]
            self.selected_params = dialog.selected_template["params"]
            self.accept()

class BlockWidget(QFrame):
    def __init__(self, block, parent=None):
        super().__init__(parent)
        self.block = block
        self.setup_ui()
        
    def setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b2b;
                border: 2px solid #3d3d3d;
                border-radius: 10px;
                padding: 10px;
                margin: 5px;
            }
            QFrame:hover {
                border: 2px solid #4a4a4a;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QLineEdit, QComboBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #4a4a4a;
                border-radius: 5px;
                padding: 5px;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #5a5a5a;
            }
            QToolButton {
                background-color: transparent;
                border: none;
                color: #ffffff;
                font-size: 14px;
            }
            QToolButton:hover {
                color: #00ff00;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Заголовок блока
        header = QHBoxLayout()
        icon_label = QLabel(BLOCK_TYPES[self.block.type]["icon"])
        icon_label.setFont(QFont("Arial", 16))
        title_label = QLabel(self.block.type)
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        description_label = QLabel(BLOCK_TYPES[self.block.type]["description"])
        description_label.setWordWrap(True)
        description_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        
        header.addWidget(icon_label)
        header.addWidget(title_label)
        header.addStretch()
        
        # Кнопка удаления
        delete_btn = QToolButton()
        delete_btn.setText("❌")
        delete_btn.setToolTip("Удалить блок")
        delete_btn.clicked.connect(self.delete_block)
        header.addWidget(delete_btn)
        
        layout.addLayout(header)
        layout.addWidget(description_label)
        
        # Параметры блока
        for param in BLOCK_TYPES[self.block.type]["params"]:
            param_layout = QVBoxLayout()
            row = QHBoxLayout()
            
            # Название параметра
            name_label = QLabel(param["name"])
            name_label.setMinimumWidth(150)
            
            # Подсказка
            help_btn = QToolButton()
            help_btn.setText("❓")
            help_btn.setToolTip(param.get("help", ""))
            
            # Поле ввода
            if "values" in param:
                input_widget = QComboBox()
                input_widget.addItems(param["values"])
                if param["name"] in self.block.params:
                    input_widget.setCurrentText(self.block.params[param["name"]])
                input_widget.currentTextChanged.connect(
                    lambda text, p=param["name"]: self.update_param(p, text))
            else:
                input_widget = QLineEdit()
                if param["name"] in self.block.params:
                    input_widget.setText(str(self.block.params[param["name"]]))
                input_widget.textChanged.connect(
                    lambda text, p=param["name"]: self.update_param(p, text))
                if "placeholder" in param:
                    input_widget.setPlaceholderText(param["placeholder"])
            
            row.addWidget(name_label)
            row.addWidget(help_btn)
            row.addWidget(input_widget)
            param_layout.addLayout(row)
            
            # Пояснение и пример
            if "description" in param:
                desc = QLabel(param["description"])
                desc.setStyleSheet("color: #aaa; font-size: 12px;")
                param_layout.addWidget(desc)
            
            if "help" in param:
                example = QLabel("Пример: " + param["help"].split("\n")[0])
                example.setStyleSheet("color: #6cf; font-size: 12px;")
                param_layout.addWidget(example)
            
            layout.addLayout(param_layout)
        
        self.setLayout(layout)
    
    def update_param(self, name, value):
        self.block.params[name] = value
    
    def delete_block(self):
        if self.parent():
            self.parent().remove_block(self)

class WizardDialog(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Пошаговый мастер создания индикатора")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
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
        self.addPage(Step1Page())
        self.addPage(Step2Page())
        self.addPage(Step3Page())

class Step1Page(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Шаг 1: Выберите тип индикатора")
        layout = QVBoxLayout()
        self.combo = QComboBox()
        for block_type in BLOCK_TYPES.keys():
            self.combo.addItem(block_type)
        layout.addWidget(QLabel("Выберите тип индикатора:"))
        layout.addWidget(self.combo)
        self.setLayout(layout)
        self.registerField("block_type", self.combo, "currentText")

class Step2Page(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Шаг 2: Настройте параметры")
        layout = QVBoxLayout()
        self.params_layout = QVBoxLayout()
        layout.addLayout(self.params_layout)
        self.setLayout(layout)

    def initializePage(self):
        # Очищаем предыдущие параметры
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        block_type = self.field("block_type")
        if block_type in BLOCK_TYPES:
            for param in BLOCK_TYPES[block_type]["params"]:
                row = QHBoxLayout()
                name_label = QLabel(param["name"])
                name_label.setMinimumWidth(150)
                if "values" in param:
                    input_widget = QComboBox()
                    input_widget.addItems(param["values"])
                else:
                    input_widget = QLineEdit()
                    if "placeholder" in param:
                        input_widget.setPlaceholderText(param["placeholder"])
                row.addWidget(name_label)
                row.addWidget(input_widget)
                self.params_layout.addLayout(row)
                self.registerField(f"param_{param['name']}", input_widget)

class Step3Page(QWizardPage):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTitle("Шаг 3: Получите код")
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
        self.setLayout(layout)

    def initializePage(self):
        block_type = self.field("block_type")
        block = Block(block_type)
        for param in BLOCK_TYPES[block_type]["params"]:
            value = self.field(f"param_{param['name']}")
            block.params[param["name"]] = value
        code = generate_code([block])
        self.code_area.setText(code)

class ExampleDialog(QDialog):
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
            },
            {
                "name": "ATR 14",
                "description": "Средний истинный диапазон с периодом 14. Показывает волатильность рынка.",
                "image": "examples/atr14.png"
            },
            {
                "name": "CCI 20",
                "description": "Индекс товарного канала с периодом 20. Показывает перекупленность/перепроданность и моментум.",
                "image": "examples/cci20.png"
            },
            {
                "name": "Объём MA 20",
                "description": "Скользящая средняя объёма с периодом 20. Показывает силу тренда и объём торгов.",
                "image": "examples/volma20.png"
            },
            {
                "name": "Тренд MA 50",
                "description": "Скользящая средняя с периодом 50. Показывает долгосрочный тренд и уровни поддержки/сопротивления.",
                "image": "examples/ma50.png"
            },
            {
                "name": "Уровень 100",
                "description": "Горизонтальная линия на уровне 100. Используется для определения уровней поддержки/сопротивления.",
                "image": "examples/level100.png"
            },
            {
                "name": "Алерт пересечение",
                "description": "Алерт при пересечении цены и скользящей средней. Показывает моменты входа в рынок.",
                "image": "examples/cross.png"
            },
            {
                "name": "Стратегия Long",
                "description": "Стратегия для длинных позиций. Показывает точки входа и выхода из рынка.",
                "image": "examples/long.png"
            },
            {
                "name": "Риск 2%",
                "description": "Управление рисками с максимальной просадкой 2%. Показывает безопасные уровни для торговли.",
                "image": "examples/risk2.png"
            },
            {
                "name": "Визуализация Blue",
                "description": "Настройки отображения с синим цветом. Показывает, как будет выглядеть индикатор на графике.",
                "image": "examples/blue.png"
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Конструктор индикаторов TradingView")
        self.setMinimumSize(800, 600)
        
        # Основной виджет
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Главный layout
        layout = QVBoxLayout()
        
        # Заголовок
        title = QLabel("Конструктор индикаторов TradingView")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #ffffff; margin: 20px;")
        layout.addWidget(title)
        
        # Описание
        description = QLabel("Создавайте индикаторы для TradingView без знания программирования!")
        description.setFont(QFont("Arial", 14))
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #aaaaaa; margin-bottom: 20px;")
        layout.addWidget(description)
        
        # Область для блоков
        self.blocks_area = QScrollArea()
        self.blocks_area.setWidgetResizable(True)
        self.blocks_area.setStyleSheet("""
            QScrollArea {
                background-color: #1e1e1e;
                border: none;
            }
        """)
        
        self.blocks_widget = QWidget()
        self.blocks_layout = QVBoxLayout()
        self.blocks_widget.setLayout(self.blocks_layout)
        self.blocks_area.setWidget(self.blocks_widget)
        layout.addWidget(self.blocks_area)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        # Кнопка добавления блока
        add_block_btn = QPushButton("➕ Добавить блок")
        add_block_btn.setFont(QFont("Arial", 12))
        add_block_btn.setStyleSheet("""
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
        add_block_btn.clicked.connect(self.add_block)
        buttons_layout.addWidget(add_block_btn)
        
        # Кнопка пошагового мастера
        wizard_btn = QPushButton("🧙 Пошаговый мастер")
        wizard_btn.setFont(QFont("Arial", 12))
        wizard_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        wizard_btn.clicked.connect(self.show_wizard)
        buttons_layout.addWidget(wizard_btn)
        
        # Кнопка показа примера
        example_btn = QPushButton("📊 Показать пример")
        example_btn.setFont(QFont("Arial", 12))
        example_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
        """)
        example_btn.clicked.connect(self.show_example)
        buttons_layout.addWidget(example_btn)
        
        # Кнопка генерации кода
        generate_btn = QPushButton("⚡ Сгенерировать код")
        generate_btn.setFont(QFont("Arial", 12))
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        generate_btn.clicked.connect(self.generate_code)
        buttons_layout.addWidget(generate_btn)
        
        # Кнопка экспорта
        export_btn = QPushButton("💾 Экспорт")
        export_btn.setFont(QFont("Arial", 12))
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        export_btn.clicked.connect(self.export_settings)
        buttons_layout.addWidget(export_btn)
        
        # Кнопка импорта
        import_btn = QPushButton("📂 Импорт")
        import_btn.setFont(QFont("Arial", 12))
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
        """)
        import_btn.clicked.connect(self.import_settings)
        buttons_layout.addWidget(import_btn)
        
        layout.addLayout(buttons_layout)
        
        # Область для кода
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
        
        main_widget.setLayout(layout)
        
        # Устанавливаем тёмную тему
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
            }
        """)
    
    def add_block(self):
        dialog = BlockSelectDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_type:
            if hasattr(dialog, 'selected_params'):
                self.create_block(dialog.selected_type, dialog.selected_params)
            else:
                self.create_block(dialog.selected_type)
    
    def create_block(self, block_type, params=None):
        block = Block(block_type)
        if params:
            block.params.update(params)
        elif "default_values" in BLOCK_TYPES[block_type]:
            block.params.update(BLOCK_TYPES[block_type]["default_values"])
        self.blocks.append(block)
        self.update_blocks()
    
    def remove_block(self, block_widget):
        index = self.blocks_widget.layout().indexOf(block_widget)
        if index != -1:
            self.blocks.pop(index)
            self.update_blocks()
    
    def update_blocks(self):
        # Очищаем текущие блоки
        while self.blocks_layout.count():
            item = self.blocks_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Добавляем блоки заново
        for block in self.blocks:
            block_widget = BlockWidget(block)
            self.blocks_layout.addWidget(block_widget)
        
        # Добавляем растягивающийся элемент
        self.blocks_layout.addStretch()
    
    def generate_code(self):
        try:
            code = generate_code(self.blocks)
            self.code_area.setText(code)
            # Валидация кода
            errors = validate_code(code)
            if errors:
                show_error_dialog(self, '\n'.join(errors))
        except Exception as e:
            tb_str = traceback.format_exc()
            logging.error(tb_str)
            show_error_dialog(self, tb_str)

    def show_wizard(self):
        wizard = WizardDialog(self)
        wizard.exec_()

    def show_example(self):
        dialog = ExampleDialog(self)
        dialog.exec_()

    def export_settings(self):
        file_name, _ = QFileDialog.getSaveFileName(self, "Экспорт настроек", "", "JSON Files (*.json)")
        if file_name:
            settings = [{"type": block.type, "params": block.params} for block in self.blocks]
            with open(file_name, 'w') as f:
                json.dump(settings, f, indent=4)

    def import_settings(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Импорт настроек", "", "JSON Files (*.json)")
        if file_name:
            with open(file_name, 'r') as f:
                settings = json.load(f)
            self.blocks = [Block(s["type"], s["params"]) for s in settings]
            self.update_blocks()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 