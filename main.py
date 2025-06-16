import sys
import os
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile, QTextStream
from ui import MainWindow

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
        print(f"Ошибка при загрузке стилей: {str(e)}")
        return ""

def setup_logging():
    """Настраивает логирование"""
    logging.basicConfig(
        filename='error.log',
        level=logging.ERROR,
        format='%(asctime)s %(levelname)s:%(message)s'
    )

if __name__ == "__main__":
    # Настройка логирования
    setup_logging()
    
    # Создаем приложение
    app = QApplication(sys.argv)
    
    # Загружаем стили
    stylesheet = load_stylesheet("styles.css")
    if stylesheet:
        app.setStyleSheet(stylesheet)
    
    # Создаем и показываем главное окно
    window = MainWindow()
    window.show()
    
    # Запускаем цикл обработки событий
    sys.exit(app.exec_())