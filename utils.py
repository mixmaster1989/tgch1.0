import os
import shutil
import logging
from PyQt5.QtWidgets import QMessageBox

def create_example_images():
    """Создает директорию с примерами изображений, если она не существует"""
    examples_dir = "examples"
    try:
        if not os.path.exists(examples_dir):
            os.makedirs(examples_dir)
        
        # Список изображений примеров
        example_images = [
            "ema14.png", "rsi14.png", "macd.png", "bb20.png", "stoch.png",
            "atr14.png", "cci20.png", "volma20.png", "ma50.png", "level100.png",
            "cross.png", "long.png", "risk2.png", "blue.png"
        ]
        
        # Создаем заглушки для изображений, если они не существуют
        for image in example_images:
            image_path = os.path.join(examples_dir, image)
            if not os.path.exists(image_path):
                # Создаем пустой файл изображения
                with open(image_path, 'w') as f:
                    f.write("# Placeholder for example image")
    except Exception as e:
        logging.error(f"Ошибка при создании примеров изображений: {str(e)}")

def validate_code(code):
    """Проверяет код на наличие ошибок"""
    errors = []
    
    # Проверка на наличие основных компонентов
    if "//@version=5" not in code:
        errors.append("Отсутствует версия Pine Script (//@version=5)")
    
    # Проверка на дублирование объявления индикатора
    indicator_count = code.count("indicator(")
    if indicator_count == 0:
        errors.append("Отсутствует объявление индикатора (indicator)")
    elif indicator_count > 1:
        errors.append("Множественное объявление индикатора. Должно быть только одно.")
    
    # Проверка на наличие ошибок в параметрах
    for line in code.split("\n"):
        if "=" in line and "ta." in line:
            if "(" not in line or ")" not in line:
                errors.append(f"Ошибка в параметрах: {line}")
    
    # Проверка баланса скобок
    stack = []
    for i, c in enumerate(code):
        if c == '(': stack.append(i)
        elif c == ')':
            if not stack:
                errors.append("Лишняя закрывающая скобка")
                break
            stack.pop()
    if stack:
        errors.append("Несоответствие скобок: не все скобки закрыты")
    
    return errors

def show_info_message(parent, title, message):
    """Показывает информационное сообщение"""
    try:
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec_()
    except Exception as e:
        logging.error(f"Ошибка при отображении сообщения: {str(e)}")

def backup_project(backup_dir="backups"):
    """Создает резервную копию проекта"""
    try:
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # Получаем текущую дату и время для имени резервной копии
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{timestamp}"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # Создаем директорию для резервной копии
        os.makedirs(backup_path)
        
        # Копируем все .py файлы
        for file in os.listdir("."):
            if file.endswith(".py"):
                shutil.copy2(file, os.path.join(backup_path, file))
        
        return backup_path
    except Exception as e:
        logging.error(f"Ошибка при создании резервной копии: {str(e)}")
        return None