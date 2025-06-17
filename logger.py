"""
Улучшенный модуль логирования для приложения
"""

import logging
import os
import sys
import traceback
from datetime import datetime
from PyQt5.QtWidgets import QMessageBox, QApplication
from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT

class Logger:
    """Класс для управления логированием в приложении"""
    
    _instance = None
    _initialized = False
    
    @staticmethod
    def get_instance():
        """Получение экземпляра логгера (паттерн Singleton)"""
        if Logger._instance is None:
            Logger._instance = Logger()
        return Logger._instance
    
    def __init__(self):
        """Инициализация логгера"""
        if not Logger._initialized:
            self.setup_logging()
            Logger._initialized = True
    
    def setup_logging(self):
        """Настройка логирования"""
        # Создаем директорию для логов, если она не существует
        log_dir = os.path.dirname(LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except Exception as e:
                print(f"Ошибка при создании директории для логов: {str(e)}")
        
        # Определяем уровень логирования
        level = getattr(logging, LOG_LEVEL.upper(), logging.ERROR)
        
        # Настраиваем логирование
        logging.basicConfig(
            filename=LOG_FILE,
            level=level,
            format=LOG_FORMAT
        )
        
        # Добавляем вывод в консоль для отладки
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_formatter = logging.Formatter(LOG_FORMAT)
        console_handler.setFormatter(console_formatter)
        
        # Получаем корневой логгер и добавляем обработчик
        root_logger = logging.getLogger()
        root_logger.addHandler(console_handler)
        
        # Не устанавливаем sys.excepthook здесь, чтобы избежать конфликта с error_handler.py
    
    def exception_handler(self, exc_type, exc_value, exc_tb):
        """Глобальный обработчик исключений"""
        tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        self.error(tb_str)
        
        # Показываем диалог с ошибкой, если приложение запущено
        app = QApplication.instance()
        if app is not None and app.activeWindow() is not None:
            self.show_error_dialog(app.activeWindow(), tb_str)
        else:
            print(tb_str)
    
    def show_error_dialog(self, parent, error):
        """Показывает диалог с ошибкой"""
        try:
            msg = QMessageBox(parent)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка")
            msg.setText("Произошла ошибка!")
            msg.setInformativeText("Подробная информация об ошибке записана в лог-файл.")
            msg.setDetailedText(str(error))
            msg.exec_()
        except Exception as e:
            print(f"Ошибка при отображении диалога ошибки: {str(e)}")
    
    def debug(self, message):
        """Логирование отладочного сообщения"""
        logging.debug(message)
    
    def info(self, message):
        """Логирование информационного сообщения"""
        logging.info(message)
    
    def warning(self, message):
        """Логирование предупреждения"""
        logging.warning(message)
    
    def error(self, message):
        """Логирование ошибки"""
        logging.error(message)
    
    def critical(self, message):
        """Логирование критической ошибки"""
        logging.critical(message)
    
    def log_exception(self, e, message=None):
        """Логирование исключения с трассировкой стека"""
        tb_str = traceback.format_exc()
        if message:
            self.error(f"{message}: {str(e)}\n{tb_str}")
        else:
            self.error(f"Исключение: {str(e)}\n{tb_str}")
    
    def log_function_call(self, func):
        """Декоратор для логирования вызовов функций"""
        def wrapper(*args, **kwargs):
            self.debug(f"Вызов функции {func.__name__}")
            try:
                result = func(*args, **kwargs)
                self.debug(f"Функция {func.__name__} успешно выполнена")
                return result
            except Exception as e:
                self.log_exception(e, f"Ошибка в функции {func.__name__}")
                raise
        return wrapper
    
    def handle_exception(self, func):
        """Декоратор для обработки исключений в функциях"""
        def wrapper(instance, *args, **kwargs):
            try:
                return func(instance, *args, **kwargs)
            except Exception as e:
                self.log_exception(e, f"Ошибка в методе {func.__name__}")
                self.show_error_dialog(instance, str(e))
        return wrapper

# Создаем глобальный экземпляр логгера
logger = Logger.get_instance()