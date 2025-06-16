from PyQt5.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, 
                            QLabel, QComboBox, QLineEdit, QToolButton,
                            QApplication)
from PyQt5.QtCore import Qt, QPoint, QMimeData
from PyQt5.QtGui import QFont, QDrag
from constants import BLOCK_TYPES

class BlockWidget(QFrame):
    """Виджет для отображения блока в интерфейсе PyQt5"""
    
    def __init__(self, block, parent=None):
        """
        Инициализация виджета блока
        
        Args:
            block: Блок для отображения
            parent: Родительский виджет
        """
        super().__init__(parent)
        self.block = block
        self.drag_start_position = None
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Настройка внешнего вида
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
        
        # Кнопка дублирования
        duplicate_btn = QToolButton()
        duplicate_btn.setText("📋")
        duplicate_btn.setToolTip("Дублировать блок")
        duplicate_btn.clicked.connect(self.duplicate_block)
        header.addWidget(duplicate_btn)
        
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
                    input_widget.setCurrentText(str(self.block.params[param["name"]]))
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
                example = QLabel("Пример: " + param["help"].split("\\n")[0])
                example.setStyleSheet("color: #6cf; font-size: 12px;")
                param_layout.addWidget(example)
            
            layout.addLayout(param_layout)
        
        self.setLayout(layout)
    
    def update_param(self, name, value):
        """Обновляет параметр блока"""
        self.block.update_param(name, value)
    
    def delete_block(self):
        """Удаляет блок"""
        if self.parent():
            self.parent().remove_block(self)
            
    def duplicate_block(self):
        """Дублирует блок"""
        if self.parent():
            self.parent().duplicate_block(self)
    
    # Реализация Drag&Drop
    def mousePressEvent(self, event):
        """Обработка нажатия кнопки мыши"""
        if event.button() == Qt.LeftButton:
            self.drag_start_position = event.pos()
    
    def mouseMoveEvent(self, event):
        """Обработка перемещения мыши"""
        if not (event.buttons() & Qt.LeftButton) or not self.drag_start_position:
            return
        
        # Проверяем, достаточно ли далеко переместилась мышь для начала перетаскивания
        if (event.pos() - self.drag_start_position).manhattanLength() < QApplication.startDragDistance():
            return
        
        # Создаем объект перетаскивания
        drag = QDrag(self)
        mime_data = QMimeData()
        
        # Сохраняем индекс блока для идентификации
        index = self.parent().layout().indexOf(self)
        mime_data.setText(str(index))
        
        drag.setMimeData(mime_data)
        
        # Устанавливаем полупрозрачность при перетаскивании
        pixmap = self.grab()
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos())
        
        # Выполняем перетаскивание
        drop_action = drag.exec_(Qt.MoveAction)
    
    def dragEnterEvent(self, event):
        """Обработка входа перетаскиваемого объекта"""
        if event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Обработка сброса перетаскиваемого объекта"""
        if event.mimeData().hasText():
            # Получаем индекс перетаскиваемого блока
            source_index = int(event.mimeData().text())
            # Получаем индекс текущего блока (куда перетаскиваем)
            target_index = self.parent().layout().indexOf(self)
            
            # Перемещаем блок в списке
            if self.parent() and hasattr(self.parent(), 'move_block'):
                self.parent().move_block(source_index, target_index)
                
            event.acceptProposedAction()