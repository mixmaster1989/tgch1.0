import sys
import traceback
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox

def setup_error_handling():
    """Настраивает обработку ошибок"""
    # Установка глобального обработчика исключений
    sys.excepthook = excepthook

def excepthook(exc_type, exc_value, exc_tb):
    """Глобальный обработчик исключений"""
    tb_str = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    logging.error(tb_str)
    
    app = QApplication.instance()
    if app is not None and app.activeWindow() is not None:
        show_error_dialog(app.activeWindow(), tb_str)
    else:
        print(tb_str)

def show_error_dialog(parent, error):
    """Показывает диалог с ошибкой"""
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowTitle("Ошибка")
    msg.setText("Произошла ошибка!")
    msg.setInformativeText("Подробная информация об ошибке записана в лог-файл.")
    msg.setDetailedText(str(error))
    msg.exec_()

def handle_exception(func):
    """Декоратор для обработки исключений в методах класса"""
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            tb_str = traceback.format_exc()
            logging.error(tb_str)
            show_error_dialog(self, tb_str)
    return wrapper