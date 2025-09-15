#!/usr/bin/env python3
"""
Скрипт для обновления защиты USDC во всех модулях
Увеличивает защиту баланса до $20 USDC для скальперов
"""

import os
import re
from pathlib import Path

def update_file_protection(file_path: str, old_value: str, new_value: str, description: str):
    """Обновить защиту баланса в файле"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if old_value in content:
            new_content = content.replace(old_value, new_value)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ {description}: {file_path}")
            return True
        else:
            print(f"⚠️  {description}: {file_path} - не найдено значение для замены")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка обновления {file_path}: {e}")
        return False

def main():
    """Основная функция обновления"""
    print("🛡️ ОБНОВЛЕНИЕ ЗАЩИТЫ USDC ВО ВСЕХ МОДУЛЯХ")
    print("=" * 60)
    
    # Список файлов для обновления
    files_to_update = [
        {
            'path': 'balance_monitor.py',
            'old': 'self.min_usdc_balance_after_purchase = 10.0  # Минимум $10 USDC должно остаться после покупки',
            'new': 'self.min_usdc_balance_after_purchase = 20.0  # Минимум $20 USDC должно остаться после покупки (зарезервировано для скальперов)',
            'description': 'Монитор баланса - автопокупки BTC/ETH'
        },
        {
            'path': 'active_50_50_balancer.py',
            'old': 'self.min_usdc_balance_after_operation = 10.0  # Минимум $10 USDC должно остаться после операции',
            'new': 'self.min_usdc_balance_after_operation = 20.0  # Минимум $20 USDC должно остаться после операции (зарезервировано для скальперов)',
            'description': 'Активный балансировщик 50/50'
        },
        {
            'path': 'stablecoin_balancer.py',
            'old': 'min_btc_requirement = 12.0  # Минимум для BTC\n        min_eth_requirement = 5.0   # Минимум для ETH',
            'new': 'min_btc_requirement = 12.0  # Минимум для BTC\n        min_eth_requirement = 5.0   # Минимум для ETH\n        min_scalper_protection = 20.0  # Защита $20 USDC для скальперов',
            'description': 'Балансировщик стейблкоинов - добавление защиты скальперов'
        }
    ]
    
    updated_count = 0
    total_count = len(files_to_update)
    
    for file_info in files_to_update:
        if os.path.exists(file_info['path']):
            if update_file_protection(
                file_info['path'], 
                file_info['old'], 
                file_info['new'], 
                file_info['description']
            ):
                updated_count += 1
        else:
            print(f"❌ Файл не найден: {file_info['path']}")
    
    print(f"\n📊 РЕЗУЛЬТАТ ОБНОВЛЕНИЯ:")
    print(f"   Обновлено файлов: {updated_count}/{total_count}")
    
    if updated_count == total_count:
        print("✅ Все файлы успешно обновлены!")
    else:
        print("⚠️  Некоторые файлы не были обновлены")
    
    print(f"\n🛡️ НОВАЯ ЗАЩИТА USDC:")
    print(f"   Минимум $20 USDC зарезервировано для скальперов")
    print(f"   Все балансировщики и закупщики обновлены")
    print(f"   Скальперы защищены от исчерпания баланса")

if __name__ == "__main__":
    main()







