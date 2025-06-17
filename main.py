print('VERY TOP')
import sys
print('AFTER sys')
import os
print('AFTER os')
from PyQt5.QtWidgets import QApplication
print('AFTER QApplication')
from PyQt5.QtCore import QFile, QTextStream
print('AFTER QtCore')
from ui import MainWindow
print('AFTER MainWindow')
from logger import logger
print('AFTER logger')

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

if __name__ == "__main__":
    print("START")
    try:
        print("BEFORE APP")
        app = QApplication(sys.argv)
        print("AFTER APP")
        stylesheet = load_stylesheet("styles.css")
        if stylesheet:
            app.setStyleSheet(stylesheet)
        print("BEFORE WINDOW")
        window = MainWindow()
        print("AFTER WINDOW")
        window.show()
        print("BEFORE EXEC")
        sys.exit(app.exec_())
        print("AFTER EXEC")
    except Exception as e:
        import traceback
        print("[FATAL ERROR]", e)
        print(traceback.format_exc())