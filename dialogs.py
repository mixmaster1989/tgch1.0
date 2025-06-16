"""
Модуль с диалоговыми окнами для приложения
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                           QComboBox, QLineEdit, QTextEdit, QFrame, QWizard, QWizardPage,
                           QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from block import Block
from constants import BLOCK_TYPES
from code_gen import generate_code

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
            {"name": "EMA 14", "type": "Скользящая средняя", "params": {"Тип": "EMA", "Период": "14", "Источник": "close"}},
            {"name": "RSI 14", "type": "RSI", "params": {"Период": "14", "Источник": "close"}},
            {"name": "MACD стандарт", "type": "MACD", "params": {"Быстрый период": "12", "Медленный период": "26", "Сигнальный период": "9"}},
            {"name": "Bollinger Bands 20", "type": "Bollinger Bands", "params": {"Период": "20", "Множитель": "2.0", "Источник": "close"}},
            {"name": "Stochastic 14/3", "type": "Stochastic", "params": {"Период K": "14", "Период D": "3", "Замедление": "3"}},
            {"name": "ATR 14", "type": "ATR", "params": {"Период": "14"}},
            {"name": "CCI 20", "type": "CCI", "params": {"Период": "20", "Источник": "hlc3"}},
            {"name": "Объём MA 20", "type": "Объем", "params": {"Период": "20", "Порог": "2.0"}},
            {"name": "Тренд MA 50", "type": "Тренд", "params": {"Период": "50", "Порог": "2.0"}},
            {"name": "Уровень 100", "type": "Уровень", "params": {"Значение": "100", "Цвет": "red", "Стиль": "solid"}},
            {"name": "Алерт пересечение", "type": "Пересечение", "params": {"Линия 1": "close", "Линия 2": "ma", "Сообщение": "Пересечение!"}},
            {"name": "Стратегия Long", "type": "Стратегия", "params": {"Название": "Long Strategy", "Начальный капитал": "10000", "Комиссия": "0.1"}},
            {"name": "Риск 2%", "type": "Риск", "params": {"Стоп-лосс": "2.0", "Тейк-профит": "4.0", "Риск на сделку": "1.0"}},
            {"name": "Визуализация Blue", "type": "Визуализация", "params": {"Цвет линии": "blue", "Толщина": "2", "Стиль": "solid"}}
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

class WizardDialog(QWizard):
    """Пошаговый мастер создания индикатора"""
    
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
    """Первый шаг мастера - выбор типа индикатора"""
    
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
    """Второй шаг мастера - настройка параметров"""
    
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
    """Третий шаг мастера - получение кода"""
    
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