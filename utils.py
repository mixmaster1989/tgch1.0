import os
import json
from tkinter import messagebox

def save_project(blocks, filename):
    """Сохранение проекта в JSON файл"""
    try:
        data = [block.get_data() for block in blocks]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить проект: {str(e)}")
        return False

def load_project(filename):
    """Загрузка проекта из JSON файла"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить проект: {str(e)}")
        return None

def validate_code(code):
    """Проверка кода на ошибки"""
    try:
        # Здесь можно добавить более сложную валидацию
        if not code.strip():
            return False, "Код пустой"
        return True, None
    except Exception as e:
        return False, str(e)

def format_code(code):
    """Форматирование Python кода"""
    try:
        import autopep8
        return autopep8.fix_code(code)
    except:
        return code

def get_project_name(filename):
    """Получение имени проекта из пути к файлу"""
    return os.path.splitext(os.path.basename(filename))[0]

def create_new_project():
    """Создание нового проекта"""
    return []

def export_to_file(code, filename):
    """Экспорт кода в файл"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(code)
        return True
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось экспортировать код: {str(e)}")
        return False 