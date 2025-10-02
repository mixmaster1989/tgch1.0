#!/usr/bin/env python3
"""
Быстрая проверка ошибок в логах
"""

import os
import re
import glob

def check_errors():
    """Проверка ошибок в логах"""
    print("🔍 ПОИСК ОШИБОК В ЛОГАХ:")
    print("=" * 50)
    
    # Ищем файлы логов
    log_files = []
    
    # PM2 логи
    pm2_logs = glob.glob("/home/user1/.pm2/logs/mex-trading-bot-*.log")
    log_files.extend(pm2_logs)
    
    # Локальные логи
    local_logs = ["bot.log", "pnl_monitor.log"]
    for log_file in local_logs:
        if os.path.exists(log_file):
            log_files.append(log_file)
    
    print(f"Найдено файлов логов: {len(log_files)}")
    
    error_patterns = [
        r'local variable.*referenced before assignment',
        r'UnboundLocalError.*time',
        r'NameError.*time',
        r'Exception.*time',
        r'Traceback.*time',
        r'Error.*time',
        r'❌.*Ошибка.*балансировки.*time',
        r'❌.*Ошибка.*time'
    ]
    
    found_errors = False
    
    for log_file in log_files:
        print(f"\n📁 Проверяем: {log_file}")
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Берем последние 500 строк
            recent_lines = lines[-500:] if len(lines) > 500 else lines
            
            for i, line in enumerate(recent_lines):
                for pattern in error_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        found_errors = True
                        print(f"🚨 НАЙДЕНА ОШИБКА в строке {len(lines) - 500 + i + 1}:")
                        print(f"   {line.strip()}")
                        
                        # Показываем контекст
                        start = max(0, i - 3)
                        end = min(len(recent_lines), i + 4)
                        print("   Контекст:")
                        for j in range(start, end):
                            marker = ">>> " if j == i else "    "
                            print(f"{marker}{recent_lines[j].strip()}")
                        print()
                        
        except Exception as e:
            print(f"❌ Ошибка чтения {log_file}: {e}")
    
    if not found_errors:
        print("✅ Ошибок с переменной 'time' не найдено")
    
    # Дополнительная проверка - ищем все упоминания 'time' в контексте ошибок
    print(f"\n🔍 ДОПОЛНИТЕЛЬНЫЙ ПОИСК 'time' В КОНТЕКСТЕ ОШИБОК:")
    print("=" * 50)
    
    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Ищем строки с 'time' и ошибками
            lines = content.split('\n')
            time_error_lines = []
            
            for i, line in enumerate(lines):
                if ('time' in line.lower() and 
                    ('error' in line.lower() or 'exception' in line.lower() or 'traceback' in line.lower() or '❌' in line)):
                    time_error_lines.append((i + 1, line.strip()))
            
            if time_error_lines:
                print(f"\n📁 В файле {log_file} найдены строки с 'time' и ошибками:")
                for line_num, line in time_error_lines[-10:]:  # Последние 10
                    print(f"   Строка {line_num}: {line}")
                    
        except Exception as e:
            print(f"❌ Ошибка чтения {log_file}: {e}")

if __name__ == "__main__":
    check_errors()
