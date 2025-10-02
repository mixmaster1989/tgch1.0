#!/usr/bin/env python3
"""
Скрипт для парсинга логов PM2 и поиска ошибок
"""

import subprocess
import re
import sys

def parse_pm2_logs():
    """Парсинг логов PM2 для поиска ошибок"""
    try:
        # Получаем последние 1000 строк логов
        result = subprocess.run(
            ['pm2', 'logs', 'mex-trading-bot', '--lines', '1000'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            print(f"Ошибка выполнения команды: {result.stderr}")
            return
        
        logs = result.stdout
        
        # Ищем ошибки
        error_patterns = [
            r'local variable.*referenced before assignment',
            r'UnboundLocalError.*time',
            r'NameError.*time',
            r'Exception.*time',
            r'Traceback.*time',
            r'Error.*time',
            r'❌.*Ошибка.*балансировки',
            r'❌.*Ошибка.*time'
        ]
        
        print("🔍 ПОИСК ОШИБОК В ЛОГАХ:")
        print("=" * 50)
        
        found_errors = False
        for pattern in error_patterns:
            matches = re.findall(pattern, logs, re.IGNORECASE)
            if matches:
                found_errors = True
                print(f"\n🚨 НАЙДЕНА ОШИБКА: {pattern}")
                for match in matches:
                    print(f"   {match}")
        
        if not found_errors:
            print("✅ Ошибок с переменной 'time' не найдено")
        
        # Ищем строки с 'time' для анализа
        print(f"\n🔍 АНАЛИЗ ИСПОЛЬЗОВАНИЯ 'time':")
        print("=" * 50)
        
        time_lines = []
        for line in logs.split('\n'):
            if 'time' in line.lower() and ('error' in line.lower() or 'exception' in line.lower() or 'traceback' in line.lower()):
                time_lines.append(line.strip())
        
        if time_lines:
            print("Найдены строки с 'time' и ошибками:")
            for line in time_lines[-10:]:  # Последние 10
                print(f"   {line}")
        else:
            print("Строк с 'time' и ошибками не найдено")
            
    except subprocess.TimeoutExpired:
        print("❌ Таймаут выполнения команды")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    parse_pm2_logs()
