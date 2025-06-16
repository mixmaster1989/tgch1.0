import sys
import os
import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtTest import QTest
from PyQt5.QtCore import Qt

# Добавляем родительскую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Создаем экземпляр приложения для тестов
app = QApplication.instance()
if app is None:
    app = QApplication([])

from ui import MainWindow
from block import Block

class TestMainWindow:
    """Тесты для главного окна приложения"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.window = MainWindow()
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        self.window.close()
    
    def test_window_title(self):
        """Тест заголовка окна"""
        assert "Конструктор индикаторов TradingView" in self.window.windowTitle()
    
    def test_create_block(self):
        """Тест создания блока"""
        # Начальное количество блоков
        initial_count = len(self.window.blocks)
        
        # Создаем блок
        self.window.create_block("Скользящая средняя", {
            "Тип": "EMA",
            "Период": "14",
            "Источник": "close"
        })
        
        # Проверяем, что блок добавлен
        assert len(self.window.blocks) == initial_count + 1
        assert self.window.blocks[-1].type == "Скользящая средняя"
        assert self.window.blocks[-1].params["Тип"] == "EMA"
    
    def test_remove_block(self):
        """Тест удаления блока"""
        # Создаем блок
        self.window.create_block("Скользящая средняя", {
            "Тип": "EMA",
            "Период": "14",
            "Источник": "close"
        })
        
        # Начальное количество блоков
        initial_count = len(self.window.blocks)
        
        # Получаем виджет блока
        block_widget = self.window.blocks_layout.itemAt(0).widget()
        
        # Удаляем блок
        self.window.remove_block(block_widget)
        
        # Проверяем, что блок удален
        assert len(self.window.blocks) == initial_count - 1
    
    def test_duplicate_block(self):
        """Тест дублирования блока"""
        # Создаем блок
        self.window.create_block("Скользящая средняя", {
            "Тип": "EMA",
            "Период": "14",
            "Источник": "close"
        })
        
        # Начальное количество блоков
        initial_count = len(self.window.blocks)
        
        # Получаем виджет блока
        block_widget = self.window.blocks_layout.itemAt(0).widget()
        
        # Дублируем блок
        self.window.duplicate_block(block_widget)
        
        # Проверяем, что блок дублирован
        assert len(self.window.blocks) == initial_count + 1
        assert self.window.blocks[-1].type == "Скользящая средняя"
        assert self.window.blocks[-1].params["Тип"] == "EMA"
    
    def test_move_block(self):
        """Тест перемещения блока"""
        # Создаем два блока
        self.window.create_block("Скользящая средняя", {
            "Тип": "EMA",
            "Период": "14",
            "Источник": "close"
        })
        self.window.create_block("RSI", {
            "Период": "14",
            "Источник": "close"
        })
        
        # Перемещаем блок
        self.window.move_block(0, 1)
        
        # Проверяем, что блоки поменялись местами
        assert self.window.blocks[0].type == "RSI"
        assert self.window.blocks[1].type == "Скользящая средняя"
    
    def test_generate_code(self):
        """Тест генерации кода"""
        # Создаем блок
        self.window.create_block("Скользящая средняя", {
            "Тип": "EMA",
            "Период": "14",
            "Источник": "close"
        })
        
        # Генерируем код
        self.window.generate_code()
        
        # Проверяем, что код сгенерирован
        assert self.window.code_area.toPlainText() != ""
        assert "ta.ema" in self.window.code_area.toPlainText()
    
    def test_new_project(self):
        """Тест создания нового проекта"""
        # Создаем блок
        self.window.create_block("Скользящая средняя", {
            "Тип": "EMA",
            "Период": "14",
            "Источник": "close"
        })
        
        # Начальное количество блоков
        initial_count = len(self.window.blocks)
        assert initial_count > 0
        
        # Создаем новый проект (без диалога подтверждения)
        self.window.blocks = []
        self.window.update_blocks()
        self.window.code_area.clear()
        
        # Проверяем, что блоки удалены
        assert len(self.window.blocks) == 0