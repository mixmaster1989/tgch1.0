"""
Главный модуль пользовательского интерфейса
"""

import sys
import os
import json
import logging
import traceback
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QComboBox, QLineEdit, QTextEdit, QScrollArea,
                            QFrame, QMessageBox, QToolButton, QToolTip, QSizePolicy, QDialog, 
                            QDialogButtonBox, QWizard, QWizardPage, QFileDialog, QAction, QMenu,
                            QStatusBar)
from PyQt5.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette, QPixmap, QKeySequence
from block import Block
from block_widget import BlockWidget
from code_gen import generate_code
from constants import BLOCK_TYPES
from utils import validate_code, show_info_message, backup_project
from error_handler import setup_error_handling, show_error_dialog
from dialogs import BlockSelectDialog, WizardDialog, ExampleDialog, HelpDialog, AboutDialog
from autosave import autosave
from preview import PreviewDialog

# Настройка обработки ошибок
setup_error_handling()

class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.setup_ui()
        
        # Запускаем автосохранение
        autosave.start(self.get_blocks)
        
        # Проверяем наличие автосохранения
        self.check_autosave()
        
        # Устанавливаем таймер для обновления статусной строки
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(1000)  # Обновление каждую секунду
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle("Конструктор индикаторов TradingView")
        self.setMinimumSize(800, 600)
        
        # Создаем меню
        self.create_menu()
        
        # Создаем статусную строку
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Готово")
        
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
        title.setProperty("heading", True)
        layout.addWidget(title)
        
        # Описание
        description = QLabel("Создавайте индикаторы для TradingView без знания программирования!")
        description.setFont(QFont("Arial", 14))
        description.setAlignment(Qt.AlignCenter)
        description.setStyleSheet("color: #aaaaaa; margin-bottom: 20px;")
        description.setProperty("subheading", True)
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
        add_block_btn.setProperty("primary", True)
        add_block_btn.clicked.connect(self.add_block)
        buttons_layout.addWidget(add_block_btn)
        
        # Кнопка пошагового мастера
        wizard_btn = QPushButton("🧙 Пошаговый мастер")
        wizard_btn.setFont(QFont("Arial", 12))
        wizard_btn.setProperty("secondary", True)
        wizard_btn.clicked.connect(self.show_wizard)
        buttons_layout.addWidget(wizard_btn)
        
        # Кнопка показа примера
        example_btn = QPushButton("📊 Показать пример")
        example_btn.setFont(QFont("Arial", 12))
        example_btn.setProperty("warning", True)
        example_btn.clicked.connect(self.show_example)
        buttons_layout.addWidget(example_btn)
        
        # Кнопка предпросмотра
        preview_btn = QPushButton("👁️ Предпросмотр")
        preview_btn.setFont(QFont("Arial", 12))
        preview_btn.setProperty("warning", True)
        preview_btn.clicked.connect(self.show_preview)
        buttons_layout.addWidget(preview_btn)
        
        # Кнопка генерации кода
        generate_btn = QPushButton("⚡ Сгенерировать код")
        generate_btn.setFont(QFont("Arial", 12))
        generate_btn.setProperty("primary", True)
        generate_btn.clicked.connect(self.generate_code)
        buttons_layout.addWidget(generate_btn)
        
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
    
    def create_menu(self):
        """Создает главное меню приложения"""
        menubar = self.menuBar()
        
        # Меню "Файл"
        file_menu = menubar.addMenu("Файл")
        
        new_action = QAction("Новый проект", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("Открыть...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.import_settings)
        file_menu.addAction(open_action)
        
        save_action = QAction("Сохранить...", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.export_settings)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        backup_action = QAction("Создать резервную копию", self)
        backup_action.triggered.connect(self.create_backup)
        file_menu.addAction(backup_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Выход", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Меню "Редактирование"
        edit_menu = menubar.addMenu("Редактирование")
        
        add_block_action = QAction("Добавить блок", self)
        add_block_action.setShortcut("Ctrl+B")
        add_block_action.triggered.connect(self.add_block)
        edit_menu.addAction(add_block_action)
        
        generate_code_action = QAction("Сгенерировать код", self)
        generate_code_action.setShortcut("F5")
        generate_code_action.triggered.connect(self.generate_code)
        edit_menu.addAction(generate_code_action)
        
        edit_menu.addSeparator()
        
        copy_code_action = QAction("Копировать код", self)
        copy_code_action.setShortcut("Ctrl+Shift+C")
        copy_code_action.triggered.connect(self.copy_code)
        edit_menu.addAction(copy_code_action)
        
        # Меню "Инструменты"
        tools_menu = menubar.addMenu("Инструменты")
        
        wizard_action = QAction("Пошаговый мастер", self)
        wizard_action.triggered.connect(self.show_wizard)
        tools_menu.addAction(wizard_action)
        
        example_action = QAction("Примеры индикаторов", self)
        example_action.triggered.connect(self.show_example)
        tools_menu.addAction(example_action)
        
        preview_action = QAction("Предпросмотр", self)
        preview_action.triggered.connect(self.show_preview)
        tools_menu.addAction(preview_action)
        
        # Меню "Справка"
        help_menu = menubar.addMenu("Справка")
        
        help_action = QAction("Справка", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        about_action = QAction("О программе", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def add_block(self):
        """Добавляет новый блок"""
        dialog = BlockSelectDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_type:
            if hasattr(dialog, 'selected_params'):
                self.create_block(dialog.selected_type, dialog.selected_params)
            else:
                self.create_block(dialog.selected_type)
    
    def create_block(self, block_type, params=None):
        """Создает новый блок"""
        block = Block(block_type)
        if params:
            block.params.update(params)
        elif "default_values" in BLOCK_TYPES[block_type]:
            block.params.update(BLOCK_TYPES[block_type]["default_values"])
        self.blocks.append(block)
        self.update_blocks()
        self.statusBar.showMessage(f"Добавлен блок: {block_type}")
    
    def remove_block(self, block_widget):
        """Удаляет блок"""
        index = self.blocks_widget.layout().indexOf(block_widget)
        if index != -1:
            block_type = self.blocks[index].type
            self.blocks.pop(index)
            self.update_blocks()
            self.statusBar.showMessage(f"Удален блок: {block_type}")
    
    def duplicate_block(self, block_widget):
        """Дублирует блок"""
        index = self.blocks_widget.layout().indexOf(block_widget)
        if index != -1:
            # Создаем копию блока
            original_block = self.blocks[index]
            new_block = original_block.duplicate()
            # Добавляем новый блок после текущего
            self.blocks.insert(index + 1, new_block)
            self.update_blocks()
            self.statusBar.showMessage(f"Дублирован блок: {original_block.type}")
    
    def move_block(self, source_index, target_index):
        """Перемещает блок с одной позиции на другую"""
        if 0 <= source_index < len(self.blocks) and 0 <= target_index < len(self.blocks):
            # Извлекаем блок из исходной позиции
            block = self.blocks.pop(source_index)
            # Вставляем блок в целевую позицию
            self.blocks.insert(target_index, block)
            # Обновляем отображение
            self.update_blocks()
            self.statusBar.showMessage(f"Перемещен блок: {block.type}")
    
    def update_blocks(self):
        """Обновляет отображение блоков"""
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
        """Генерирует код Pine Script на основе блоков"""
        try:
            if not self.blocks:
                show_info_message(self, "Генерация кода", "Добавьте хотя бы один блок для генерации кода.")
                return
                
            code = generate_code(self.blocks)
            self.code_area.setText(code)
            
            # Валидация кода
            errors = validate_code(code)
            if errors:
                error_text = '\n'.join(errors)
                show_error_dialog(self, error_text)
            else:
                show_info_message(self, "Генерация кода", "Код успешно сгенерирован!")
                self.statusBar.showMessage("Код успешно сгенерирован")
        except Exception as e:
            tb_str = traceback.format_exc()
            logging.error(tb_str)
            show_error_dialog(self, tb_str)
    
    def copy_code(self):
        """Копирует сгенерированный код в буфер обмена"""
        code = self.code_area.toPlainText()
        if code:
            clipboard = QApplication.clipboard()
            clipboard.setText(code)
            self.statusBar.showMessage("Код скопирован в буфер обмена")
            show_info_message(self, "Копирование кода", "Код скопирован в буфер обмена.")
        else:
            show_info_message(self, "Копирование кода", "Нет кода для копирования. Сначала сгенерируйте код.")
    
    def show_wizard(self):
        """Показывает пошаговый мастер"""
        wizard = WizardDialog(self)
        wizard.exec_()
    
    def show_example(self):
        """Показывает примеры индикаторов"""
        dialog = ExampleDialog(self)
        dialog.exec_()
    
    def show_preview(self):
        """Показывает предварительный просмотр индикатора"""
        if not self.blocks:
            show_info_message(self, "Предпросмотр", "Добавьте хотя бы один блок для предпросмотра.")
            return
            
        dialog = PreviewDialog(self.blocks, self)
        dialog.exec_()
    
    def show_help(self):
        """Показывает справку"""
        dialog = HelpDialog(self)
        dialog.exec_()
    
    def show_about(self):
        """Показывает информацию о программе"""
        dialog = AboutDialog(self)
        dialog.exec_()
    
    def export_settings(self):
        """Экспортирует настройки в файл"""
        if not self.blocks:
            show_info_message(self, "Экспорт", "Нет блоков для экспорта.")
            return
            
        file_name, _ = QFileDialog.getSaveFileName(self, "Экспорт настроек", "", "JSON Files (*.json)")
        if file_name:
            try:
                settings = []
                for block in self.blocks:
                    settings.append(block.get_data())
                
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=4, ensure_ascii=False)
                
                self.statusBar.showMessage(f"Настройки экспортированы в {file_name}")
                show_info_message(self, "Экспорт", f"Настройки успешно экспортированы в {file_name}.")
            except Exception as e:
                logging.error(f"Ошибка при экспорте настроек: {str(e)}")
                show_error_dialog(self, f"Ошибка при экспорте настроек: {str(e)}")
    
    def import_settings(self):
        """Импортирует настройки из файла"""
        file_name, _ = QFileDialog.getOpenFileName(self, "Импорт настроек", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                self.blocks = []
                for s in settings:
                    if "type" in s and "params" in s:
                        block = Block(s["type"], s["params"])
                        self.blocks.append(block)
                
                self.update_blocks()
                self.statusBar.showMessage(f"Настройки импортированы из {file_name}")
                show_info_message(self, "Импорт", f"Настройки успешно импортированы из {file_name}.")
            except Exception as e:
                logging.error(f"Ошибка при импорте настроек: {str(e)}")
                show_error_dialog(self, f"Ошибка при импорте настроек: {str(e)}")
    
    def new_project(self):
        """Создает новый проект"""
        if self.blocks:
            reply = QMessageBox.question(self, "Новый проект", 
                                        "Вы уверены, что хотите создать новый проект? Все несохраненные изменения будут потеряны.",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.blocks = []
                self.update_blocks()
                self.code_area.clear()
                self.statusBar.showMessage("Создан новый проект")
    
    def create_backup(self):
        """Создает резервную копию проекта"""
        backup_path = backup_project()
        if backup_path:
            self.statusBar.showMessage(f"Резервная копия создана в {backup_path}")
            show_info_message(self, "Резервное копирование", f"Резервная копия создана в директории: {backup_path}")
        else:
            show_error_dialog(self, "Ошибка при создании резервной копии.")
    
    def get_blocks(self):
        """Возвращает список блоков для автосохранения"""
        return self.blocks
    
    def check_autosave(self):
        """Проверяет наличие автосохранения"""
        blocks = autosave.load_autosave(Block)
        if blocks:
            reply = QMessageBox.question(self, "Автосохранение", 
                                        "Найдено автосохранение. Хотите восстановить последнюю сессию?",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.blocks = blocks
                self.update_blocks()
                self.statusBar.showMessage("Восстановлена последняя сессия из автосохранения")
    
    def update_status(self):
        """Обновляет статусную строку"""
        if not self.statusBar.currentMessage():
            self.statusBar.showMessage(f"Блоков: {len(self.blocks)}")
    
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        # Останавливаем автосохранение
        autosave.stop()
        
        # Проверяем, есть ли несохраненные изменения
        if self.blocks:
            reply = QMessageBox.question(self, "Выход", 
                                        "У вас есть несохраненные изменения. Хотите сохранить проект перед выходом?",
                                        QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.export_settings()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())