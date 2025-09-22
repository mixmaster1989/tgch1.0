#!/usr/bin/env python3
"""
Скрипт для исправления ошибки отступов в portfolio_balancer.py
"""

def fix_indentation_error():
    # Читаем файл
    with open('portfolio_balancer.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Исправляем ошибку отступов
    old_except = '''        except Exception as e:

    def get_asset_pnl(self, asset: str, balances: Dict, values: Dict) -> float:'''
    
    new_except = '''        except Exception as e:
            logger.error(f"Ошибка выполнения балансировки: {e}")
            return {'success': False, 'error': str(e)}

    def get_asset_pnl(self, asset: str, balances: Dict, values: Dict) -> float:'''
    
    # Заменяем
    content = content.replace(old_except, new_except)
    
    # Записываем обратно
    with open('portfolio_balancer.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ portfolio_balancer.py исправлен - исправлена ошибка отступов")

if __name__ == "__main__":
    fix_indentation_error()
