#!/usr/bin/env python3
"""
Скрипт для создания бэкапа comprehensive_data_manager.py
"""

import os
import shutil
from datetime import datetime

def create_backup():
    """Создать бэкап файла comprehensive_data_manager.py"""
    source_file = "comprehensive_data_manager.py"
    
    if not os.path.exists(source_file):
        print(f"❌ Файл {source_file} не найден!")
        return False
    
    # Создаем имя бэкапа с временной меткой
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"comprehensive_data_manager_backup_{timestamp}.py"
    
    try:
        # Копируем файл
        shutil.copy2(source_file, backup_file)
        print(f"✅ Бэкап создан: {backup_file}")
        
        # Показываем размер файла
        size = os.path.getsize(backup_file)
        print(f"📁 Размер бэкапа: {size:,} байт")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания бэкапа: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Создание бэкапа comprehensive_data_manager.py...")
    create_backup() 