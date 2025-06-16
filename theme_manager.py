"""
Менеджер тем для приложения
"""

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile, QTextStream
from PyQt5.QtGui import QPalette, QColor
import os
import json
import logging
from config import get_colors, UI_THEME, UI_FONT_FAMILY, UI_TITLE_FONT_SIZE, UI_NORMAL_FONT_SIZE

class ThemeManager:
    """Класс для управления темами приложения"""
    
    @staticmethod
    def apply_theme(app):
        """Применяет тему к приложению"""
        try:
            # Загружаем CSS стили
            stylesheet = ThemeManager.load_stylesheet("styles.css")
            if stylesheet:
                app.setStyleSheet(stylesheet)
            else:
                # Если CSS файл не найден, применяем стили программно
                ThemeManager.apply_programmatic_theme(app)
        except Exception as e:
            logging.error(f"Ошибка при применении темы: {str(e)}")
            # В случае ошибки применяем базовую тему
            ThemeManager.apply_basic_theme(app)
    
    @staticmethod
    def load_stylesheet(file_path):
        """Загружает стили из CSS файла"""
        try:
            if not os.path.exists(file_path):
                return ""
                
            css_file = QFile(file_path)
            if css_file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(css_file)
                stylesheet = stream.readAll()
                css_file.close()
                return stylesheet
            return ""
        except Exception as e:
            logging.error(f"Ошибка при загрузке стилей: {str(e)}")
            return ""
    
    @staticmethod
    def apply_programmatic_theme(app):
        """Применяет тему программно"""
        colors = get_colors()
        
        # Создаем палитру
        palette = QPalette()
        
        # Устанавливаем цвета для различных элементов
        palette.setColor(QPalette.Window, QColor(colors["background"]))
        palette.setColor(QPalette.WindowText, QColor(colors["text"]))
        palette.setColor(QPalette.Base, QColor(colors["secondary_background"]))
        palette.setColor(QPalette.AlternateBase, QColor(colors["card_background"]))
        palette.setColor(QPalette.ToolTipBase, QColor(colors["card_background"]))
        palette.setColor(QPalette.ToolTipText, QColor(colors["text"]))
        palette.setColor(QPalette.Text, QColor(colors["text"]))
        palette.setColor(QPalette.Button, QColor(colors["secondary_background"]))
        palette.setColor(QPalette.ButtonText, QColor(colors["text"]))
        palette.setColor(QPalette.BrightText, QColor(colors["accent"]))
        palette.setColor(QPalette.Link, QColor(colors["accent"]))
        palette.setColor(QPalette.Highlight, QColor(colors["accent"]))
        palette.setColor(QPalette.HighlightedText, QColor(colors["text"]))
        
        # Применяем палитру
        app.setPalette(palette)
        
        # Создаем базовые стили
        stylesheet = f"""
        QWidget {{
            background-color: {colors["background"]};
            color: {colors["text"]};
            font-family: {UI_FONT_FAMILY};
            font-size: {UI_NORMAL_FONT_SIZE}px;
        }}
        
        QLabel[heading="true"] {{
            font-size: {UI_TITLE_FONT_SIZE}px;
            font-weight: bold;
        }}
        
        QPushButton {{
            background-color: {colors["success"]};
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
        }}
        
        QPushButton:hover {{
            background-color: {colors["success_hover"]};
        }}
        
        QLineEdit, QComboBox {{
            background-color: {colors["secondary_background"]};
            color: {colors["text"]};
            border: 1px solid {colors["border"]};
            border-radius: 5px;
            padding: 5px;
        }}
        
        QTextEdit {{
            background-color: {colors["secondary_background"]};
            color: {colors["text"]};
            border: 1px solid {colors["border"]};
            border-radius: 5px;
            padding: 10px;
        }}
        """
        
        # Применяем стили
        app.setStyleSheet(stylesheet)
    
    @staticmethod
    def apply_basic_theme(app):
        """Применяет базовую тему в случае ошибок"""
        if UI_THEME == "dark":
            # Темная тема
            app.setStyleSheet("""
                QWidget {
                    background-color: #1e1e1e;
                    color: #ffffff;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        else:
            # Светлая тема
            app.setStyleSheet("""
                QWidget {
                    background-color: #f5f5f5;
                    color: #212121;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #388E3C;
                }
            """)
    
    @staticmethod
    def toggle_theme():
        """Переключает тему между светлой и темной"""
        # Загружаем текущие настройки
        config_file = "config.json"
        config = {}
        
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config = json.load(f)
            except Exception as e:
                logging.error(f"Ошибка при загрузке конфигурации: {str(e)}")
        
        # Переключаем тему
        current_theme = config.get("UI_THEME", UI_THEME)
        new_theme = "light" if current_theme == "dark" else "dark"
        config["UI_THEME"] = new_theme
        
        # Сохраняем настройки
        try:
            with open(config_file, "w") as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            logging.error(f"Ошибка при сохранении конфигурации: {str(e)}")
        
        return new_theme